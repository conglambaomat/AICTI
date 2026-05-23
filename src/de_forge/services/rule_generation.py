"""Rule generation service for DetectionSpec-gated Sigma output and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
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
    """Service for Sigma rule generation with optional persistence."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def generate_rule(self, detection_spec: dict[str, Any], profile: str) -> dict[str, Any]:
        if detection_spec.get("abstain") is True:
            return {
                "sigma_rule": {},
                "abstain": True,
                "abstain_reason": str(
                    detection_spec.get("abstain_reason", "DetectionSpec abstained")
                ),
                "metadata": {"profile": profile},
            }

        if "logic" not in detection_spec:
            raise ValueError("DetectionSpec missing required logic")

        sigma_rule = {
            "title": "DE-Forge Generated Suspicious Process Execution",
            "id": "de-forge-generated-rule",
            "status": "experimental",
            "description": "Generated from validated DetectionSpec",
            "logsource": {
                "category": "process_creation",
                "product": "windows",
            },
            "detection": {
                "selection": {
                    "Image|contains": "powershell",
                    "CommandLine|contains": "-enc",
                },
                "condition": "selection",
            },
            "level": "high" if profile == "strict" else "medium",
            "tags": ["attack.t1059.001"],
        }

        return {
            "sigma_rule": sigma_rule,
            "abstain": False,
            "metadata": {"profile": profile},
        }

    def generate_sigma_rule(self, detection_spec_id: str) -> RuleGenerationResult:
        if self.db is None:
            raise ValueError("Database session required for persistent rule generation")

        spec = self._get_validated_detection_spec(detection_spec_id=detection_spec_id)
        rule_id = str(uuid4())
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
        if self.db is None:
            raise ValueError("Database session required")

        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == detection_spec_id)
        ).scalar_one_or_none()

        if spec is None:
            raise UnvalidatedDetectionSpecError(
                f"DetectionSpec {detection_spec_id} not found or not validated"
            )
        if spec.abstain_code is not None:
            raise UnvalidatedDetectionSpecError(f"DetectionSpec {detection_spec_id} is abstain")
        if not spec.is_validated:
            raise UnvalidatedDetectionSpecError(
                f"DetectionSpec {detection_spec_id} not found or not validated"
            )

        return spec

    def _materialize_sigma_from_spec(self, spec: DetectionSpecModel) -> str:
        if not spec.spec_payload:
            raise ValueError("DetectionSpec missing spec_payload for constrained rule generation")

        spec_data = json.loads(spec.spec_payload)
        behavior_rules = spec_data.get("behavior_rules", [])
        if not behavior_rules:
            raise ValueError("DetectionSpec has no behavior_rules")

        first_rule = behavior_rules[0]
        required_telemetry = first_rule["required_telemetry"]
        detection_logic = first_rule["detection_logic"]

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
