from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_reports_page_renders() -> None:
    response = client.get("/api/ui/reports")

    assert response.status_code == 200
    assert "DE-Forge UI" in response.text
    assert "Reports" in response.text


def test_run_detail_page_renders() -> None:
    response = client.get("/api/ui/runs/run_1")

    assert response.status_code == 200
    assert "Run Detail" in response.text
    assert "run_1" in response.text


def test_evidence_spec_page_renders_trust_depth() -> None:
    response = client.get("/api/ui/runs/run_1/evidence-spec")

    assert response.status_code == 200
    assert "Evidence + DetectionSpec" in response.text
    assert "Lineage" in response.text
    assert "Citation" in response.text
    assert "Validation" in response.text
    assert "Oracle" in response.text


def test_portfolio_review_page_renders_trust_and_actions() -> None:
    response = client.get("/api/ui/runs/run_1/portfolio-review")

    assert response.status_code == 200
    assert "Rule Portfolio + Review" in response.text
    assert "Evidence quote" in response.text
    assert "Detection logic" in response.text
    assert "Sigma condition" in response.text
    assert "Proof status" in response.text
    assert "Approve" in response.text
    assert "Reject" in response.text
    assert "Reviewer" in response.text


def test_dashboard_page_renders_with_convenience_controls() -> None:
    response = client.get("/api/ui/dashboard")

    assert response.status_code == 200
    assert "Ops Dashboard" in response.text
    assert "Queue" in response.text
    assert "Filter" in response.text
    assert "Sort" in response.text
    assert "Search" in response.text
    assert "Saved view" in response.text
