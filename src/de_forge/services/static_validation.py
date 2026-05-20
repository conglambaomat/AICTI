"""Static validation services for DE-Forge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.services.telemetry_registry import TELEMETRY_REGISTRY


@dataclass(frozen=True)
class ValidationReport:
    """Deterministic static validation report."""

    is_valid: bool
    issues: list[str]


class StaticValidationService:
    """Service for deterministic static validation of generated Sigma rules."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def validate_rule(self, rule_id: str) -> ValidationReport:
        """Validate generated rule deterministically against DetectionSpec constraints."""
        rule = self.db.execute(
            select(GeneratedRuleModel).where(GeneratedRuleModel.id == rule_id)
        ).scalar_one_or_none()
        if rule is None or not rule.rule_content:
            return ValidationReport(is_valid=False, issues=["rule not found or empty content"])

        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == rule.detection_spec_id)
        ).scalar_one_or_none()
        if spec is None or not spec.spec_payload or not spec.is_validated:
            return ValidationReport(is_valid=False, issues=["missing validated DetectionSpec"])

        issues: list[str] = []

        parsed = self._parse_sigma(rule.rule_content, issues)
        if parsed is None:
            return ValidationReport(is_valid=False, issues=sorted(set(issues)))

        self._validate_structure(parsed, issues)
        self._validate_telemetry_and_fields(parsed, issues)
        self._validate_overbroad(rule.rule_content, parsed, issues)

        return ValidationReport(is_valid=len(issues) == 0, issues=sorted(set(issues)))

    def _parse_sigma(self, rule_content: str, issues: list[str]) -> dict[str, Any] | None:
        try:
            parsed = yaml.safe_load(rule_content)
        except yaml.YAMLError:
            issues.append("invalid sigma yaml syntax")
            return None

        if not isinstance(parsed, dict):
            issues.append("invalid sigma structure")
            return None

        return parsed

    def _validate_structure(self, parsed: dict[str, Any], issues: list[str]) -> None:
        if "logsource" not in parsed or not isinstance(parsed.get("logsource"), dict):
            issues.append("missing logsource structure")

        if "detection" not in parsed or not isinstance(parsed.get("detection"), dict):
            issues.append("invalid detection structure")

    def _validate_telemetry_and_fields(self, parsed: dict[str, Any], issues: list[str]) -> None:
        logsource = parsed.get("logsource", {})
        category = logsource.get("category")
        if category != "process_creation":
            issues.append("unknown or unsupported telemetry category")
            return

        allowed_fields = TELEMETRY_REGISTRY["process_creation"].allowed_fields
        detection = parsed.get("detection", {})
        selection = detection.get("selection", {})

        if not isinstance(selection, dict):
            issues.append("invalid detection selection structure")
            return

        for key in selection:
            field_name = key.split("|", 1)[0]
            if field_name not in allowed_fields:
                issues.append(f"unknown telemetry field: {field_name}")

    def _validate_overbroad(self, rule_content: str, parsed: dict[str, Any], issues: list[str]) -> None:
        detection = parsed.get("detection", {})
        if not isinstance(detection, dict):
            return
        selection = detection.get("selection", {})

        if (
            isinstance(selection, dict)
            and set(selection.keys()) == {"EventID"}
            and (str(selection.get("EventID")) == "1" or selection.get("EventID") == 1)
        ):
            issues.append("rule is overbroad: matches all process_creation events")
            return

        if "Image|contains" not in rule_content and "CommandLine|contains" not in rule_content:
            issues.append("rule is too broad: missing behavior-specific selectors")


def validate_retrieval_faithfulness(
    evidence: list[dict[str, Any]],
    chunks: dict[str, dict[str, Any]],
    required_claims: list[str] | None = None,
) -> dict[str, Any]:
    """Validate retrieval faithfulness as a hard gate."""
    errors: list[str] = []

    for item in evidence:
        chunk_id = str(item.get("chunk_id", ""))
        quote = str(item.get("quote", ""))
        char_start = int(item.get("char_start", -1))
        char_end = int(item.get("char_end", -1))

        chunk = chunks.get(chunk_id)
        if chunk is None:
            errors.append(f"Citation mismatch: chunk_id '{chunk_id}' not found")
            continue

        chunk_text = str(chunk.get("text", ""))
        chunk_start = int(chunk.get("start_offset", 0))

        quote_idx = chunk_text.find(quote)
        if quote_idx == -1:
            errors.append(f"Citation mismatch for chunk '{chunk_id}': quote not found in chunk text")
            continue

        expected_start = chunk_start + quote_idx
        expected_end = expected_start + len(quote)

        if char_start != expected_start or char_end != expected_end:
            errors.append(
                f"Offset mismatch for chunk '{chunk_id}': expected ({expected_start}, {expected_end}), got ({char_start}, {char_end})"
            )

    if required_claims is not None:
        supported_claims = {str(item.get("supports", "")) for item in evidence}
        for claim in required_claims:
            if claim not in supported_claims:
                errors.append(f"Unsupported claim: '{claim}' is not backed by evidence")

    return {"valid": len(errors) == 0, "errors": errors}
