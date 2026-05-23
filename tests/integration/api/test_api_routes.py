from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_start_golden_run_endpoint_returns_awaiting_review() -> None:
    response = client.post(
        "/api/runs/golden",
        json={"report_id": "report_1", "report_text": "PowerShell -enc AAA", "mode": "auto"},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "awaiting_review"


def test_review_endpoint_blocks_export_on_reject() -> None:
    response = client.post(
        "/api/review",
        json={
            "run_id": "run_1",
            "rule_candidate_id": "candidate_1",
            "action": "reject",
            "reviewer_notes": "Too broad",
        },
    )

    assert response.status_code == 200
    assert response.json()["export_allowed"] is False


def test_metrics_endpoint_returns_quality_summary() -> None:
    response = client.get("/api/metrics/quality")

    assert response.status_code == 200
    assert "overall_quality" in response.json()


def test_review_ui_page_contains_trust_columns() -> None:
    response = client.get("/api/ui/review")

    assert response.status_code == 200
    assert "Evidence quote" in response.text
    assert "Detection logic" in response.text
    assert "Sigma condition" in response.text
    assert "Proof status" in response.text
