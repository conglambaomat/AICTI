"""Integration tests for DB-derived metrics and dashboard API summaries."""

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.dashboard import router as dashboard_router
from de_forge.api.routes.metrics import router as metrics_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import PipelineRunRecord, Report


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
    app.include_router(metrics_router)
    app.include_router(dashboard_router)

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), db


def test_metrics_routes_return_empty_database_truthful_summaries() -> None:
    client, _db = _build_client()

    quality_response = client.get("/metrics/quality")
    ops_response = client.get("/metrics/ops")
    dashboard_response = client.get("/dashboard/summary")

    assert quality_response.status_code == 200
    assert quality_response.json() == {
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
    assert ops_response.status_code == 200
    expected_empty_queue: dict[str, object] = {
        "queue_depth": 0,
        "run_success_rate": None,
        "run_counts": {},
        "total_runs": 0,
    }
    assert ops_response.json() == expected_empty_queue
    assert dashboard_response.status_code == 200
    assert dashboard_response.json() == {
        "queue": expected_empty_queue,
        "quality": {
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
        },
    }


def test_metrics_and_dashboard_routes_return_seeded_database_truth() -> None:
    client, db = _build_client()
    now = "2026-05-25T00:00:00+00:00"
    db.add(
        Report(
            id="report-metrics-api",
            source_type="txt",
            source_uri="memory://report-metrics-api",
            title="Metrics API report",
            raw_text="truthful api metrics",
            content_hash="hash-metrics-api",
            metadata_json="{}",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    db.add(
        PipelineRunRecord(
            id="pipeline-run-metrics-api",
            run_id="run-metrics-api",
            report_id="report-metrics-api",
            status="ok",
            stage="completed",
            detection_spec_id=None,
            rule_id=None,
            created_at=now,
        )
    )
    db.commit()

    ops_response = client.get("/metrics/ops")
    dashboard_response = client.get("/dashboard/summary")

    assert ops_response.status_code == 200
    assert ops_response.json() == {
        "queue_depth": 0,
        "run_success_rate": 1.0,
        "run_counts": {"ok": 1},
        "total_runs": 1,
    }
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["queue"] == {
        "queue_depth": 0,
        "run_success_rate": 1.0,
        "run_counts": {"ok": 1},
        "total_runs": 1,
    }
    assert dashboard_response.json()["quality"]["overall_quality"] is None
