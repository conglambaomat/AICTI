from fastapi.testclient import TestClient

from de_forge.core.config import Settings
from de_forge.main import app, create_app


def test_ready_endpoint_reports_policy_checks() -> None:
    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert "ready" in body
    assert "checks" in body
    assert "schema" in body["checks"]
    assert body["checks"]["seed_routes"] == "ok"
    assert body["checks"]["provider_config"] == "ok"


def test_factory_app_exposes_ready_endpoint_with_injected_settings() -> None:
    test_app = create_app(Settings(env="test", openai_model="test-model"))

    response = TestClient(test_app).get("/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["provider_config"] == "ok"


def test_ready_endpoint_fails_without_production_provider_key() -> None:
    test_app = create_app(Settings(env="production", openai_api_key=""))

    response = TestClient(test_app).get("/ready")

    body = response.json()
    assert response.status_code == 200
    assert body["ready"] is False
    assert body["readiness"] == "not_ready"
    assert body["checks"]["provider_config"] == "failed"
    assert "provider_config_missing" in body["errors"]


def test_ready_endpoint_fails_when_seed_routes_enabled_outside_dev() -> None:
    test_app = create_app(
        Settings(env="production", openai_api_key="key", enable_dev_seed_routes=True)
    )

    response = TestClient(test_app).get("/ready")

    body = response.json()
    assert response.status_code == 200
    assert body["ready"] is False
    assert body["readiness"] == "not_ready"
    assert body["checks"]["seed_routes"] == "failed"
    assert "seed_routes_enabled_outside_dev" in body["errors"]
