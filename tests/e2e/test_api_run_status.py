from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_get_run_status_returns_run_details() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.get(f"/v1/runs/{run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["status"] in ["pending", "running", "completed", "failed"]
    assert "created_at" in body
    assert body["report_id"] == detection_spec_id
    assert body["detection_spec_id"] == detection_spec_id


def test_get_run_status_unknown_run_is_not_found_fail_closed() -> None:
    response = client.get("/v1/runs/run_unknown_realistic")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]


def test_get_run_status_after_abstain_run_reports_detection_spec_stage() -> None:
    seed = client.post("/v1/pipeline:seed-abstain")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    status = client.get(f"/v1/runs/{run_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["stage"] == "detection_spec"
    assert body["status"] == "completed"
    assert body["detection_spec_id"] == detection_spec_id


def test_get_run_status_after_failed_run_reports_failed_stage() -> None:
    failed_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": "rep_force_error", "profile": "balanced"},
    )
    assert failed_run.status_code == 500
    run_id = failed_run.json()["run_id"]

    status = client.get(f"/v1/runs/{run_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "failed"
    assert body["stage"] == "failed_generation"


def test_get_run_status_after_memory_gate_failure_reports_failed_memory_stage() -> None:
    failed_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": "rep_force_memory_contract_error", "profile": "balanced"},
    )
    assert failed_run.status_code == 500
    run_id = failed_run.json()["run_id"]

    status = client.get(f"/v1/runs/{run_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "failed"
    assert body["stage"] == "failed_memory_contract"


def test_get_run_status_not_found() -> None:
    response = client.get("/v1/runs/run_nonexistent")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]


def test_get_run_status_not_found() -> None:
    response = client.get("/v1/runs/run_nonexistent")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]
