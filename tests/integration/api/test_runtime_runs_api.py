"""Integration tests for runtime runs API backed by persisted state."""

from __future__ import annotations

import json
from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.runs import router as runs_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import DetectionSpec, GeneratedRule, PipelineRunRecord, Report, ValidationResult


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()

    app = FastAPI()
    app.include_router(runs_router)

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), db


def _seed_run(db: Session) -> None:
    now = "2026-05-24T00:00:00Z"
    report = Report(
        id="report-api",
        source_type="txt",
        source_uri=None,
        title="Runtime API report",
        raw_text="Threat behavior",
        content_hash="hash-api",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    spec = DetectionSpec(
        id="spec-api",
        report_id=report.id,
        abstain_code=None,
        spec_payload=json.dumps({"title": "Runtime API spec"}),
        is_validated=True,
    )
    rule = GeneratedRule(id="rule-api", detection_spec_id=spec.id, rule_content="title: api")
    run = PipelineRunRecord(
        id="pipeline-run-api",
        run_id="run-api",
        report_id=report.id,
        status="completed",
        stage="validation",
        detection_spec_id=spec.id,
        rule_id=rule.id,
        created_at=now,
    )
    validation = ValidationResult(
        id="validation-api",
        rule_id=rule.id,
        run_id=run.run_id,
        status="passed",
        details_json=json.dumps({"score": 1.0}),
        created_at=now,
    )
    db.add_all([report, spec, rule, run, validation])
    db.commit()


def test_list_runs_returns_empty_items_when_no_runs_exist() -> None:
    client, _db = _build_client()

    response = client.get("/runs")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_runtime_run_endpoints_return_404_when_run_is_missing() -> None:
    client, _db = _build_client()

    for path in (
        "/runs/missing-run",
        "/runs/missing-run/spec",
        "/runs/missing-run/portfolio",
        "/runs/missing-run/validation",
    ):
        response = client.get(path)
        assert response.status_code == 404


def test_runtime_run_endpoints_return_persisted_state() -> None:
    client, db = _build_client()
    _seed_run(db)

    expected_run = {
        "id": "pipeline-run-api",
        "run_id": "run-api",
        "report_id": "report-api",
        "status": "completed",
        "stage": "validation",
        "detection_spec_id": "spec-api",
        "rule_id": "rule-api",
        "created_at": "2026-05-24T00:00:00Z",
    }

    assert client.get("/runs").json() == {"items": [expected_run]}
    assert client.get("/runs/run-api").json() == expected_run
    assert client.get("/runs/run-api/spec").json() == {
        "run_id": "run-api",
        "detection_spec_id": "spec-api",
        "is_validated": True,
        "abstain_code": None,
        "spec_payload": {"title": "Runtime API spec"},
    }
    assert client.get("/runs/run-api/portfolio").json() == {
        "run_id": "run-api",
        "items": [
            {
                "rule_id": "rule-api",
                "detection_spec_id": "spec-api",
                "proof_status": "missing",
            }
        ],
    }
    assert client.get("/runs/run-api/validation").json() == {
        "run_id": "run-api",
        "items": [
            {
                "id": "validation-api",
                "rule_id": "rule-api",
                "status": "passed",
                "details": {"score": 1.0},
                "created_at": "2026-05-24T00:00:00Z",
            }
        ],
    }
