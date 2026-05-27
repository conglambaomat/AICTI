from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import (
    PipelineRunRecord,
    ProofObligationRecord,
    RegressionRun,
    ValidationResult,
)
from de_forge.services.metrics import MetricsService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, class_=Session)
    return session_factory()


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def test_metrics_service_summarizes_quality_snapshot() -> None:
    summary = MetricsService().quality_snapshot(
        citation_faithfulness=1.0,
        proof_pass_rate=0.9,
        static_validity_rate=0.95,
        regression_pass_rate=1.0,
    )

    assert summary["citation_faithfulness"] == 1.0
    assert summary["overall_quality"] == 0.9625


def test_quality_summary_uses_persisted_counts() -> None:
    db = _build_session()
    now = _now()
    db.add_all(
        [
            ProofObligationRecord(
                id="proof-1",
                run_id="run-1",
                rule_candidate_id="rule-1",
                claim_type="citation_faithful",
                claim_text="citation exact",
                required_artifact_types="[]",
                status="proven",
                justification="ok",
            ),
            ProofObligationRecord(
                id="proof-2",
                run_id="run-1",
                rule_candidate_id="rule-1",
                claim_type="not_overbroad",
                claim_text="not broad",
                required_artifact_types="[]",
                status="unknown",
                justification=None,
            ),
            ValidationResult(
                id="validation-1",
                rule_id="rule-1",
                run_id="run-1",
                status="passed",
                details_json="{}",
                created_at=now,
            ),
            ValidationResult(
                id="validation-2",
                rule_id="rule-1",
                run_id="run-1",
                status="failed",
                details_json="{}",
                created_at=now,
            ),
            RegressionRun(
                id="regression-1",
                rule_id="rule-1",
                run_id="run-1",
                status="passed",
                result_json="{}",
                created_at=now,
            ),
        ]
    )
    db.commit()

    summary = MetricsService(db).quality_summary()

    assert summary["sample_counts"]["proof_obligations"] == 2
    assert summary["sample_counts"]["static_validations"] == 2
    assert summary["sample_counts"]["regression_runs"] == 1
    assert summary["citation_faithfulness"] == 1.0
    assert summary["proof_pass_rate"] == 0.5
    assert summary["static_validity_rate"] == 0.5
    assert summary["regression_pass_rate"] == 1.0


def test_ops_summary_uses_persisted_run_counts() -> None:
    db = _build_session()
    now = _now()
    db.add_all(
        [
            PipelineRunRecord(
                id="pipeline-ok",
                run_id="run-ok",
                report_id="report-1",
                status="ok",
                stage="complete",
                detection_spec_id="spec-1",
                rule_id="rule-1",
                created_at=now,
            ),
            PipelineRunRecord(
                id="pipeline-failed",
                run_id="run-failed",
                report_id="report-1",
                status="failed",
                stage="validation",
                detection_spec_id="spec-1",
                rule_id="rule-1",
                created_at=now,
            ),
            PipelineRunRecord(
                id="pipeline-running",
                run_id="run-running",
                report_id="report-1",
                status="running",
                stage="proof",
                detection_spec_id="spec-1",
                rule_id="rule-1",
                created_at=now,
            ),
        ]
    )
    db.commit()

    summary = MetricsService(db).ops_summary()

    assert summary == {
        "queue_depth": 1,
        "run_success_rate": 0.5,
        "run_counts": {"failed": 1, "ok": 1, "running": 1},
        "total_runs": 3,
    }
