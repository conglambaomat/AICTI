"""Integration tests for validation and proof persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.core.errors import ProofObligationError
from de_forge.db.base import Base
from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    OracleEvaluationResult,
    PipelineRunRecord,
    ProofObligationRecord,
    RegressionRun,
    Report,
    TestRun,
    ValidationResult,
)
from de_forge.schemas.oracle import OracleEvaluationResult as OracleEvaluationSchema
from de_forge.services.dynamic_validation import SyntheticValidationResult
from de_forge.services.static_validation import ValidationReport
from de_forge.services.validation_proof_persistence import ValidationProofPersistenceService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, class_=Session)
    return session_factory()


def _seed_rule(db: Session, rule_id: str = "rule-1") -> str:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri=None,
        title="Test report",
        raw_text="Threat activity",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    detection_spec = DetectionSpec(
        id="spec-1",
        report_id=report.id,
        spec_payload=json.dumps({"title": "test spec"}),
        is_validated=True,
    )
    rule = GeneratedRule(
        id=rule_id,
        detection_spec_id=detection_spec.id,
        rule_content="title: test rule",
    )
    db.add_all([report, detection_spec, rule])
    db.commit()
    return rule.id


def _seed_pipeline_run(db: Session, *, run_id: str, rule_id: str) -> None:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    db.add(
        PipelineRunRecord(
            id=f"pipeline-{run_id}",
            run_id=run_id,
            report_id="report-1",
            status="ok",
            stage="validation",
            detection_spec_id="spec-1",
            rule_id=rule_id,
            created_at=now,
        )
    )
    db.commit()


def test_record_static_validation_persists_validation_result() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_static_validation(
        run_id="run-static",
        rule_id=rule_id,
        report=ValidationReport(is_valid=False, issues=["missing logsource structure"]),
    )

    assert len(result_id) == 36
    validation_result = db.execute(select(ValidationResult)).scalar_one()
    assert validation_result.id == result_id
    assert validation_result.rule_id == rule_id
    assert validation_result.run_id == "run-static"
    assert validation_result.status == "failed"
    assert json.loads(validation_result.details_json) == {
        "validation_type": "static",
        "issues": ["missing logsource structure"],
    }


def test_record_dynamic_validation_persists_test_run() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_dynamic_validation(
        run_id="run-dynamic",
        rule_id=rule_id,
        result=SyntheticValidationResult(
            true_positives=2,
            false_positives=0,
            attack_total=2,
            benign_total=3,
        ),
    )

    assert len(result_id) == 36
    test_run = db.execute(select(TestRun)).scalar_one()
    assert test_run.id == result_id
    assert test_run.rule_id == rule_id
    assert test_run.run_id == "run-dynamic"
    assert test_run.status == "passed"
    assert json.loads(test_run.result_json) == {
        "validation_type": "dynamic_synthetic",
        "attack_total": 2,
        "benign_total": 3,
        "false_positives": 0,
        "true_positives": 2,
    }


def test_record_oracle_evaluation_persists_score() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    _seed_pipeline_run(db, run_id="run-oracle", rule_id=rule_id)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_oracle_evaluation(
        run_id="run-oracle",
        rule_id=rule_id,
        oracle_case_id="oracle-case-1",
        result=OracleEvaluationSchema(
            technique_score=1.0,
            telemetry_score=1.0,
            event_score=0.5,
            benign_avoidance_score=1.0,
            logic_family_score=1.0,
            overall_score=0.9,
        ),
    )

    assert len(result_id) == 36
    oracle_result = db.execute(select(OracleEvaluationResult)).scalar_one()
    assert oracle_result.id == result_id
    assert oracle_result.rule_id == rule_id
    assert oracle_result.run_id == "run-oracle"
    assert oracle_result.oracle_case_id == "oracle-case-1"
    assert oracle_result.score == 0.9
    assert json.loads(oracle_result.details_json)["event_score"] == 0.5


def test_record_regression_persists_status() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    _seed_pipeline_run(db, run_id="run-regression", rule_id=rule_id)
    service = ValidationProofPersistenceService(db)
    details = {"repeated_pattern": "bad-pattern"}

    result_id = service.record_regression(
        run_id="run-regression",
        rule_id=rule_id,
        passed=False,
        details=details,
    )

    assert len(result_id) == 36
    regression_run = db.execute(select(RegressionRun)).scalar_one()
    assert regression_run.id == result_id
    assert regression_run.rule_id == rule_id
    assert regression_run.run_id == "run-regression"
    assert regression_run.status == "failed"
    assert json.loads(regression_run.result_json) == details


def test_generate_proof_obligations_marks_proven_when_required_artifacts_pass() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    _seed_pipeline_run(db, run_id="run-proof", rule_id=rule_id)
    service = ValidationProofPersistenceService(db)

    service.record_static_validation(
        run_id="run-proof",
        rule_id=rule_id,
        report=ValidationReport(is_valid=True, issues=[]),
    )
    service.record_dynamic_validation(
        run_id="run-proof",
        rule_id=rule_id,
        result=SyntheticValidationResult(
            true_positives=2,
            false_positives=0,
            attack_total=2,
            benign_total=3,
        ),
    )
    service.record_regression(
        run_id="run-proof",
        rule_id=rule_id,
        passed=True,
        details={"regressions": []},
    )

    obligation_ids = service.generate_proof_obligations_from_artifacts(
        run_id="run-proof", rule_id=rule_id
    )

    obligations = db.execute(
        select(ProofObligationRecord)
        .where(ProofObligationRecord.id.in_(obligation_ids))
        .order_by(ProofObligationRecord.claim_type)
    ).scalars().all()
    assert {obligation.status for obligation in obligations} == {"proven"}
    assert {obligation.claim_type for obligation in obligations} == {
        "citation_faithful",
        "detects_report_behavior",
        "not_overbroad",
        "telemetry_fields_exist",
    }


def test_generate_proof_obligations_marks_missing_artifacts_unknown() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    obligation_ids = service.generate_proof_obligations_from_artifacts(
        run_id="run-missing-proof", rule_id=rule_id
    )

    obligations = db.execute(
        select(ProofObligationRecord).where(ProofObligationRecord.id.in_(obligation_ids))
    ).scalars().all()
    assert {obligation.status for obligation in obligations} == {"unknown"}


def test_generate_proof_obligations_keeps_static_only_artifacts_unknown() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)
    service.record_static_validation(
        run_id="run-static-only-proof",
        rule_id=rule_id,
        report=ValidationReport(is_valid=True, issues=[]),
    )

    obligation_ids = service.generate_proof_obligations_from_artifacts(
        run_id="run-static-only-proof", rule_id=rule_id
    )

    obligations = db.execute(
        select(ProofObligationRecord).where(ProofObligationRecord.id.in_(obligation_ids))
    ).scalars().all()
    assert {obligation.status for obligation in obligations} == {"unknown"}


def test_verify_persisted_proofs_allows_only_proven_obligations() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    _seed_pipeline_run(db, run_id="run-selectable", rule_id=rule_id)
    service = ValidationProofPersistenceService(db)
    service.record_static_validation(
        run_id="run-selectable",
        rule_id=rule_id,
        report=ValidationReport(is_valid=True, issues=[]),
    )
    service.record_dynamic_validation(
        run_id="run-selectable",
        rule_id=rule_id,
        result=SyntheticValidationResult(
            true_positives=2,
            false_positives=0,
            attack_total=2,
            benign_total=3,
        ),
    )
    service.record_regression(
        run_id="run-selectable",
        rule_id=rule_id,
        passed=True,
        details={"regressions": []},
    )
    service.generate_proof_obligations_from_artifacts(
        run_id="run-selectable", rule_id=rule_id
    )

    assert (
        service.verify_persisted_proofs_selectable(
            run_id="run-selectable", rule_id=rule_id
        )
        is True
    )


def test_verify_persisted_proofs_fails_closed_on_unknown_or_missing_obligations() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    with pytest.raises(ProofObligationError, match="proof obligations missing"):
        service.verify_persisted_proofs_selectable(run_id="run-missing", rule_id=rule_id)

    service.generate_proof_obligations_from_artifacts(run_id="run-unknown", rule_id=rule_id)

    with pytest.raises(ProofObligationError, match="proof obligation"):
        service.verify_persisted_proofs_selectable(run_id="run-unknown", rule_id=rule_id)
