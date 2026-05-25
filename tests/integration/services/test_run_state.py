"""Integration tests for database-backed run state service."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    ProofObligationRecord,
    Report,
    ValidationResult,
)
from de_forge.services.run_state import RunStateService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, class_=Session)
    return session_factory()


def _now(offset: int = 0) -> str:
    return (datetime.now(UTC) + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z")


def _seed_run(db: Session, *, run_id: str = "run-1", rule_id: str | None = "rule-1") -> None:
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri=None,
        title="Test report",
        raw_text="Threat activity",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=_now(),
        updated_at=_now(),
    )
    spec = DetectionSpec(
        id="spec-1",
        report_id=report.id,
        abstain_code=None,
        spec_payload=json.dumps({"title": "Credential dumping"}),
        is_validated=True,
    )
    db.add_all([report, spec])
    if rule_id is not None:
        db.add(GeneratedRule(id=rule_id, detection_spec_id=spec.id, rule_content="title: test"))
    db.add(
        PipelineRunRecord(
            id=f"pipeline-{run_id}",
            run_id=run_id,
            report_id=report.id,
            status="completed",
            stage="validation",
            detection_spec_id=spec.id,
            rule_id=rule_id,
            created_at=_now(),
        )
    )
    db.commit()


def test_list_runs_returns_empty_items_when_no_runs_exist() -> None:
    db = _build_session()

    assert RunStateService(db).list_runs() == {"items": []}


def test_list_runs_and_detail_return_persisted_run_payloads() -> None:
    db = _build_session()
    _seed_run(db)
    service = RunStateService(db)

    expected = {
        "id": "pipeline-run-1",
        "run_id": "run-1",
        "report_id": "report-1",
        "status": "completed",
        "stage": "validation",
        "detection_spec_id": "spec-1",
        "rule_id": "rule-1",
    }
    listed = service.list_runs()["items"][0]
    detail = service.get_run_detail("run-1")

    assert listed | expected == listed
    assert detail is not None
    assert detail | expected == detail
    assert service.get_run_detail("missing") is None


def test_get_run_spec_returns_parsed_spec_payload_or_none() -> None:
    db = _build_session()
    _seed_run(db)
    service = RunStateService(db)

    assert service.get_run_spec("run-1") == {
        "run_id": "run-1",
        "detection_spec_id": "spec-1",
        "is_validated": True,
        "abstain_code": None,
        "spec_payload": {"title": "Credential dumping"},
    }
    assert service.get_run_spec("missing") is None


def test_get_run_portfolio_reports_proof_status_from_obligations() -> None:
    db = _build_session()
    _seed_run(db)
    service = RunStateService(db)

    assert service.get_run_portfolio("run-1") == {
        "run_id": "run-1",
        "items": [
            {
                "rule_id": "rule-1",
                "detection_spec_id": "spec-1",
                "proof_status": "missing",
            }
        ],
    }

    db.add(
        ProofObligationRecord(
            id="proof-1",
            run_id="run-1",
            rule_candidate_id="rule-1",
            claim_type="static",
            claim_text="static valid",
            required_artifact_types="[]",
            status="unknown",
        )
    )
    db.commit()
    assert service.get_run_portfolio("run-1")["items"][0]["proof_status"] == "blocked"

    db.query(ProofObligationRecord).delete()
    db.add_all(
        [
            ProofObligationRecord(
                id="proof-2",
                run_id="run-1",
                rule_candidate_id="rule-1",
                claim_type="static",
                claim_text="static valid",
                required_artifact_types="[]",
                status="proven",
            ),
            ProofObligationRecord(
                id="proof-3",
                run_id="run-1",
                rule_candidate_id="rule-1",
                claim_type="dynamic",
                claim_text="dynamic valid",
                required_artifact_types="[]",
                status="proven",
            ),
        ]
    )
    db.commit()
    assert service.get_run_portfolio("run-1")["items"][0]["proof_status"] == "proven"


def test_get_run_validation_returns_ordered_results_with_parsed_details() -> None:
    db = _build_session()
    _seed_run(db)
    db.add_all(
        [
            ValidationResult(
                id="validation-2",
                rule_id="rule-1",
                run_id="run-1",
                status="failed",
                details_json=json.dumps({"order": 2}),
                created_at=_now(2),
            ),
            ValidationResult(
                id="validation-1",
                rule_id="rule-1",
                run_id="run-1",
                status="passed",
                details_json=json.dumps({"order": 1}),
                created_at=_now(1),
            ),
        ]
    )
    db.commit()

    assert RunStateService(db).get_run_validation("run-1") == {
        "run_id": "run-1",
        "items": [
            {
                "id": "validation-1",
                "rule_id": "rule-1",
                "status": "passed",
                "details": {"order": 1},
                "created_at": db.get(ValidationResult, "validation-1").created_at,
            },
            {
                "id": "validation-2",
                "rule_id": "rule-1",
                "status": "failed",
                "details": {"order": 2},
                "created_at": db.get(ValidationResult, "validation-2").created_at,
            },
        ],
    }
