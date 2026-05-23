"""API route smoke tests to improve coverage for route wiring."""

from fastapi.testclient import TestClient

from de_forge.main import app


client = TestClient(app)


def test_root_health_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "DE-Forge"
    assert body["database"] in {"connected", "disconnected"}
    assert body["readiness"] in {"ready", "not_ready"}
    assert body["ready"] is (body["readiness"] == "ready")
    assert body["ok"] is body["ready"]
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["database"] in {"ok", "failed"}
    assert body["checks"]["orchestrator"] == "ok"
    assert isinstance(body["errors"], list)
    assert body["run_id"]
    assert body["trace_id"]
    assert body["timestamp_utc"]
    assert body["uptime_seconds"] >= 0
    assert body["details"]["db_probe"] == "select_1"
    assert body["details"]["lifecycle"]["state"] == "running"
    assert body["details"]["lifecycle"]["mode"] in {"auto", "cautious"}
    assert body["details"]["lifecycle"]["gate"] == "operational"


def test_pipeline_route_rejects_missing_payload() -> None:
    response = client.post("/pipeline/run", json={})
    assert response.status_code == 422


def test_review_decision_route_rejects_missing_payload() -> None:
    response = client.post("/review/decision", json={})
    assert response.status_code == 422


def test_review_assert_export_route_rejects_missing_payload() -> None:
    response = client.post("/review/assert-export", json={})
    assert response.status_code == 422


def test_ingestion_route_rejects_missing_file() -> None:
    response = client.post("/ingest")
    assert response.status_code == 422
