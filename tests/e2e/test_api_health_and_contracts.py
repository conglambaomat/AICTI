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


def test_root_health_still_available() -> None:
    client, _db = _build_client()
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_post_reports_ingest_rejects_invalid_external_ref_fail_closed() -> None:
    client, _db = _build_client()
    content = "PowerShell launch behavior observed\n\nEncoded command spawned child process"
    response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": content,
            "external_ref": "r-001",
            "metadata": {"title": "sample"},
        },
    )

    assert response.status_code == 400


def test_pipeline_seed_endpoint_not_available_in_production() -> None:
    client, _db = _build_client()
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 404
