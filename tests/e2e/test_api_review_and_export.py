from __future__ import annotations

from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_post_review_approval() -> None:
    response = client.post(
        "/v1/reviews",
        json={
            "run_id": "run_test123",
            "reviewer": "analyst@example.com",
            "decision": "approved",
            "comments": "Looks good",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["review_id"]
    assert body["run_id"] == "run_test123"
    assert body["decision"] == "approved"


def test_post_review_rejection() -> None:
    response = client.post(
        "/v1/reviews",
        json={
            "run_id": "run_test456",
            "reviewer": "analyst@example.com",
            "decision": "rejected",
            "comments": "False positive risk too high",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"] == "rejected"


def test_export_sigma_requires_approval() -> None:
    response = client.post(
        "/v1/exports/sigma",
        json={
            "run_id": "run_unapproved",
        },
    )

    assert response.status_code == 403
    body = response.json()
    assert "approval" in body["detail"].lower()


def test_export_sigma_success() -> None:
    response = client.post(
        "/v1/exports/sigma",
        json={
            "run_id": "run_approved",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rule_id"]
    assert body["format"] == "sigma"
    assert body["content"]
