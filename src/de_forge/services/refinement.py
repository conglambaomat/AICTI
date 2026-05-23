"""Bounded refinement services and controller logic."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import func, inspect, text, select
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
        count = self._count_for_detection_spec(detection_spec_id)
        if count >= MAX_QUERY_REFINEMENT:
            raise RefinementLimitExceededError("query refinement limit exceeded")
        return self._persist_iteration(detection_spec_id=detection_spec_id, rule_id=None)

    def record_rule_refinement(self, rule_id: str) -> str:
        count = self._count_for_rule(rule_id)
        if count >= MAX_RULE_REFINEMENT:
            raise RefinementLimitExceededError("rule refinement limit exceeded")
        return self._persist_iteration(detection_spec_id=None, rule_id=rule_id)

    def record_dynamic_refinement(self, rule_id: str) -> str:
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
        bind = self.db.get_bind()
        columns = {column["name"] for column in inspect(bind).get_columns("refinement_iterations")}
        payload: dict[str, str | None] = {
            "id": iteration_id,
            "detection_spec_id": detection_spec_id,
            "rule_id": rule_id,
        }
        if "run_id" in columns:
            payload["run_id"] = "run_unknown"
        if "feedback_ref" in columns:
            payload["feedback_ref"] = ""
        if "regression_ref" in columns:
            payload["regression_ref"] = ""
        if "created_at" in columns:
            payload["created_at"] = "1970-01-01T00:00:00+00:00"

        try:
            self.db.execute(text(self._build_refinement_insert_sql(columns)), payload)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return iteration_id

    def _build_refinement_insert_sql(self, columns: set[str]) -> str:
        ordered = ["id", "detection_spec_id", "rule_id"]
        for optional in ("run_id", "feedback_ref", "regression_ref", "created_at"):
            if optional in columns:
                ordered.append(optional)
        column_sql = ", ".join(ordered)
        value_sql = ", ".join(f":{name}" for name in ordered)
        return f"INSERT INTO refinement_iterations ({column_sql}) VALUES ({value_sql})"


class RefinementController:
    def __init__(self, max_iterations: int = 3) -> None:
        self.max_iterations = max_iterations
        self._history: dict[int, int] = {}

    def record_iteration_result(self, iteration: int, issues_count: int) -> None:
        self._history[iteration] = issues_count

    def _is_plateau(self, iteration: int) -> bool:
        prev_count = self._history.get(iteration - 1)
        current_count = self._history.get(iteration)
        if prev_count is None or current_count is None:
            return False
        return current_count >= prev_count

    def refine(
        self,
        current_rule: dict[str, Any],
        validation_issues: list[dict[str, Any]],
        detection_spec: dict[str, Any],
        iteration: int,
    ) -> dict[str, Any]:
        if iteration >= self.max_iterations:
            return {
                "revised_sigma_rule": current_rule,
                "applied_fixes": [],
                "should_abort": True,
                "abort_reason": f"Reached max iterations ({self.max_iterations})",
            }

        if self._is_plateau(iteration):
            return {
                "revised_sigma_rule": current_rule,
                "applied_fixes": [],
                "should_abort": True,
                "abort_reason": "Refinement plateau detected",
            }

        revised = dict(current_rule)
        detection = dict(revised.get("detection", {}))
        selection = dict(detection.get("selection", {}))

        required_fields = detection_spec.get("logic", {}).get("required_fields", [])
        applied_fixes: list[str] = []
        for field in required_fields:
            if field not in selection:
                selection[field] = "*"
                applied_fixes.append(f"Added missing field {field}")

        if validation_issues and not applied_fixes:
            applied_fixes.append("Reviewed validation issues")

        detection["selection"] = selection
        revised["detection"] = detection

        return {
            "revised_sigma_rule": revised,
            "applied_fixes": applied_fixes,
            "should_abort": False,
            "abort_reason": "",
        }
