from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_legacy_review_response_declares_non_authoritative() -> None:
    response = client.post(
        "/api/review",
        json={
            "run_id": "run_1",
            "rule_candidate_id": "candidate_1",
            "action": "approve",
            "reviewer_notes": "ok",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is False
    assert body["authoritative_for_export"] is False


def test_review_assert_export_requires_persisted_run_context() -> None:
    response = client.post(
        "/review/assert-export",
        json={"rule_id": "candidate_1", "rule_status": "awaiting_review"},
    )

    assert response.status_code == 422


def test_legacy_review_does_not_report_export_allowed() -> None:
    response = client.post(
        "/api/review",
        json={
            "run_id": "run_1",
            "rule_candidate_id": "candidate_1",
            "action": "approve",
            "reviewer_notes": "ok",
        },
    )

    assert response.status_code == 200
    assert response.json()["export_allowed"] is False
