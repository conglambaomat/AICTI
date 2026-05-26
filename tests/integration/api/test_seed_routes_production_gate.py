"""Production gate tests for development-only seed routes."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from de_forge.main import app


def test_seed_routes_are_not_mounted_by_default() -> None:
    response = TestClient(app).post("/v1/pipeline:seed")

    assert response.status_code == 404


def test_seed_router_can_be_mounted_explicitly_for_dev_tools() -> None:
    from de_forge.api.routes.pipeline import seed_router

    dev_app = FastAPI()
    dev_app.include_router(seed_router)

    response = TestClient(dev_app, raise_server_exceptions=False).post("/v1/pipeline:seed")

    assert response.status_code in {201, 500}
