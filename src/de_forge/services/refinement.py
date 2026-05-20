"""Bounded refinement controller service with canonical iteration ceilings."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from de_forge.models import RefinementIteration as RefinementIterationModel

MAX_QUERY_REFINEMENT = 3
MAX_RULE_REFINEMENT = 2
MAX_DYNAMIC_REFINEMENT = 2


class RefinementLimitExceededError(ValueError):
    """Raised when refinement iteration exceeds canonical bounded limit."""


class RefinementService:
    """Service to record bounded refinement iterations with lineage."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record_query_refinement(self, detection_spec_id: str) -> str:
        """Record query refinement iteration for a DetectionSpec lineage."""
        count = self._count_for_detection_spec(detection_spec_id)
        if count >= MAX_QUERY_REFINEMENT:
            raise RefinementLimitExceededError("query refinement limit exceeded")

        return self._persist_iteration(detection_spec_id=detection_spec_id, rule_id=None)

    def record_rule_refinement(self, rule_id: str) -> str:
        """Record rule refinement iteration for a rule lineage."""
        count = self._count_for_rule(rule_id)
        if count >= MAX_RULE_REFINEMENT:
            raise RefinementLimitExceededError("rule refinement limit exceeded")

        return self._persist_iteration(detection_spec_id=None, rule_id=rule_id)

    def record_dynamic_refinement(self, rule_id: str) -> str:
        """Record dynamic refinement iteration for a rule lineage."""
        count = self._count_for_rule(rule_id)
        if count >= MAX_DYNAMIC_REFINEMENT:
            raise RefinementLimitExceededError("dynamic refinement limit exceeded")

        return self._persist_iteration(detection_spec_id=None, rule_id=rule_id)

    def _count_for_detection_spec(self, detection_spec_id: str) -> int:
        return int(
            self.db.execute(
                select(func.count())
                .select_from(RefinementIterationModel)
                .where(RefinementIterationModel.detection_spec_id == detection_spec_id)
            ).scalar_one()
        )

    def _count_for_rule(self, rule_id: str) -> int:
        return int(
            self.db.execute(
                select(func.count())
                .select_from(RefinementIterationModel)
                .where(RefinementIterationModel.rule_id == rule_id)
            ).scalar_one()
        )

    def _persist_iteration(self, detection_spec_id: str | None, rule_id: str | None) -> str:
        iteration_id = str(uuid4())
        try:
            self.db.add(
                RefinementIterationModel(
                    id=iteration_id,
                    detection_spec_id=detection_spec_id,
                    rule_id=rule_id,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return iteration_id
