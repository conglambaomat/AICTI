"""Human review gate service with append-only decision semantics."""

from __future__ import annotations

import json
from time import time_ns
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from de_forge.core.errors import ProofObligationError
from de_forge.schemas.proof_obligation import ProofObligation
from de_forge.schemas.review import ReviewAction, ReviewDecision, ReviewRequest
from de_forge.services.evidence_graph import EvidenceGraphService
from de_forge.services.proof_obligation_service import ProofObligationService


class ExportBlockedError(ValueError):
    """Raised when export is attempted without required human approval."""


ALLOWED_REVIEW_DECISIONS = {"approved", "rejected"}


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
            persisted=False,
            authoritative_for_export=False,
        )

    def _require_db(self) -> Session:
        if self.db is None:
            raise ValueError("database session is required for persistence operations")
        return self.db

    def record_decision(
        self,
        rule_id: str,
        decision: str,
        reviewer: str,
        run_id: str,
        comments: str,
    ) -> str:
        """Record append-only review decision for a rule."""
        if decision not in ALLOWED_REVIEW_DECISIONS:
            raise ValueError(f"invalid review decision: {decision}")

        db = self._require_db()
        decision_id = str(uuid4())
        created_at = f"{time_ns():020d}"
        bind = db.get_bind()
        columns = {column["name"] for column in inspect(bind).get_columns("review_decisions")}
        payload: dict[str, str] = {
            "id": decision_id,
            "rule_id": rule_id,
            "decision": decision,
            "reviewer": reviewer,
            "created_at": created_at,
        }
        if "run_id" in columns:
            payload["run_id"] = run_id
        if "comments" in columns:
            payload["comments"] = comments

        handoff_scope = f"{rule_id}:review.handoff"
        run_handoff_scope = f"{rule_id}:{run_id}:review.handoff"
        try:
            db.execute(text(self._build_review_insert_sql(columns)), payload)
            db.execute(
                text(
                    """
                    DELETE FROM memory_views
                    WHERE scope IN (:rule_scope, :run_scope) AND key = :key
                    """
                ),
                {"rule_scope": handoff_scope, "run_scope": run_handoff_scope, "key": "latest"},
            )
            handoff_value = json.dumps(
                {
                    "approved": decision == "approved",
                    "decision": decision,
                    "reviewer": reviewer,
                    "run_id": run_id,
                    "decision_id": decision_id,
                },
                sort_keys=True,
            )
            for scope in (handoff_scope, run_handoff_scope):
                db.execute(
                    text(
                        """
                        INSERT INTO memory_views (id, scope, key, value, updated_at)
                        VALUES (:id, :scope, :key, :value, :updated_at)
                        """
                    ),
                    {
                        "id": f"mv-{decision_id}-{scope}",
                        "scope": scope,
                        "key": "latest",
                        "value": handoff_value,
                        "updated_at": created_at,
                    },
                )
            graph = EvidenceGraphService(db)
            rule_node = graph.upsert_node(
                run_id=run_id,
                node_type="generated_rule",
                ref_table="generated_rules",
                ref_id=rule_id,
                payload={},
            )
            decision_node = graph.upsert_node(
                run_id=run_id,
                node_type="review_decision",
                ref_table="review_decisions",
                ref_id=decision_id,
                payload={"decision": decision, "reviewer": reviewer},
            )
            graph.add_edge(
                run_id=run_id,
                source_node_id=rule_node,
                target_node_id=decision_node,
                edge_type="validated_by",
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        return decision_id

    def _build_review_insert_sql(self, columns: set[str]) -> str:
        ordered = ["id", "rule_id"]
        if "run_id" in columns:
            ordered.append("run_id")
        ordered.extend(["decision", "reviewer"])
        if "comments" in columns:
            ordered.append("comments")
        ordered.append("created_at")
        column_sql = ", ".join(ordered)
        value_sql = ", ".join(f":{name}" for name in ordered)
        return f"INSERT INTO review_decisions ({column_sql}) VALUES ({value_sql})"

    def can_export(self, rule_status: str, review_decision: str | None) -> bool:
        """Check if rule can be exported based on status and review decision."""
        if rule_status != "awaiting_review":
            return False
        return review_decision == "approved"

    def assert_can_export(
        self,
        rule_id: str,
        rule_status: str,
        proof_obligations: list[ProofObligation] | None = None,
        run_id: str | None = None,
    ) -> None:
        """Assert that rule can be exported, raising ExportBlockedError if not."""
        if not self._has_review_handoff_memory(rule_id, run_id=run_id):
            raise ExportBlockedError("review handoff memory required before export")

        latest_decision = self._get_latest_decision(rule_id, run_id=run_id)
        if latest_decision is None:
            raise ExportBlockedError("human approval required before export")

        if not self.can_export(rule_status, latest_decision.decision):
            raise ExportBlockedError("human approval required before export")

        if proof_obligations is not None:
            try:
                ProofObligationService().verify_selectable(proof_obligations)
            except ProofObligationError as exc:
                raise ExportBlockedError(str(exc)) from exc

            return

        if self._has_failed_or_unknown_proof_obligations(rule_id, run_id=run_id):
            raise ExportBlockedError("proof obligation gate failed before export")

    def _has_failed_or_unknown_proof_obligations(
        self, rule_id: str, *, run_id: str | None = None
    ) -> bool:
        db = self._require_db()
        try:
            rows = db.execute(
                text(
                    """
                    SELECT status, justification
                    FROM proof_obligations
                    WHERE rule_candidate_id = :rule_candidate_id
                      AND (:run_id IS NULL OR run_id = :run_id)
                    """
                ),
                {"rule_candidate_id": rule_id, "run_id": run_id},
            ).fetchall()
        except SQLAlchemyError:
            return True

        if not rows:
            return run_id is not None

        return any(status != "proven" for status, _justification in rows)

    def _has_review_handoff_memory(self, rule_id: str, *, run_id: str | None = None) -> bool:
        db = self._require_db()
        scope = (
            f"{rule_id}:{run_id}:review.handoff"
            if run_id is not None
            else f"{rule_id}:review.handoff"
        )
        row = (
            db.execute(
                text(
                    """
                    SELECT value
                    FROM memory_views
                    WHERE scope = :scope AND key = 'latest'
                    LIMIT 1
                    """
                ),
                {"scope": scope},
            )
            .mappings()
            .first()
        )
        if row is None:
            return False
        try:
            payload = json.loads(str(row["value"]))
        except (TypeError, json.JSONDecodeError):
            return False
        decision = payload.get("decision")
        payload_run_id = payload.get("run_id")
        return (
            decision in ALLOWED_REVIEW_DECISIONS
            and payload.get("approved") == (decision == "approved")
            and bool(payload.get("decision_id"))
            and bool(payload.get("reviewer"))
            and bool(payload_run_id)
            and (run_id is None or payload_run_id == run_id)
        )

    def _get_latest_decision(
        self, rule_id: str, *, run_id: str | None = None
    ) -> SimpleNamespace | None:
        db = self._require_db()
        bind = db.get_bind()
        columns = {column["name"] for column in inspect(bind).get_columns("review_decisions")}
        selected = ["id", "rule_id", "decision", "reviewer", "created_at"]
        if "run_id" in columns:
            selected.insert(2, "run_id")
        if "comments" in columns:
            selected.insert(-1, "comments")

        select_sql = ", ".join(selected)
        row = (
            db.execute(
                text(
                    f"""
                SELECT {select_sql}
                FROM review_decisions
                WHERE rule_id = :rule_id
                  AND (:run_id IS NULL OR run_id = :run_id)
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
                ),
                {"rule_id": rule_id, "run_id": run_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return SimpleNamespace(**dict(row))
