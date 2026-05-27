from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.db.base import Base
from de_forge.db.session import get_db


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()

    app = FastAPI()

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok"}

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(pipeline_router)
    return TestClient(app), db


def test_get_run_status_unknown_run_is_not_found_fail_closed() -> None:
    client, _db = _build_client()
    response = client.get("/v1/runs/run_unknown_realistic")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]


def test_get_run_status_after_failed_run_reports_failed_stage() -> None:
    client, _db = _build_client()
    failed_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": "rep_force_error", "profile": "balanced"},
    )
    assert failed_run.status_code == 500
    run_id = failed_run.json()["run_id"]

    status = client.get(f"/v1/runs/{run_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "failed"
    assert body["stage"] == "failed_generation"


def test_get_run_status_after_memory_gate_failure_reports_failed_memory_stage() -> None:
    client, _db = _build_client()
    failed_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": "rep_force_memory_contract_error", "profile": "balanced"},
    )
    assert failed_run.status_code == 500
    run_id = failed_run.json()["run_id"]

    status = client.get(f"/v1/runs/{run_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "failed"
    assert body["stage"] == "failed_memory_contract"


def test_seed_endpoints_not_available_in_production() -> None:
    client, _db = _build_client()
    assert client.post("/v1/pipeline:seed").status_code == 404
    assert client.post("/v1/pipeline:seed-abstain").status_code == 404
