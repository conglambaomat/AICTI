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
    assert body["stage"] == "detection_spec"
    assert body["abstain_code"] == "NO_EVIDENCE"
