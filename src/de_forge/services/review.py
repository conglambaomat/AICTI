"""Human review gate service with append-only decision semantics."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import ReviewDecision as ReviewDecisionModel


class ExportBlockedError(ValueError):
    """Raised when export is attempted without required human approval."""


class ReviewService:
    """Service for recording human review decisions and enforcing export policy."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record_decision(self, rule_id: str, decision: str, reviewer: str) -> str:
        """Record append-only review decision for a rule."""
        decision_id = str(uuid4())
        created_at = datetime.utcnow().isoformat()
        try:
            self.db.add(
                ReviewDecisionModel(
                    id=decision_id,
                    rule_id=rule_id,
                    decision=decision,
                    reviewer=reviewer,
                    created_at=created_at,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return decision_id

    def can_export(self, rule_status: str, review_decision: str | None) -> bool:
        """Check if rule can be exported based on status and review decision."""
        if rule_status != "awaiting_review":
            return False
        return review_decision == "approved"

    def assert_can_export(self, rule_id: str, rule_status: str) -> None:
        """Assert that rule can be exported, raising ExportBlockedError if not."""
        latest_decision = self._get_latest_decision(rule_id)
        if latest_decision is None:
            raise ExportBlockedError("human approval required before export")

        if not self.can_export(rule_status, latest_decision.decision):
            raise ExportBlockedError("human approval required before export")

    def _get_latest_decision(self, rule_id: str) -> ReviewDecisionModel | None:
        return self.db.execute(
            select(ReviewDecisionModel)
            .where(ReviewDecisionModel.rule_id == rule_id)
            .order_by(ReviewDecisionModel.created_at.desc(), ReviewDecisionModel.id.desc())
            .limit(1)
        ).scalar_one_or_none()
