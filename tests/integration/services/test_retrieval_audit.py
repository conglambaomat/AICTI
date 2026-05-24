"""Integration tests for retrieval audit lineage persistence."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.db.base import Base
from de_forge.models import Report, ReportChunk, RetrievalAuditRun, RetrievalCandidate
from de_forge.services.retrieval import ScoredChunk
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


def test_record_retrieval_persists_run_and_ranked_candidates() -> None:
    db = _build_session()
    now = "2026-05-24T00:00:00+00:00"
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri="memory://report-1",
        title="Test report",
        raw_text="alpha beta gamma delta",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    chunk_one = ReportChunk(
        id="chunk-1",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="alpha beta",
        char_start=0,
        char_end=10,
        chunk_type="paragraph",
        created_at=now,
    )
    chunk_two = ReportChunk(
        id="chunk-2",
        report_id=report.id,
        chunk_index=1,
        section_title=None,
        chunk_text="gamma delta",
        char_start=11,
        char_end=22,
        chunk_type="paragraph",
        created_at=now,
    )
    db.add_all([report, chunk_one, chunk_two])
    db.commit()

    audit_run = RetrievalAuditService(db).record_retrieval(
        run_id="run-1",
        report_id=report.id,
        query_text="find alpha behavior",
        retrieval_mode="hybrid_rrf",
        top_k=2,
        candidates=[
            ScoredChunk(
                chunk_id=chunk_one.id,
                text=chunk_one.chunk_text,
                score_sparse=1.5,
                score_dense=0.75,
                score_fused=0.42,
            ),
            ScoredChunk(
                chunk_id=chunk_two.id,
                text=chunk_two.chunk_text,
                score_sparse=0.5,
                score_dense=0.25,
                score_fused=0.21,
            ),
        ],
    )

    persisted_run = db.execute(select(RetrievalAuditRun)).scalar_one()
    assert audit_run.id == persisted_run.id
    assert persisted_run.run_id == "run-1"
    assert persisted_run.report_id == report.id
    assert persisted_run.query_text == "find alpha behavior"
    assert len(persisted_run.query_hash) == 64
    assert persisted_run.retrieval_mode == "hybrid_rrf"
    assert persisted_run.top_k == 2

    persisted_candidates = (
        db.execute(select(RetrievalCandidate).order_by(RetrievalCandidate.rank))
        .scalars()
        .all()
    )
    assert len(persisted_candidates) == 2
    assert [candidate.retrieval_run_id for candidate in persisted_candidates] == [
        persisted_run.id,
        persisted_run.id,
    ]
    assert [candidate.run_id for candidate in persisted_candidates] == ["run-1", "run-1"]
    assert [candidate.report_id for candidate in persisted_candidates] == [report.id, report.id]
    assert [candidate.chunk_id for candidate in persisted_candidates] == [chunk_one.id, chunk_two.id]
    assert [candidate.rank for candidate in persisted_candidates] == [1, 2]
    assert [candidate.score_sparse for candidate in persisted_candidates] == [1.5, 0.5]
    assert [candidate.score_dense for candidate in persisted_candidates] == [0.75, 0.25]
    assert [candidate.score_fused for candidate in persisted_candidates] == [0.42, 0.21]
    assert [candidate.selected for candidate in persisted_candidates] == [True, True]
