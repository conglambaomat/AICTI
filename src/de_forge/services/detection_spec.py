"""DetectionSpec builder service with strict runtime gating."""

from __future__ import annotations

from dataclasses import dataclass

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
    """Service for validating and persisting DetectionSpec contracts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_detection_spec(
        self,
        spec: DetectionSpec,
        available_telemetry: list[str] | None = None,
    ) -> DetectionSpecBuildResult:
        """Persist behavior DetectionSpec after strict telemetry runtime gate."""
        self._enforce_behavior_telemetry_gate(spec, available_telemetry)

        detection_spec_id = make_idempotency_key(
            "detection_spec",
            {
                "report_id": spec.report_id,
                "behavior_rules": [rule.model_dump() for rule in spec.behavior_rules],
                "false_positive_hypotheses": spec.false_positive_hypotheses,
                "test_plan": spec.test_plan,
            },
        )

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

    def build_abstain_spec(
        self,
        report_id: str,
        abstain_decision: AbstainDecision,
    ) -> DetectionSpecBuildResult:
        """Persist abstain DetectionSpec with structured reason and lineage."""
        detection_spec_id = make_idempotency_key(
            "detection_spec_abstain",
            {
                "report_id": report_id,
                "abstain_decision": abstain_decision.model_dump(),
            },
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

    def _enforce_behavior_telemetry_gate(
        self,
        spec: DetectionSpec,
        available_telemetry: list[str] | None,
    ) -> None:
        """Fail fast when required behavior telemetry is missing from hard gate."""
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
