"""Hard-gated pipeline orchestrator with canonical state transitions."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.services.static_validation import StaticValidationService


class PipelineState(StrEnum):
    INGESTED = "ingested"
    SPEC_VALIDATED = "spec_validated"
    RULE_GENERATED = "rule_generated"
    STATIC_VALIDATED = "static_validated"
    AWAITING_REVIEW = "awaiting_review"


class PipelineTransitionError(ValueError):
    """Raised when a hard gate blocks pipeline transition."""


class PipelineOrchestrator:
    """Orchestrates deterministic, hard-gated stage transitions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.static_validator = StaticValidationService(db)

    def run_pipeline(self, detection_spec_id: str) -> PipelineState:
        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == detection_spec_id)
        ).scalar_one_or_none()

        if spec is None or not spec.is_validated:
            raise PipelineTransitionError("validated DetectionSpec required")
        if spec.abstain_code is not None:
            raise PipelineTransitionError("abstain DetectionSpec cannot proceed to rule generation")

        rule = self.db.execute(
            select(GeneratedRuleModel).where(
                GeneratedRuleModel.detection_spec_id == detection_spec_id
            )
        ).scalar_one_or_none()
        if rule is None:
            raise PipelineTransitionError("generated rule required before validation")

        validation = self.static_validator.validate_rule(rule.id)
        if not validation.is_valid:
            raise PipelineTransitionError("static validation gate failed")

        return PipelineState.AWAITING_REVIEW
