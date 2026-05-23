from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_pipeline_run_abstain_response_contract() -> None:
    response = client.post(
        "/v1/pipeline:run",
        json={
            "report_id": "rep_demo",
            "profile": "strict",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "abstain"
    assert body["abstain"] is True
    assert body["abstain_code"] == "ATTACK_CONFIDENCE_BELOW_PROFILE_THRESHOLD"
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
