"""Integration tests for production Sigma export gates."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.main import app
from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    ProofObligationRecord,
    Report,
)
from de_forge.services.review import ReviewService


_REQUIRED_CLAIMS = [
    "detects_report_behavior",
    "not_overbroad",
    "telemetry_fields_exist",
    "positive_tests_pass",
    "benign_baseline_not_matched",
    "citation_faithful",
    "oracle_expectations_satisfied",
    "regression_safe",
]


def _build_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_export_blocks_manual_rule_without_compiler_provenance() -> None:
    db = _build_session()
    now = datetime.now(UTC).isoformat()
    report_id = "report-export-provenance"
    spec_id = "spec-export-provenance"
    rule_id = "rule-export-provenance"
    run_id = "run-export-provenance"

    db.add(
        Report(
            id=report_id,
            source_type="txt",
            source_uri="test://export-provenance",
            title="Export provenance test report",
            raw_text="PowerShell encoded command observed.",
            content_hash="export-provenance-hash",
            metadata_json="{}",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    db.add(
        DetectionSpec(
            id=spec_id,
            report_id=report_id,
            spec_payload='{"detection_strategy":"process command line"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRule(
            id=rule_id,
            detection_spec_id=spec_id,
            rule_content="title: manual rule\ndetection:\n  condition: selection\n",
        )
    )
    db.add(
        PipelineRunRecord(
            id="pipeline-run-export-provenance",
            run_id=run_id,
            report_id=report_id,
            status="ok",
            stage="awaiting_review",
            detection_spec_id=spec_id,
            rule_id=rule_id,
            created_at=now,
        )
    )
    for index, claim_type in enumerate(_REQUIRED_CLAIMS, start=1):
        db.add(
            ProofObligationRecord(
                id=f"proof-export-provenance-{index}",
                run_id=run_id,
                rule_candidate_id=rule_id,
                claim_type=claim_type,
                claim_text=f"{claim_type} is proven.",
                required_artifact_types='["test_artifact"]',
                status="proven",
                justification=None,
            )
        )
    db.commit()
    ReviewService(db).record_decision(
        rule_id=rule_id,
        run_id=run_id,
        decision="approved",
        reviewer="analyst@example.com",
        comments="Approved after checking proof rows.",
    )

    app.dependency_overrides[get_db] = lambda: db
    try:
        response = TestClient(app).post("/v1/exports/sigma", json={"run_id": run_id})
    finally:
        app.dependency_overrides.clear()
        db.close()

    assert response.status_code == 403
    assert response.json()["detail"] == "COMPILER_PROVENANCE_MISSING"


def test_export_blocks_generated_rule_with_placeholder_compiler_provenance() -> None:
    db = _build_session()
    now = datetime.now(UTC).isoformat()
    report_id = "report-export-placeholder-provenance"
    spec_id = "spec-export-placeholder-provenance"
    rule_id = "rule-export-placeholder-provenance"
    run_id = "run-export-placeholder-provenance"

    db.add(
        Report(
            id=report_id,
            source_type="txt",
            source_uri="test://export-placeholder-provenance",
            title="Export placeholder provenance test report",
            raw_text="PowerShell encoded command observed.",
            content_hash="export-placeholder-provenance-hash",
            metadata_json="{}",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    db.add(
        DetectionSpec(
            id=spec_id,
            report_id=report_id,
            spec_payload='{"detection_strategy":"process command line"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRule(
            id=rule_id,
            detection_spec_id=spec_id,
            rule_content="title: generated draft rule\ndetection:\n  condition: selection\n",
            generation_source="compiler",
            detection_ast_id=f"ast-{rule_id}",
            compiled_sigma_id=f"sigma-{rule_id}",
        )
    )
    db.add(
        PipelineRunRecord(
            id="pipeline-run-export-placeholder-provenance",
            run_id=run_id,
            report_id=report_id,
            status="ok",
            stage="awaiting_review",
            detection_spec_id=spec_id,
            rule_id=rule_id,
            created_at=now,
        )
    )
    for index, claim_type in enumerate(_REQUIRED_CLAIMS, start=1):
        db.add(
            ProofObligationRecord(
                id=f"proof-export-placeholder-provenance-{index}",
                run_id=run_id,
                rule_candidate_id=rule_id,
                claim_type=claim_type,
                claim_text=f"{claim_type} is proven.",
                required_artifact_types='["test_artifact"]',
                status="proven",
                justification=None,
            )
        )
    db.commit()
    ReviewService(db).record_decision(
        rule_id=rule_id,
        run_id=run_id,
        decision="approved",
        reviewer="analyst@example.com",
        comments="Approved after checking proof rows.",
    )

    app.dependency_overrides[get_db] = lambda: db
    try:
        response = TestClient(app).post("/v1/exports/sigma", json={"run_id": run_id})
    finally:
        app.dependency_overrides.clear()
        db.close()

    assert response.status_code == 403
    assert response.json()["detail"] == "COMPILER_PROVENANCE_MISSING"
