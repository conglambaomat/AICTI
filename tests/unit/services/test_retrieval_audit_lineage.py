import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.db.base import Base
from de_forge.models import (
    EvidenceRetrievalLink,
    Report,
    ReportChunk,
    RetrievalAuditRun,
    RetrievalCandidate,
)
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval_audit import RetrievalAuditService


def _build_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report_chunk_and_evidence(db: Session) -> tuple[str, str, str]:
    now = "2026-05-27T00:00:00+00:00"
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri="memory://report-1",
        title="Lineage report",
        raw_text="first behavior",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    chunk = ReportChunk(
        id="chunk-1",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="first behavior",
        char_start=0,
        char_end=14,
        chunk_type="paragraph",
        created_at=now,
    )
    db.add_all([report, chunk])
    db.commit()
    EvidenceService(db).persist_evidence(
        report_id=report.id,
        run_id="run-1",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-1",
                chunk_id=chunk.id,
                quote="first behavior",
                char_start=0,
                char_end=14,
                supports_claim="First behavior observed",
                confidence=0.9,
            )
        ],
    )
    return report.id, chunk.id, "evidence-1"


def _add_retrieval_run(
    db: Session,
    *,
    retrieval_run_id: str,
    report_id: str,
    chunk_id: str,
    score_fused: float = 0.5,
) -> str:
    now = "2026-05-27T00:00:00+00:00"
    db.add(
        RetrievalAuditRun(
            id=retrieval_run_id,
            run_id="run-1",
            report_id=report_id,
            query_text=f"query {retrieval_run_id}",
            query_hash=f"hash-{retrieval_run_id}",
            retrieval_mode="hybrid_rrf",
            top_k=1,
            created_at=now,
        )
    )
    db.add(
        RetrievalCandidate(
            id=f"candidate-{retrieval_run_id}",
            retrieval_run_id=retrieval_run_id,
            run_id="run-1",
            report_id=report_id,
            chunk_id=chunk_id,
            rank=1,
            score_sparse=0.0,
            score_dense=0.0,
            score_fused=score_fused,
            selected=True,
            created_at=now,
        )
    )
    db.commit()
    return f"candidate-{retrieval_run_id}"


def test_duplicate_chunk_candidates_require_explicit_evidence_link() -> None:
    db = _build_session()
    report_id, chunk_id, _evidence_id = _seed_report_chunk_and_evidence(db)
    _add_retrieval_run(db, retrieval_run_id="retrieval-1", report_id=report_id, chunk_id=chunk_id)
    _add_retrieval_run(db, retrieval_run_id="retrieval-2", report_id=report_id, chunk_id=chunk_id)

    with pytest.raises(ValueError, match="ambiguous retrieval audit lineage"):
        RetrievalAuditService(db).get_run_evidence_lineage("run-1")


def test_explicit_evidence_retrieval_link_disambiguates_duplicate_chunk_candidates() -> None:
    db = _build_session()
    report_id, chunk_id, evidence_id = _seed_report_chunk_and_evidence(db)
    _add_retrieval_run(
        db,
        retrieval_run_id="retrieval-1",
        report_id=report_id,
        chunk_id=chunk_id,
        score_fused=0.25,
    )
    linked_candidate_id = _add_retrieval_run(
        db,
        retrieval_run_id="retrieval-2",
        report_id=report_id,
        chunk_id=chunk_id,
        score_fused=0.75,
    )
    db.add(
        EvidenceRetrievalLink(
            id="link-evidence-candidate",
            run_id="run-1",
            evidence_id=evidence_id,
            retrieval_candidate_id=linked_candidate_id,
            created_at="2026-05-27T00:00:00+00:00",
        )
    )
    db.commit()

    lineage = RetrievalAuditService(db).get_run_evidence_lineage("run-1")

    assert lineage["items"][0]["retrieval_score_fused"] == 0.75
    assert lineage["items"][0]["retrieval_rank"] == 1


def test_inconsistent_evidence_retrieval_link_fails_closed() -> None:
    db = _build_session()
    report_id, chunk_id, evidence_id = _seed_report_chunk_and_evidence(db)
    _add_retrieval_run(db, retrieval_run_id="retrieval-1", report_id=report_id, chunk_id=chunk_id)
    db.add(
        EvidenceRetrievalLink(
            id="link-evidence-missing-candidate",
            run_id="run-1",
            evidence_id=evidence_id,
            retrieval_candidate_id="missing-candidate",
            created_at="2026-05-27T00:00:00+00:00",
        )
    )
    db.commit()

    with pytest.raises(ValueError, match="ambiguous retrieval audit lineage"):
        RetrievalAuditService(db).get_run_evidence_lineage("run-1")
