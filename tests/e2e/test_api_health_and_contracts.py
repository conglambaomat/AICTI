from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_root_health_still_available() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_post_reports_ingest_endpoint_exists() -> None:
    response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "PowerShell launch behavior observed",
            "external_ref": "r-001",
            "metadata": {"title": "sample"},
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "report_id" in body
    assert body["status"] == "ingested"
    assert "trace_id" in body


def test_post_pipeline_run_endpoint_exists() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    response = client.post(
        "/v1/pipeline:run",
        json={
            "report_id": report_id,
            "profile": "balanced",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "run_id" in body
    assert body["status"] == "ok"
    assert body["abstain"] is False
    assert body["stage"] == "awaiting_review"
