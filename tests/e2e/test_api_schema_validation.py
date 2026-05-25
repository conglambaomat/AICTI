from __future__ import annotations

import asyncio

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


def test_pipeline_run_returns_abstain_contract_shape(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import PipelineRunRequest

    class FakeReport:
        id = "rep_demo"

    class FakeDetectionSpec:
        id = "spec_demo"
        report_id = "rep_demo"
        abstain_code = "NO_EVIDENCE"
        abstain_context = "No quote-backed behavior found"
        abstain_human_message = "Cannot generate detection"

    class FakeRecord:
        status = "abstain"
        stage = "detection_spec"
        detection_spec_id = "spec_demo"
        rule_id = None

    class FakeQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return FakeReport()

    class FakeDb:
        def query(self, *_args):
            return FakeQuery()

        def get(self, model, key):
            assert model is pipeline.DetectionSpecModel
            assert key == "spec_demo"
            return FakeDetectionSpec()

    class FakeOrchestrator:
        def __init__(self, db) -> None:
            self.db = db

        def run_report_pipeline(self, *, report_id: str, run_id: str) -> FakeRecord:
            assert report_id == "rep_demo"
            assert run_id
            return FakeRecord()

    monkeypatch.setattr(pipeline, "assert_schema_contract_current", lambda db: None)
    monkeypatch.setattr(pipeline, "PipelineOrchestrator", FakeOrchestrator)

    response = asyncio.run(
        pipeline.run_pipeline(
            PipelineRunRequest(report_id="rep_demo", profile="strict"), db=FakeDb()
        )
    )

    body = response.model_dump()
    assert body["status"] == "abstain"
    assert body["abstain"] is True
    assert body["stage"] == "detection_spec"
    assert body["abstain_code"] == "NO_EVIDENCE"


def test_pipeline_run_rejects_detection_spec_without_persisted_report(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import PipelineRunRequest
    from de_forge.services.orchestrator import PipelineTransitionError

    class FakeFailedRecord:
        status = "failed"
        stage = "report_not_found"
        detection_spec_id = None
        rule_id = None

    class FakeRunQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return FakeFailedRecord()

    class FakeDb:
        def query(self, model):
            assert model is pipeline.PipelineRunRecordModel
            return FakeRunQuery()

    class FakeOrchestrator:
        def __init__(self, db) -> None:
            self.db = db

        def run_report_pipeline(self, *, report_id: str, run_id: str):
            assert report_id == "rep_orphan"
            raise PipelineTransitionError("persisted Report required")

    monkeypatch.setattr(pipeline, "assert_schema_contract_current", lambda db: None)
    monkeypatch.setattr(pipeline, "PipelineOrchestrator", FakeOrchestrator)

    response = asyncio.run(
        pipeline.run_pipeline(
            PipelineRunRequest(report_id="rep_orphan", profile="balanced"), db=FakeDb()
        )
    )

    assert response.status_code == 404
    body = response.body.decode()
    assert "report_not_found" in body
    assert "persisted Report required" in body


def test_pipeline_run_routes_through_report_scoped_orchestrator(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import PipelineRunRequest

    captured = {}

    class FakeReport:
        id = "rep_demo"

    class FakeRecord:
        status = "ok"
        stage = "awaiting_review"
        detection_spec_id = "spec_demo"
        rule_id = "rule_demo"

    class FakeQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return FakeReport()

    class FakeDb:
        def query(self, model):
            assert model is pipeline.ReportModel
            return FakeQuery()

    class FakeOrchestrator:
        def __init__(self, db) -> None:
            captured["db"] = db

        def run_report_pipeline(self, *, report_id: str, run_id: str) -> FakeRecord:
            captured["report_id"] = report_id
            captured["run_id"] = run_id
            return FakeRecord()

        def run_pipeline(self, detection_spec_id: str):
            raise AssertionError(f"legacy detection spec path used: {detection_spec_id}")

    monkeypatch.setattr(pipeline, "assert_schema_contract_current", lambda db: None)
    monkeypatch.setattr(pipeline, "PipelineOrchestrator", FakeOrchestrator)

    response = asyncio.run(
        pipeline.run_pipeline(
            PipelineRunRequest(report_id="rep_demo", profile="balanced"), db=FakeDb()
        )
    )

    body = response.model_dump()
    assert body["status"] == "ok"
    assert body["stage"] == "awaiting_review"
    assert body["detection_spec_id"] == "spec_demo"
    assert body["rule_id"] == "rule_demo"
    assert captured["report_id"] == "rep_demo"
    assert captured["run_id"] == body["run_id"]


def test_pipeline_run_failure_preserves_persisted_record_stage(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import PipelineRunRequest
    from de_forge.services.orchestrator import PipelineTransitionError

    class FakeReport:
        id = "rep_demo"

    class FakeFailedRecord:
        status = "failed"
        stage = "evidence_required"
        detection_spec_id = None
        rule_id = None

    class FakeReportQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return FakeReport()

    class FakeRunQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return FakeFailedRecord()

    class FakeDb:
        query_count = 0

        def query(self, model):
            if model is pipeline.ReportModel:
                return FakeReportQuery()
            assert model is pipeline.PipelineRunRecordModel
            return FakeRunQuery()

    class FakeOrchestrator:
        def __init__(self, db) -> None:
            self.db = db

        def run_report_pipeline(self, *, report_id: str, run_id: str):
            raise PipelineTransitionError("evidence required before DetectionSpec generation")

    monkeypatch.setattr(pipeline, "assert_schema_contract_current", lambda db: None)
    monkeypatch.setattr(pipeline, "PipelineOrchestrator", FakeOrchestrator)

    response = asyncio.run(
        pipeline.run_pipeline(
            PipelineRunRequest(report_id="rep_demo", profile="balanced"), db=FakeDb()
        )
    )

    assert response.status_code == 400
    body = response.body.decode()
    assert "evidence_required" in body
    assert "failed" in body


def test_reports_ingest_is_idempotent_by_content_hash() -> None:
    payload = {
        "source_type": "txt",
        "content": "Credential dumping behavior\n\nLSASS access observed",
        "external_ref": "idempotent-a.txt",
        "metadata": {"title": "first"},
    }

    first = client.post("/v1/reports:ingest", json=payload)
    second = client.post(
        "/v1/reports:ingest",
        json={**payload, "external_ref": "idempotent-b.txt", "metadata": {"title": "second"}},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["report_id"] == second.json()["report_id"]
    assert first.json()["chunk_count"] == second.json()["chunk_count"] == 2


def test_reports_ingest_rejects_pdf_with_stable_unsupported_error() -> None:
    response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "pdf",
            "content": "%PDF-1.7 fake content",
            "external_ref": "report.pdf",
            "metadata": {},
        },
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "PDF ingestion is not supported"


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


def test_pipeline_approve_helper_records_run_context(monkeypatch) -> None:
    from de_forge.api.routes import pipeline

    captured = {}

    class FakeRecord:
        rule_id = "rule_demo"

    class FakeReviewService:
        def __init__(self, db) -> None:
            self.db = db

        def record_decision(self, **kwargs) -> str:
            captured.update(kwargs)
            return "review_demo"

    monkeypatch.setattr(pipeline, "_resolve_run_record", lambda db, run_id: FakeRecord())
    monkeypatch.setattr(pipeline, "ReviewService", FakeReviewService)

    response = asyncio.run(
        pipeline.approve_rule_for_export(
            rule_id="rule_demo",
            run_id="run_demo",
            reviewer="analyst@example.com",
            db=object(),
        )
    )

    assert response["decision_id"] == "review_demo"
    assert captured["rule_id"] == "rule_demo"
    assert captured["decision"] == "approved"
    assert captured["reviewer"] == "analyst@example.com"
    assert captured["run_id"] == "run_demo"
    assert captured["comments"] == "pipeline approval helper"


def test_pipeline_approve_helper_rejects_mismatched_run_rule(monkeypatch) -> None:
    from de_forge.api.routes import pipeline

    class FakeRecord:
        rule_id = "different_rule"

    monkeypatch.setattr(pipeline, "_resolve_run_record", lambda db, run_id: FakeRecord())

    response = asyncio.run(
        pipeline.approve_rule_for_export(
            rule_id="rule_demo",
            run_id="run_demo",
            db=object(),
        )
    )

    assert response.status_code == 404


def test_legacy_review_decision_forwards_db_to_create_review(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import ReviewRequest

    captured = {}

    async def fake_create_review(payload, db):
        captured["payload"] = payload
        captured["db"] = db
        return object()

    monkeypatch.setattr(pipeline, "create_review", fake_create_review)

    payload = ReviewRequest(
        run_id="run_demo",
        reviewer="analyst@example.com",
        decision="approved",
        comments="Legacy review wrapper should preserve DB session.",
    )
    fake_db = object()

    asyncio.run(pipeline.legacy_review_decision(payload, db=fake_db))

    assert captured["payload"] is payload
    assert captured["db"] is fake_db


def test_legacy_assert_export_forwards_db_to_export_sigma(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import ExportSigmaRequest

    captured = {}

    async def fake_export_sigma(payload, db):
        captured["payload"] = payload
        captured["db"] = db
        return object()

    monkeypatch.setattr(pipeline, "export_sigma", fake_export_sigma)

    payload = ExportSigmaRequest(run_id="run_demo")
    fake_db = object()

    asyncio.run(pipeline.legacy_assert_export(payload, db=fake_db))

    assert captured["payload"] is payload
    assert captured["db"] is fake_db
