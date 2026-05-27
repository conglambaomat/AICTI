from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    ProofObligationRecord,
    RegressionRun,
    Report,
    ReviewDecision,
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


def _seed_metrics_rows(db: Session) -> None:
    now = _now()
    report = Report(
        id="report-metrics",
        source_type="txt",
        source_uri=None,
        title="Metrics report",
        raw_text="Threat activity",
        content_hash="hash-metrics",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    spec = DetectionSpec(
        id="spec-metrics",
        report_id=report.id,
        spec_payload=json.dumps({"title": "metrics"}),
        is_validated=True,
    )
    rule = GeneratedRule(
        id="rule-metrics",
        detection_spec_id=spec.id,
        rule_content="title: metrics",
    )
    db.add_all([report, spec, rule])
    db.add_all(
        [
            PipelineRunRecord(
                id="pipeline-ok",
                run_id="run-ok",
                report_id=report.id,
                status="ok",
                stage="complete",
                detection_spec_id=spec.id,
                rule_id=rule.id,
                created_at=now,
            ),
            PipelineRunRecord(
                id="pipeline-failed",
                run_id="run-failed",
                report_id=report.id,
                status="failed",
                stage="validation",
                detection_spec_id=spec.id,
                rule_id=rule.id,
                created_at=now,
            ),
            PipelineRunRecord(
                id="pipeline-running",
                run_id="run-running",
                report_id=report.id,
                status="running",
                stage="proof",
                detection_spec_id=spec.id,
                rule_id=rule.id,
                created_at=now,
            ),
        ]
    )
    db.add_all(
        [
            ValidationResult(
                id="validation-passed",
                rule_id=rule.id,
                run_id="run-ok",
                status="passed",
                details_json="{}",
                created_at=now,
            ),
            ValidationResult(
                id="validation-failed",
                rule_id=rule.id,
                run_id="run-failed",
                status="failed",
                details_json="{}",
                created_at=now,
            ),
            ProofObligationRecord(
                id="proof-citation",
                run_id="run-ok",
                rule_candidate_id=rule.id,
                claim_type="citation_faithful",
                claim_text="Citation is faithful",
                required_artifact_types="[]",
                status="proven",
                justification="ok",
            ),
            ProofObligationRecord(
                id="proof-overbroad",
                run_id="run-failed",
                rule_candidate_id=rule.id,
                claim_type="not_overbroad",
                claim_text="Rule is not overbroad",
                required_artifact_types="[]",
                status="unknown",
                justification=None,
            ),
            RegressionRun(
                id="regression-passed",
                rule_id=rule.id,
                run_id="run-ok",
                status="passed",
                result_json="{}",
                created_at=now,
            ),
            ReviewDecision(
                id="review-approved",
                rule_id=rule.id,
                run_id="run-ok",
                decision="approved",
                reviewer="analyst",
                comments="approved",
                created_at=now,
            ),
        ]
    )
    db.commit()


def test_quality_snapshot_preserves_explicit_rates_and_average() -> None:
    snapshot = MetricsService().quality_snapshot(0.8, 0.6, 1.0, 0.4)

    assert snapshot == {
        "citation_faithfulness": 0.8,
        "proof_pass_rate": 0.6,
        "static_validity_rate": 1.0,
        "regression_pass_rate": 0.4,
        "overall_quality": 0.7,
    }


def test_empty_db_quality_summary_reports_unknown_rates_and_zero_samples() -> None:
    db = _build_session()

    summary = MetricsService(db).quality_summary()

    assert summary == {
        "citation_faithfulness": None,
        "proof_pass_rate": None,
        "static_validity_rate": None,
        "regression_pass_rate": None,
        "overall_quality": None,
        "sample_counts": {
            "proof_obligations": 0,
            "static_validations": 0,
            "regression_runs": 0,
        },
    }


def test_populated_db_quality_summary_reports_database_derived_rates() -> None:
    db = _build_session()
    _seed_metrics_rows(db)

    summary = MetricsService(db).quality_summary()

    assert summary == {
        "citation_faithfulness": 1.0,
        "proof_pass_rate": 0.5,
        "static_validity_rate": 0.5,
        "regression_pass_rate": 1.0,
        "overall_quality": 0.75,
        "sample_counts": {
            "proof_obligations": 2,
            "static_validations": 2,
            "regression_runs": 1,
        },
    }


def test_empty_db_ops_summary_reports_no_runs() -> None:
    db = _build_session()

    summary = MetricsService(db).ops_summary()

    assert summary == {
        "queue_depth": 0,
        "run_success_rate": None,
        "run_counts": {},
        "total_runs": 0,
    }


def test_populated_db_ops_summary_reports_database_derived_runtime_state() -> None:
    db = _build_session()
    _seed_metrics_rows(db)

    summary = MetricsService(db).ops_summary()

    assert summary == {
        "queue_depth": 1,
        "run_success_rate": 0.5,
        "run_counts": {"failed": 1, "ok": 1, "running": 1},
        "total_runs": 3,
    }


def test_populated_db_dashboard_summary_returns_database_derived_queue_and_quality() -> None:
    db = _build_session()
    _seed_metrics_rows(db)

    summary = MetricsService(db).dashboard_summary()

    assert summary == {
        "queue": {
            "queue_depth": 1,
            "run_success_rate": 0.5,
            "run_counts": {"failed": 1, "ok": 1, "running": 1},
            "total_runs": 3,
        },
        "quality": {
            "citation_faithfulness": 1.0,
            "proof_pass_rate": 0.5,
            "static_validity_rate": 0.5,
            "regression_pass_rate": 1.0,
            "overall_quality": 0.75,
            "sample_counts": {
                "proof_obligations": 2,
                "static_validations": 2,
                "regression_runs": 1,
            },
        },
    }


@pytest.mark.parametrize(
    "method_name",
    ["quality_summary", "ops_summary", "dashboard_summary"],
)
def test_db_backed_summary_methods_without_db_raise_value_error(method_name: str) -> None:
    method = getattr(MetricsService(), method_name)

    with pytest.raises(ValueError, match="^database session required$"):
        method()
