from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from de_forge.api.router import api_router
from de_forge.api.routes.ingestion import router as ingestion_router
from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.api.routes.review import router as review_router
from de_forge.db.session import get_db
from de_forge.main import health
from de_forge.models import ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService
from tests.integration.e2e.test_sota_pipeline_e2e import _build_client, _persist_validated_spec


def _build_runtime_client() -> tuple[TestClient, Session]:
    _pipeline_client, db = _build_client()
    app = FastAPI()

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(pipeline_router)
    app.include_router(ingestion_router)
    app.include_router(review_router)
    app.include_router(api_router)
    app.add_api_route("/health", health, methods=["GET"])
    return TestClient(app), db


def test_runtime_apis_reflect_completed_pipeline_state() -> None:
    client, db = _build_runtime_client()
    ingest_response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "powershell encoded command",
            "external_ref": "runtime-e2e-report.txt",
            "metadata": {},
        },
    )
    report_id = ingest_response.json()["report_id"]
    chunk = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).one()
    RetrievalAuditService(db).record_retrieval(
        run_id="run-runtime-evidence",
        report_id=report_id,
        query_text="powershell encoded command",
        retrieval_mode="hybrid_rrf_stub",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id=chunk.id,
                text=chunk.chunk_text,
                score_sparse=1.0,
                score_dense=1.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-runtime-evidence",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-runtime-e2e",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )
    _persist_validated_spec(db, report_id, "evidence-runtime-e2e")

    run_body = client.post("/v1/pipeline:run", json={"report_id": report_id}).json()
    run_id = run_body["run_id"]

    runs = client.get("/api/runs").json()
    assert any(item["run_id"] == run_id for item in runs["items"])

    run_detail = client.get(f"/api/runs/{run_id}").json()
    assert run_detail["stage"] == "awaiting_review"
    assert run_detail["rule_id"] == run_body["rule_id"]

    validation = client.get(f"/api/runs/{run_id}/validation").json()
    assert validation["items"]
    assert validation["items"][0]["status"] == "passed"

    ops = client.get("/api/metrics/ops").json()
    assert ops["total_runs"] == 1
    assert ops["run_counts"] == {"ok": 1}

    quality = client.get("/api/metrics/quality").json()
    assert quality["overall_quality"] is not None

    dashboard = client.get("/api/dashboard/summary").json()
    assert dashboard["queue"]["total_runs"] == 1

    health_response = client.get("/health")
    assert health_response.status_code == 200
    health_body = health_response.json()
    assert "checks" in health_body
    assert "policy" in health_body
