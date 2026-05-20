"""Sigma rule generation service with DetectionSpec hard gate and immutable versioning."""

from __future__ import annotations

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

        try:
            self.db.add(
                GeneratedRuleModel(
                    id=rule_id,
                    detection_spec_id=spec.id,
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

        return spec
