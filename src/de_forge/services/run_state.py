"""Database-backed runtime state queries."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    ProofObligationRecord,
    ValidationResult,
)


class RunStateService:
    """Read persisted pipeline run state."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_runs(self) -> dict[str, list[dict[str, Any]]]:
        runs = self._db.execute(
            select(PipelineRunRecord).order_by(PipelineRunRecord.created_at)
        ).scalars().all()
        return {"items": [self._run_payload(run) for run in runs]}

    def get_run_detail(self, run_id: str) -> dict[str, Any] | None:
        run = self._get_run(run_id)
        if run is None:
            return None
        return self._run_payload(run)

    def get_run_spec(self, run_id: str) -> dict[str, Any] | None:
        run = self._get_run(run_id)
        if run is None or run.detection_spec_id is None:
            return None

        spec = self._db.get(DetectionSpec, run.detection_spec_id)
        if spec is None:
            return None

        return {
            "run_id": run.run_id,
            "detection_spec_id": spec.id,
            "is_validated": spec.is_validated,
            "abstain_code": spec.abstain_code,
            "spec_payload": self._parse_json(spec.spec_payload),
        }

    def get_run_portfolio(self, run_id: str) -> dict[str, Any] | None:
        run = self._get_run(run_id)
        if run is None:
            return None
        if run.rule_id is None:
            return {"run_id": run.run_id, "items": []}

        rule = self._db.get(GeneratedRule, run.rule_id)
        if rule is None:
            return {"run_id": run.run_id, "items": []}

        return {
            "run_id": run.run_id,
            "items": [
                {
                    "rule_id": rule.id,
                    "detection_spec_id": rule.detection_spec_id,
                    "proof_status": self._proof_status(run.run_id, rule.id),
                }
            ],
        }

    def get_run_validation(self, run_id: str) -> dict[str, Any] | None:
        run = self._get_run(run_id)
        if run is None:
            return None

        results = self._db.execute(
            select(ValidationResult)
            .where(ValidationResult.run_id == run_id)
            .order_by(ValidationResult.created_at, ValidationResult.id)
        ).scalars().all()
        return {
            "run_id": run.run_id,
            "items": [
                {
                    "id": result.id,
                    "rule_id": result.rule_id,
                    "status": result.status,
                    "details": self._parse_json(result.details_json),
                    "created_at": result.created_at,
                }
                for result in results
            ],
        }

    def _get_run(self, run_id: str) -> PipelineRunRecord | None:
        return self._db.execute(
            select(PipelineRunRecord).where(PipelineRunRecord.run_id == run_id)
        ).scalar_one_or_none()

    def _proof_status(self, run_id: str, rule_id: str) -> str:
        obligations = self._db.execute(
            select(ProofObligationRecord).where(
                ProofObligationRecord.run_id == run_id,
                ProofObligationRecord.rule_candidate_id == rule_id,
            )
        ).scalars().all()
        if not obligations:
            return "missing"
        if all(obligation.status == "proven" for obligation in obligations):
            return "proven"
        return "blocked"

    @staticmethod
    def _parse_json(raw: str | None) -> Any:
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    def _run_payload(run: PipelineRunRecord) -> dict[str, Any]:
        return {
            "id": run.id,
            "run_id": run.run_id,
            "report_id": run.report_id,
            "status": run.status,
            "stage": run.stage,
            "detection_spec_id": run.detection_spec_id,
            "rule_id": run.rule_id,
            "created_at": run.created_at,
        }
