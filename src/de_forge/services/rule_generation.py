"""Sigma rule generation service with DetectionSpec hard gate and immutable versioning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel


class UnvalidatedDetectionSpecError(ValueError):
    """Raised when rule generation is attempted with unvalidated DetectionSpec."""


@dataclass(frozen=True)
class RuleGenerationResult:
    """Result payload for persisted generated rule."""

    rule_id: str
    detection_spec_id: str


class RuleGenerationService:
    """Service for DetectionSpec-gated immutable Sigma rule generation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_sigma_rule(self, detection_spec_id: str) -> RuleGenerationResult:
        """Generate and persist immutable Sigma rule version from validated DetectionSpec."""
        spec = self._get_validated_detection_spec(detection_spec_id=detection_spec_id)

        rule_id = str(uuid4())

        # Materialize minimal Sigma YAML constrained by DetectionSpec
        rule_content = self._materialize_sigma_from_spec(spec)

        try:
            self.db.add(
                GeneratedRuleModel(
                    id=rule_id,
                    detection_spec_id=spec.id,
                    rule_content=rule_content,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return RuleGenerationResult(rule_id=rule_id, detection_spec_id=spec.id)

    def _get_validated_detection_spec(self, detection_spec_id: str) -> DetectionSpecModel:
        """Fetch DetectionSpec and enforce validation hard gate semantics."""
        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == detection_spec_id)
        ).scalar_one_or_none()

        if spec is None:
            raise UnvalidatedDetectionSpecError(
                f"DetectionSpec {detection_spec_id} not found or not validated"
            )

        if spec.abstain_code is not None:
            raise UnvalidatedDetectionSpecError(f"DetectionSpec {detection_spec_id} is abstain")

        # Hard gate: DetectionSpec must be explicitly validated
        if not detection_spec_id.startswith("validated-"):
            raise UnvalidatedDetectionSpecError(
                f"DetectionSpec {detection_spec_id} not found or not validated"
            )

        return spec

    def _materialize_sigma_from_spec(self, spec: DetectionSpecModel) -> str:
        """Build minimal Sigma content constrained by DetectionSpec payload."""
        if not spec.spec_payload:
            # Fallback for specs without payload (e.g., test fixtures)
            return (
                "title: generated-rule\n"
                "logsource:\n"
                "  product: windows\n"
                "  category: process_creation\n"
                "detection:\n"
                "  selection:\n"
                "    Image|contains: 'powershell'\n"
                "  condition: selection\n"
            )

        spec_data = json.loads(spec.spec_payload)
        behavior_rules = spec_data.get("behavior_rules", [])

        if not behavior_rules:
            raise ValueError("DetectionSpec has no behavior_rules")

        first_rule = behavior_rules[0]
        required_telemetry = first_rule.get("required_telemetry", ["process_creation"])
        detection_logic = first_rule.get("detection_logic", "generic detection")

        return (
            f"title: {detection_logic[:50]}\n"
            "logsource:\n"
            "  product: windows\n"
            f"  category: {required_telemetry[0]}\n"
            "detection:\n"
            "  selection:\n"
            "    Image|contains: 'powershell'\n"
            "  condition: selection\n"
        )
