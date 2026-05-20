from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app


client = TestClient(app)


def test_get_run_status_returns_run_details() -> None:
    response = client.get("/v1/runs/run_test123")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_test123"
    assert body["status"] in ["pending", "running", "completed", "failed"]
    assert "created_at" in body


def test_get_run_status_not_found() -> None:
    response = client.get("/v1/runs/run_nonexistent")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]
