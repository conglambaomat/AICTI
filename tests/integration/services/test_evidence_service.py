"""Integration tests for evidence extraction service."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import EvidenceSpan, Report, ReportChunk
from de_forge.services.evidence import EvidenceExtractionError, EvidenceInput, EvidenceService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report_and_chunk(
    db: Session,
    chunk_text: str = "powershell -enc abc",
    chunk_char_start: int = 0,
) -> tuple[str, str]:
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text=chunk_text,
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at="1970-01-01T00:00:00Z",
        updated_at="1970-01-01T00:00:00Z",
    )
    chunk = ReportChunk(
        id="chunk-1",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text=chunk_text,
        char_start=chunk_char_start,
        char_end=chunk_char_start + len(chunk_text),
        chunk_type="paragraph",
        created_at="1970-01-01T00:00:00Z",
    )
    db.add(report)
    db.add(chunk)
    db.commit()
    return report.id, chunk.id


def test_empty_evidence_payload_transitions_to_failed_generation() -> None:
    """Empty evidence payload must fail-fast and persist nothing."""
    db = _build_session()
    report_id, _ = _seed_report_and_chunk(db)
    service = EvidenceService(db)

    try:
        service.persist_evidence(report_id=report_id, run_id="run-1", created_by_agent="evidence-agent", evidence=[])
        assert False, "Expected EvidenceExtractionError for empty evidence payload"
    except EvidenceExtractionError as exc:
        assert "empty evidence" in str(exc).lower()

    persisted = db.execute(select(EvidenceSpan).where(EvidenceSpan.report_id == report_id)).scalars().all()
    assert persisted == []


def test_valid_evidence_persists_with_lineage_fields() -> None:
    """Valid evidence should persist with report_id, chunk_id, and evidence_id lineage."""
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(db)
    service = EvidenceService(db)

    result = service.persist_evidence(
        report_id=report_id,
        run_id="run-2",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-1",
                chunk_id=chunk_id,
                quote="powershell -enc abc",
                char_start=0,
                char_end=18,
                supports_claim="Encoded PowerShell command execution observed",
                confidence=0.92,
            )
        ],
    )

    assert result == ["evidence-1"]

    persisted = db.execute(select(EvidenceSpan).where(EvidenceSpan.id == "evidence-1")).scalar_one()
    assert persisted.id == "evidence-1"
    assert persisted.report_id == report_id
    assert persisted.chunk_id == chunk_id
    assert persisted.run_id == "run-2"


def test_evidence_with_nonzero_chunk_start_validates_absolute_offsets() -> None:
    """Evidence offsets are absolute and must stay within non-zero chunk bounds."""
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(db, chunk_char_start=100)
    service = EvidenceService(db)

    result = service.persist_evidence(
        report_id=report_id,
        run_id="run-3",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-2",
                chunk_id=chunk_id,
                quote="powershell -enc",
                char_start=100,
                char_end=115,
                supports_claim="PowerShell execution detected",
                confidence=0.88,
            )
        ],
    )

    assert result == ["evidence-2"]

    persisted = db.execute(select(EvidenceSpan).where(EvidenceSpan.id == "evidence-2")).scalar_one()
    assert persisted.char_start == 100
    assert persisted.char_end == 115
    assert persisted.chunk_id == chunk_id
