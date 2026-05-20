from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app


client = TestClient(app)


def test_pipeline_run_rejects_invalid_profile() -> None:
    response = client.post(
        "/v1/pipeline:run",
        json={
            "report_id": "rep_demo",
            "profile": "invalid-profile",
        },
    )
    assert response.status_code == 422


def test_pipeline_run_rejects_missing_report_id() -> None:
    response = client.post(
        "/v1/pipeline:run",
        json={
            "profile": "balanced",
        },
    )
    assert response.status_code == 422


def test_pipeline_run_returns_abstain_contract_shape() -> None:
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
    assert body["stage"] == "attack_mapping"
    assert body["abstain_code"] == "ATTACK_CONFIDENCE_BELOW_PROFILE_THRESHOLD"
