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


def test_seed_endpoint_not_available_in_production() -> None:
    client, _db = _build_client()
    response = client.post("/v1/pipeline:seed")
    assert response.status_code == 404


def test_review_requires_existing_run_mapping() -> None:
    client, _db = _build_client()
    response = client.post(
        "/v1/reviews",
        json={
            "run_id": "run_nonexistent",
            "reviewer": "analyst@example.com",
            "decision": "approved",
            "comments": "Looks good",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Run mapping not found"


def test_review_rejects_invalid_decision() -> None:
    client, _db = _build_client()
    response = client.post(
        "/v1/reviews",
        json={
            "run_id": "run_nonexistent",
            "reviewer": "analyst@example.com",
            "decision": "maybe",
            "comments": "Invalid review decision.",
        },
    )
    assert response.status_code == 422


def test_export_requires_existing_run_mapping() -> None:
    client, _db = _build_client()
    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": "run_nonexistent"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Run mapping not found"
