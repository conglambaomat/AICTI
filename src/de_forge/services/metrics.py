from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from de_forge.models import (
    PipelineRunRecord,
    ProofObligationRecord,
    RegressionRun,
    ValidationResult,
)

TERMINAL_RUN_STATUSES = {"ok", "failed", "abstain"}


class MetricsService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def quality_snapshot(
        self,
        citation_faithfulness: float,
        proof_pass_rate: float,
        static_validity_rate: float,
        regression_pass_rate: float,
    ) -> dict[str, float]:
        values = [
            citation_faithfulness,
            proof_pass_rate,
            static_validity_rate,
            regression_pass_rate,
        ]
        return {
            "citation_faithfulness": citation_faithfulness,
            "proof_pass_rate": proof_pass_rate,
            "static_validity_rate": static_validity_rate,
            "regression_pass_rate": regression_pass_rate,
            "overall_quality": round(sum(values) / len(values), 4),
        }

    def quality_summary(self) -> dict[str, Any]:
        proof_counts = self._status_counts(ProofObligationRecord)
        citation_counts = self._status_counts(
            ProofObligationRecord,
            ProofObligationRecord.claim_type == "citation_faithful",
        )
        validation_counts = self._status_counts(ValidationResult)
        regression_counts = self._status_counts(RegressionRun)

        citation_faithfulness = self._rate_from_counts(citation_counts, "proven")
        proof_pass_rate = self._rate_from_counts(proof_counts, "proven")
        static_validity_rate = self._rate_from_counts(validation_counts, "passed")
        regression_pass_rate = self._rate_from_counts(regression_counts, "passed")
        available_rates = [
            rate
            for rate in (
                citation_faithfulness,
                proof_pass_rate,
                static_validity_rate,
                regression_pass_rate,
            )
            if rate is not None
        ]

        return {
            "citation_faithfulness": citation_faithfulness,
            "proof_pass_rate": proof_pass_rate,
            "static_validity_rate": static_validity_rate,
            "regression_pass_rate": regression_pass_rate,
            "overall_quality": round(sum(available_rates) / len(available_rates), 4)
            if available_rates
            else None,
            "sample_counts": {
                "proof_obligations": sum(proof_counts.values()),
                "static_validations": sum(validation_counts.values()),
                "regression_runs": sum(regression_counts.values()),
            },
        }

    def ops_summary(self) -> dict[str, Any]:
        self._require_db()
        run_counts = dict(sorted(self._status_counts(PipelineRunRecord).items()))
        terminal_count = sum(
            count for status, count in run_counts.items() if status in TERMINAL_RUN_STATUSES
        )
        ok_count = run_counts.get("ok", 0)
        total_runs = sum(run_counts.values())

        return {
            "queue_depth": sum(
                count for status, count in run_counts.items() if status not in TERMINAL_RUN_STATUSES
            ),
            "run_success_rate": round(ok_count / terminal_count, 4) if terminal_count else None,
            "run_counts": run_counts,
            "total_runs": total_runs,
        }

    def dashboard_summary(self) -> dict[str, Any]:
        return {"queue": self.ops_summary(), "quality": self.quality_summary()}

    def _require_db(self) -> Session:
        if self.db is None:
            raise ValueError("database session required")
        return self.db

    def _status_counts(self, model: Any, *where_clauses: Any) -> dict[str, int]:
        db = self._require_db()
        statement = select(model.status, func.count()).select_from(model)
        for clause in where_clauses:
            statement = statement.where(clause)
        statement = statement.group_by(model.status)
        return {str(status): int(count) for status, count in db.execute(statement).all()}

    @staticmethod
    def _rate_from_counts(counts: dict[str, int], passing_status: str) -> float | None:
        total = sum(counts.values())
        if total == 0:
            return None
        return round(counts.get(passing_status, 0) / total, 4)
