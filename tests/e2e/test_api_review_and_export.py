from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_post_review_approval() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_id,
            "reviewer": "analyst@example.com",
            "decision": "approved",
            "comments": "Looks good",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["review_id"]
    assert body["run_id"] == run_id
    assert body["decision"] == "approved"


def test_post_review_rejection() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_id,
            "reviewer": "analyst@example.com",
            "decision": "rejected",
            "comments": "False positive risk too high",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"] == "rejected"


def test_export_sigma_requires_approval() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 403
    body = response.json()
    assert "approval" in body["detail"].lower()


def test_export_sigma_success() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]
    rule_id = seed.json()["rule_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}")
    assert approve.status_code == 201

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rule_id"] == rule_id
    assert body["format"] == "sigma"
    assert body["content"]


def test_export_sigma_blocked_when_latest_decision_is_rejected() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    detection_spec_id = seed.json()["detection_spec_id"]
    rule_id = seed.json()["rule_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": detection_spec_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}")
    assert approve.status_code == 201

    reject = client.post(f"/v1/pipeline:reject?rule_id={rule_id}")
    assert reject.status_code == 201

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 403
    body = response.json()
    assert "approval" in body["detail"].lower()
