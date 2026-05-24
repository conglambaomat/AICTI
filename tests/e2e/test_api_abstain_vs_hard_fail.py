from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_pipeline_run_abstain_response_contract() -> None:
    seed = client.post("/v1/pipeline:seed-abstain")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    response = client.post(
        "/v1/pipeline:run",
        json={
            "report_id": report_id,
            "profile": "strict",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "abstain"
    assert body["abstain"] is True
    assert body["abstain_code"] == "NO_EVIDENCE"
    assert body["reason"]


def test_pipeline_run_failed_response_contract() -> None:
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
