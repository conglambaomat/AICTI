import json
from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import DetectionSpec, ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()
    app = FastAPI()

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(pipeline_router)
    return TestClient(app), db


def _persist_validated_spec(db: Session, report_id: str, evidence_id: str) -> str:
    spec_payload = {
        "report_id": report_id,
        "behavior_rules": [
            {
                "evidence": [evidence_id],
                "attack_ids": ["T1059.001"],
                "required_telemetry": ["process_creation"],
                "detection_logic": "CommandLine contains 'powershell'",
            }
        ],
        "false_positive_hypotheses": ["administrative scripts"],
        "test_plan": "validate against process creation logs",
        "evidence_ids": [evidence_id],
        "behavior_ids": ["behavior-1"],
        "detection_strategy": "detect encoded powershell",
        "analytic": "powershell command line analytic",
        "data_component": "process creation",
        "allowed_telemetry_fields": ["CommandLine", "Image"],
        "rationale_traceability": [evidence_id],
    }
    spec = DetectionSpec(
        id="spec-e2e",
        report_id=report_id,
        spec_payload=json.dumps(spec_payload),
        is_validated=True,
    )
    db.add(spec)
    db.commit()
    return spec.id


def test_successful_sota_pipeline_ingest_run_review_export() -> None:
    client, db = _build_client()

    ingest_response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "powershell encoded command",
            "external_ref": "e2e-report.txt",
            "metadata": {},
        },
    )
    assert ingest_response.status_code == 201
    report_id = ingest_response.json()["report_id"]
    chunk = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).one()

    RetrievalAuditService(db).record_retrieval(
        run_id="run-evidence-e2e",
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
        run_id="run-evidence-e2e",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-e2e",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )
    _persist_validated_spec(db, report_id, "evidence-e2e")

    run_response = client.post("/v1/pipeline:run", json={"report_id": report_id})
    assert run_response.status_code == 200
    run_body = run_response.json()
    assert run_body["status"] == "ok"
    assert run_body["stage"] == "awaiting_review"
    assert run_body["detection_spec_id"] == "spec-e2e"
    assert run_body["rule_id"]

    review_response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_body["run_id"],
            "decision": "approved",
            "reviewer": "analyst@example.com",
            "comments": "E2E approved.",
        },
    )
    assert review_response.status_code == 201

    export_response = client.post("/v1/exports/sigma", json={"run_id": run_body["run_id"]})
    assert export_response.status_code == 200
    export_body = export_response.json()
    assert export_body["rule_id"] == run_body["rule_id"]
    assert "CommandLine|contains" in export_body["content"]
    assert "powershell" in export_body["content"]
