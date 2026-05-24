"""Persistence services for validation and proof artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from de_forge.models import (
    GeneratedRule,
    OracleEvaluationResult,
    PipelineRunRecord,
    RegressionRun,
    TestRun,
    ValidationResult,
)
from de_forge.schemas.oracle import OracleEvaluationResult as OracleEvaluationSchema
from de_forge.services.dynamic_validation import SyntheticValidationResult
from de_forge.services.static_validation import ValidationReport


class ValidationProofPersistenceService:
    """Persist deterministic validation and proof results."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _require_rule(self, rule_id: str) -> None:
        if self.db.get(GeneratedRule, rule_id) is None:
            raise ValueError(f"rule_id {rule_id} not found")

    def _require_pipeline_run(self, run_id: str) -> None:
        if self.db.query(PipelineRunRecord).filter(PipelineRunRecord.run_id == run_id).first() is None:
            raise ValueError(f"run_id {run_id} not found")

    def record_static_validation(
        self, *, run_id: str, rule_id: str, report: ValidationReport
    ) -> str:
        self._require_rule(rule_id)

        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = str(uuid4())
        validation_result = ValidationResult(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status="passed" if report.is_valid else "failed",
            details_json=json.dumps(
                {"validation_type": "static", "issues": report.issues}, sort_keys=True
            ),
            created_at=created_at,
        )
        self.db.add(validation_result)
        self.db.commit()
        return result_id

    def record_dynamic_validation(
        self, *, run_id: str, rule_id: str, result: SyntheticValidationResult
    ) -> str:
        self._require_rule(rule_id)

        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = str(uuid4())
        status = (
            "passed"
            if result.true_positives == result.attack_total and result.false_positives == 0
            else "failed"
        )
        test_run = TestRun(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status=status,
            result_json=json.dumps(
                {
                    "validation_type": "dynamic_synthetic",
                    "attack_total": result.attack_total,
                    "benign_total": result.benign_total,
                    "false_positives": result.false_positives,
                    "true_positives": result.true_positives,
                },
                sort_keys=True,
            ),
            created_at=created_at,
        )
        self.db.add(test_run)
        self.db.commit()
        return result_id

    def record_oracle_evaluation(
        self,
        *,
        run_id: str,
        rule_id: str,
        oracle_case_id: str,
        result: OracleEvaluationSchema,
    ) -> str:
        self._require_rule(rule_id)
        self._require_pipeline_run(run_id)

        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = str(uuid4())
        oracle_result = OracleEvaluationResult(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            oracle_case_id=oracle_case_id,
            score=result.overall_score,
            details_json=result.model_dump_json(),
            created_at=created_at,
        )
        self.db.add(oracle_result)
        self.db.commit()
        return result_id

    def record_regression(
        self, *, run_id: str, rule_id: str, passed: bool, details: dict[str, object]
    ) -> str:
        self._require_rule(rule_id)
        self._require_pipeline_run(run_id)

        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = str(uuid4())
        regression_run = RegressionRun(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status="passed" if passed else "failed",
            result_json=json.dumps(details, sort_keys=True),
            created_at=created_at,
        )
        self.db.add(regression_run)
        self.db.commit()
        return result_id
