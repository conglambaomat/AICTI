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


def test_pipeline_seed_abstain_endpoint_not_available_in_production() -> None:
    client, _db = _build_client()
    seed = client.post("/v1/pipeline:seed-abstain")
    assert seed.status_code == 404


def test_pipeline_run_failed_response_contract() -> None:
    client, _db = _build_client()
    response = client.post(
        "/v1/pipeline:run",
        json={
            "report_id": "rep_force_error",
            "profile": "balanced",
        },
    )

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_code"] == "PIPELINE_EXECUTION_ERROR"
    assert body["message"]
    assert body["trace_id"]
    assert body["run_id"]
