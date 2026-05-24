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


def test_review_rejects_invalid_decision_before_persistence() -> None:
    response = client.post(
        "/v1/reviews",
        json={
            "run_id": "run_demo",
            "reviewer": "analyst@example.com",
            "decision": "maybe",
            "comments": "Invalid review decision.",
        },
    )

    assert response.status_code == 422


def test_review_route_passes_run_context_and_comments_to_service(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import ReviewRequest

    captured = {}

    class FakeRecord:
        rule_id = "rule_demo"

    class FakeReviewService:
        def __init__(self, db) -> None:
            self.db = db

        def record_decision(self, **kwargs) -> str:
            captured.update(kwargs)
            return "review_demo"

    monkeypatch.setattr(pipeline, "assert_schema_contract_current", lambda db: None)
    monkeypatch.setattr(pipeline, "_resolve_run_record", lambda db, run_id: FakeRecord())
    monkeypatch.setattr(pipeline, "ReviewService", FakeReviewService)

    payload = ReviewRequest(
        run_id="run_demo",
        reviewer="analyst@example.com",
        decision="approved",
        comments="Persist this audit comment.",
    )

    response = __import__("asyncio").run(pipeline.create_review(payload, db=object()))

    assert response.run_id == "run_demo"
    assert captured["run_id"] == "run_demo"
    assert captured["comments"] == "Persist this audit comment."

