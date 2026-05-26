"""Persistence services for validation and proof artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.core.errors import ProofObligationError
from de_forge.models import (
    GeneratedRule,
    OracleEvaluationResult,
    PipelineRunRecord,
    ProofObligationRecord,
    RegressionRun,
    TestRun,
    ValidationResult,
)
from de_forge.schemas.oracle import OracleEvaluationResult as OracleEvaluationSchema
from de_forge.services.dynamic_validation import SyntheticValidationResult
from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService
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

    def generate_proof_obligations_from_artifacts(
        self, *, run_id: str, rule_id: str
    ) -> list[str]:
        self._require_rule(rule_id)

        static_passed = self._has_passed_static_validation(run_id, rule_id)
        dynamic_passed = self._has_passed_dynamic_validation(run_id, rule_id)
        regression_passed = self._has_passed_regression(run_id, rule_id)
        all_required_artifacts_passed = static_passed and dynamic_passed and regression_passed
        obligation_definitions = [
            (
                "detects_report_behavior",
                "Rule detects the behavior described by the report.",
                ["static_validation", "dynamic_validation"],
                all_required_artifacts_passed,
            ),
            (
                "not_overbroad",
                "Rule is not overbroad against regression coverage.",
                ["static_validation", "regression"],
                all_required_artifacts_passed,
            ),
            (
                "telemetry_fields_exist",
                "Rule telemetry fields exist in validated schema.",
                ["static_validation"],
                all_required_artifacts_passed,
            ),
            (
                "citation_faithful",
                "Rule citations are faithful to validated evidence.",
                ["static_validation"],
                all_required_artifacts_passed,
            ),
        ]

        obligation_ids: list[str] = []
        for claim_type, claim_text, required_artifacts, is_proven in obligation_definitions:
            obligation_id = str(uuid4())
            obligation_ids.append(obligation_id)
            self.db.add(
                ProofObligationRecord(
                    id=obligation_id,
                    run_id=run_id,
                    rule_candidate_id=rule_id,
                    claim_type=claim_type,
                    claim_text=claim_text,
                    required_artifact_types=json.dumps(required_artifacts, sort_keys=True),
                    status="proven" if is_proven else "unknown",
                    justification=(
                        "derived from persisted validation artifacts" if is_proven else None
                    ),
                )
            )
        self.db.commit()
        return obligation_ids

    def verify_persisted_proofs_selectable(self, *, run_id: str, rule_id: str) -> bool:
        obligations = (
            self.db.execute(
                select(ProofObligationRecord).where(
                    ProofObligationRecord.run_id == run_id,
                    ProofObligationRecord.rule_candidate_id == rule_id,
                )
            )
            .scalars()
            .all()
        )
        if not obligations:
            raise ProofObligationError("proof obligations missing")
        proof_rows = [
            {
                "run_id": obligation.run_id,
                "rule_candidate_id": obligation.rule_candidate_id,
                "claim_type": obligation.claim_type,
                "status": obligation.status,
                "justification": obligation.justification,
            }
            for obligation in obligations
        ]
        try:
            ProofCoverageService().assert_coverage_satisfied(
                run_id=run_id, rule_id=rule_id, proof_rows=proof_rows
            )
        except ProofCoverageError as exc:
            raise ProofObligationError(str(exc)) from exc
        return True

    def _has_passed_static_validation(self, run_id: str, rule_id: str) -> bool:
        return (
            self.db.execute(
                select(ValidationResult.id).where(
                    ValidationResult.run_id == run_id,
                    ValidationResult.rule_id == rule_id,
                    ValidationResult.status == "passed",
                )
            ).first()
            is not None
        )

    def _has_passed_dynamic_validation(self, run_id: str, rule_id: str) -> bool:
        return (
            self.db.execute(
                select(TestRun.id).where(
                    TestRun.run_id == run_id,
                    TestRun.rule_id == rule_id,
                    TestRun.status == "passed",
                )
            ).first()
            is not None
        )

    def _has_passed_regression(self, run_id: str, rule_id: str) -> bool:
        return (
            self.db.execute(
                select(RegressionRun.id).where(
                    RegressionRun.run_id == run_id,
                    RegressionRun.rule_id == rule_id,
                    RegressionRun.status == "passed",
                )
            ).first()
            is not None
        )
