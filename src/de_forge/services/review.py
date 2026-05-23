"""Human review gate service with append-only decision semantics."""

from __future__ import annotations

from datetime import UTC, datetime
from time import time_ns
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import ReviewDecision as ReviewDecisionModel
from de_forge.schemas.review import ReviewAction, ReviewDecision, ReviewRequest


class ExportBlockedError(ValueError):
    """Raised when export is attempted without required human approval."""


class ReviewService:
    """Service for recording human review decisions and enforcing export policy."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def decide(self, request: ReviewRequest) -> ReviewDecision:
        export_allowed = request.action == ReviewAction.APPROVE
        return ReviewDecision(
            run_id=request.run_id,
            rule_candidate_id=request.rule_candidate_id,
            action=request.action,
            reviewer_notes=request.reviewer_notes,
            export_allowed=export_allowed,
        )

    def _require_db(self) -> Session:
        if self.db is None:
            raise ValueError("database session is required for persistence operations")
        return self.db

    def record_decision(self, rule_id: str, decision: str, reviewer: str) -> str:
        """Record append-only review decision for a rule."""
        db = self._require_db()
        decision_id = str(uuid4())
        created_at = datetime.fromtimestamp(time_ns() / 1_000_000_000, tz=UTC).isoformat()
        try:
            db.add(
                ReviewDecisionModel(
                    id=decision_id,
                    rule_id=rule_id,
                    decision=decision,
                    reviewer=reviewer,
                    created_at=created_at,
                )
            )
            db.commit()
        except Exception:
            db.rollback()
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
        db = self._require_db()
        return db.execute(
            select(ReviewDecisionModel)
            .where(ReviewDecisionModel.rule_id == rule_id)
            .order_by(ReviewDecisionModel.created_at.desc(), ReviewDecisionModel.id.desc())
            .limit(1)
        ).scalar_one_or_none()
