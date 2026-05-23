from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)


def test_runs_list_endpoint_returns_items() -> None:
    response = client.get("/api/runs")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert isinstance(payload["items"], list)


def test_run_detail_endpoint_returns_run_id() -> None:
    response = client.get("/api/runs/run_1")

    assert response.status_code == 200
    assert response.json()["run_id"] == "run_1"


def test_run_evidence_endpoint_returns_quotes() -> None:
    response = client.get("/api/runs/run_1/evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run_1"
    assert isinstance(payload["items"], list)


def test_run_spec_endpoint_returns_detection_spec_shape() -> None:
    response = client.get("/api/runs/run_1/spec")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run_1"
    assert "telemetry_requirements" in payload


def test_run_portfolio_endpoint_returns_candidates() -> None:
    response = client.get("/api/runs/run_1/portfolio")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run_1"
    assert isinstance(payload["items"], list)


def test_run_validation_endpoint_returns_scores() -> None:
    response = client.get("/api/runs/run_1/validation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run_1"
    assert "static_valid" in payload
    assert "dynamic_score" in payload


def test_review_queue_endpoint_returns_pending_items() -> None:
    response = client.get("/api/review/queue")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert isinstance(payload["items"], list)


def test_ops_metrics_endpoint_returns_operational_summary() -> None:
    response = client.get("/api/metrics/ops")

    assert response.status_code == 200
    payload = response.json()
    assert "queue_depth" in payload
    assert "avg_latency_ms" in payload


def test_dashboard_summary_endpoint_returns_topline_cards() -> None:
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    payload = response.json()
    assert "queue" in payload
    assert "quality" in payload
    assert "throughput" in payload
