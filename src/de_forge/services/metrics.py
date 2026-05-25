from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from de_forge.models import PipelineRunRecord, ProofObligationRecord, RegressionRun, ValidationResult

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
        db = self._require_db()
        proof_rows = db.query(ProofObligationRecord).all()
        citation_rows = [row for row in proof_rows if row.claim_type == "citation_faithful"]
        validation_rows = db.query(ValidationResult).all()
        regression_rows = db.query(RegressionRun).all()

        citation_faithfulness = self._rate(citation_rows, "proven")
        proof_pass_rate = self._rate(proof_rows, "proven")
        static_validity_rate = self._rate(validation_rows, "passed")
        regression_pass_rate = self._rate(regression_rows, "passed")
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
                "proof_obligations": len(proof_rows),
                "static_validations": len(validation_rows),
                "regression_runs": len(regression_rows),
            },
        }

    def ops_summary(self) -> dict[str, Any]:
        db = self._require_db()
        rows = db.query(PipelineRunRecord).all()
        terminal_rows = [row for row in rows if row.status in TERMINAL_RUN_STATUSES]
        run_counts = dict(sorted(Counter(row.status for row in rows).items()))

        return {
            "queue_depth": sum(1 for row in rows if row.status not in TERMINAL_RUN_STATUSES),
            "run_success_rate": self._rate(terminal_rows, "ok"),
            "run_counts": run_counts,
            "total_runs": len(rows),
        }

    def dashboard_summary(self) -> dict[str, Any]:
        return {"queue": self.ops_summary(), "quality": self.quality_summary()}

    def _require_db(self) -> Session:
        if self.db is None:
            raise ValueError("database session required")
        return self.db

    @staticmethod
    def _rate(rows: list[Any], passing_status: str) -> float | None:
        if not rows:
            return None
        return round(sum(1 for row in rows if row.status == passing_status) / len(rows), 4)
