"""DetectionSpec services for persistence and synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from de_forge.core.idempotency import make_idempotency_key
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.schemas.abstain import AbstainDecision
from de_forge.schemas.detection_spec import DetectionSpec


@dataclass(frozen=True)
class DetectionSpecBuildResult:
    """Result payload for persisted detection spec build."""

    detection_spec_id: str
    report_id: str
    abstain_code: str | None = None


class DetectionSpecService:
    """Service for DetectionSpec validation, persistence, and synthesis."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def build_detection_spec(
        self,
        evidence_spans: list[dict[str, Any]] | None = None,
        attack_mappings: list[dict[str, Any]] | None = None,
        telemetry_registry: dict[str, list[str]] | None = None,
        profile: str | None = None,
        spec: DetectionSpec | None = None,
        available_telemetry: list[str] | None = None,
    ) -> dict[str, Any] | DetectionSpecBuildResult:
        # Synthesis mode (no spec provided)
        if spec is None:
            if not evidence_spans or not attack_mappings:
                return {
                    "abstain": True,
                    "abstain_reason": "Insufficient evidence or ATT&CK mappings to build DetectionSpec",
                    "behavior": [],
                    "attack_mappings": [],
                    "telemetry_requirements": [],
                    "logic": {},
                    "false_positive_hypotheses": [],
                    "test_plan": [],
                    "metadata": {"profile": profile or "balanced"},
                }

            behavior = [
                {
                    "behavior_label": span.get("behavior_label", "unknown_behavior"),
                    "evidence_ids": [span.get("evidence_id", "e1")],
                }
                for span in evidence_spans
            ]

            telemetry_requirements = [
                {"source": source, "allowed_fields": fields}
                for source, fields in (telemetry_registry or {}).items()
            ]

            return {
                "abstain": False,
                "behavior": behavior,
                "attack_mappings": attack_mappings,
                "telemetry_requirements": telemetry_requirements,
                "logic": {
                    "selection": "process_creation with suspicious commandline",
                    "condition": "selection",
                },
                "false_positive_hypotheses": ["Legitimate administrative scripting activity"],
                "test_plan": [
                    "Test against known malicious PowerShell execution logs",
                    "Test against benign admin PowerShell activity",
                ],
                "metadata": {"profile": profile or "balanced"},
            }

        # Persistence mode (spec provided)
        if self.db is None:
            raise ValueError("Database session required for persistence")

        self._enforce_behavior_telemetry_gate(spec, available_telemetry)

        idempotency_payload: dict[str, Any] = {
            "report_id": spec.report_id,
            "behavior_rules": [rule.model_dump(mode="json") for rule in spec.behavior_rules],
            "false_positive_hypotheses": spec.false_positive_hypotheses,
            "test_plan": spec.test_plan,
        }
        detection_spec_id = make_idempotency_key("detection_spec", idempotency_payload)

        try:
            self.db.add(
                DetectionSpecModel(
                    id=detection_spec_id,
                    report_id=spec.report_id,
                    spec_payload=spec.model_dump_json(),
                    is_validated=True,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return DetectionSpecBuildResult(
            detection_spec_id=detection_spec_id,
            report_id=spec.report_id,
        )

    def build_abstain_spec(self, report_id: str, abstain_decision: AbstainDecision) -> DetectionSpecBuildResult:
        if self.db is None:
            raise ValueError("Database session required for persistence")

        detection_spec_id = make_idempotency_key(
            "detection_spec_abstain",
            {"report_id": report_id, "abstain_decision": abstain_decision.model_dump()},
        )

        try:
            self.db.add(
                DetectionSpecModel(
                    id=detection_spec_id,
                    report_id=report_id,
                    abstain_code=abstain_decision.abstain_code,
                    abstain_context=abstain_decision.abstain_context,
                    abstain_human_message=abstain_decision.human_message,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return DetectionSpecBuildResult(
            detection_spec_id=detection_spec_id,
            report_id=report_id,
            abstain_code=abstain_decision.abstain_code,
        )

    def _enforce_behavior_telemetry_gate(self, spec: DetectionSpec, available_telemetry: list[str] | None) -> None:
        if available_telemetry is None:
            return

        available_set = set(available_telemetry)
        for rule in spec.behavior_rules:
            if not rule.required_telemetry:
                raise ValueError("behavior-rule branch requires telemetry but none provided")
            missing = set(rule.required_telemetry) - available_set
            if missing:
                raise ValueError(
                    f"missing required telemetry: {sorted(missing)} not in available telemetry {sorted(available_telemetry)}"
                )
