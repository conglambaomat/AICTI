"""Integration tests for run evidence lineage API."""

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.runs import router as runs_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import Report, ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()

    app = FastAPI()
    app.include_router(runs_router)

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), db


def _seed_report_and_chunk(db: Session) -> None:
    now = "2026-05-24T00:00:00+00:00"
    report = Report(
        id="report-api",
        source_type="txt",
        source_uri="memory://report-api",
        title="API report",
        raw_text="api behavior",
        content_hash="hash-api",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    chunk = ReportChunk(
        id="chunk-api",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="api behavior",
        char_start=0,
        char_end=12,
        chunk_type="paragraph",
        created_at=now,
    )
    db.add_all([report, chunk])
    db.commit()


def test_run_evidence_returns_persisted_lineage_json() -> None:
    client, db = _build_client()
    _seed_report_and_chunk(db)
    RetrievalAuditService(db).record_retrieval(
        run_id="run-api",
        report_id="report-api",
        query_text="api behavior",
        retrieval_mode="hybrid_rrf",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id="chunk-api",
                text="api behavior",
                score_sparse=0.0,
                score_dense=0.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id="report-api",
        run_id="run-api",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-api",
                chunk_id="chunk-api",
                quote="api behavior",
                char_start=0,
                char_end=12,
                supports_claim="API behavior observed",
                confidence=0.9,
            )
        ],
    )

    response = client.get("/runs/run-api/evidence")

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "run-api",
        "items": [
            {
                "evidence_id": "evidence-api",
                "report_id": "report-api",
                "chunk_id": "chunk-api",
                "quote": "api behavior",
                "char_start": 0,
                "char_end": 12,
                "retrieval_rank": 1,
                "retrieval_score_fused": 0.03,
                "lineage": {
                    "report_id": "report-api",
                    "chunk_id": "chunk-api",
                    "evidence_id": "evidence-api",
                },
            }
        ],
    }


def test_run_evidence_returns_empty_items_for_missing_run() -> None:
    client, _db = _build_client()

    response = client.get("/runs/missing-run/evidence")

    assert response.status_code == 200
    assert response.json() == {"run_id": "missing-run", "items": []}
