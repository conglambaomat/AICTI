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
