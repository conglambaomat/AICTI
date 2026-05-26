"""Production gate tests for development-only seed routes."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from de_forge.core.config import Settings
from de_forge.main import app, create_app


def test_seed_routes_are_not_mounted_by_default() -> None:
    response = TestClient(app).post("/v1/pipeline:seed")

    assert response.status_code == 404


def test_seed_router_can_be_mounted_explicitly_for_dev_tools() -> None:
    from de_forge.api.routes.pipeline import seed_router

    dev_app = FastAPI()
    dev_app.include_router(seed_router)

    response = TestClient(dev_app, raise_server_exceptions=False).post("/v1/pipeline:seed")

    assert response.status_code in {201, 500}


def test_create_app_mounts_seed_routes_when_enabled_in_development() -> None:
    dev_app = create_app(
        Settings(env="development", enable_dev_seed_routes=True, openai_api_key="test-key")
    )

    response = TestClient(dev_app, raise_server_exceptions=False).post("/v1/pipeline:seed")

    assert response.status_code in {201, 500}


def test_create_app_mounts_seed_routes_when_enabled_in_test() -> None:
    test_app = create_app(Settings(env="test", enable_dev_seed_routes=True, openai_api_key="test-key"))

    response = TestClient(test_app, raise_server_exceptions=False).post("/v1/pipeline:seed")

    assert response.status_code in {201, 500}


def test_create_app_does_not_mount_seed_routes_in_production_when_enabled() -> None:
    prod_app = create_app(
        Settings(env="production", enable_dev_seed_routes=True, openai_api_key="test-key")
    )

    response = TestClient(prod_app).post("/v1/pipeline:seed")

    assert response.status_code == 404
