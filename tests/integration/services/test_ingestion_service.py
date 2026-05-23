"""Integration tests for ingestion service."""

from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import Report, ReportChunk
from de_forge.services.ingestion import IngestionService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_ingest_txt_persists_report_and_chunks_in_one_transaction() -> None:
    """TXT ingestion should persist report and chunks atomically."""
    db = _build_session()
    service = IngestionService(db)

    content = "alpha line\n\n beta line\n\n gamma line"
    result = service.ingest(
        source_type="txt", filename="sample.txt", content_bytes=content.encode("utf-8")
    )

    reports = db.execute(select(Report)).scalars().all()
    chunks = (
        db.execute(select(ReportChunk).where(ReportChunk.report_id == result.report_id))
        .scalars()
        .all()
    )

    assert len(reports) == 1
    assert len(chunks) == len(result.chunks)
    assert len(chunks) > 0

    report = reports[0]
    report_created = datetime.fromisoformat(report.created_at.replace("Z", "+00:00"))
    report_updated = datetime.fromisoformat(report.updated_at.replace("Z", "+00:00"))
    assert report_created.year >= 2025
    assert report_updated.year >= 2025
    assert report_created.tzinfo == UTC
    assert report_updated.tzinfo == UTC

    for chunk in chunks:
        chunk_created = datetime.fromisoformat(chunk.created_at.replace("Z", "+00:00"))
        assert chunk_created.year >= 2025
        assert chunk_created.tzinfo == UTC
        assert chunk.created_at != "1970-01-01T00:00:00Z"

    assert report.created_at != "1970-01-01T00:00:00Z"
    assert report.updated_at != "1970-01-01T00:00:00Z"


def test_chunking_is_deterministic_for_same_input() -> None:
    """Chunking IDs and offsets must be stable for same content."""
    db = _build_session()
    service = IngestionService(db)

    payload = b"one\n\ntwo\n\nthree"

    first = service.ingest(source_type="txt", filename="a.txt", content_bytes=payload)
    second = service.ingest(source_type="txt", filename="b.txt", content_bytes=payload)

    first_sig = [(chunk.chunk_id, chunk.char_start, chunk.char_end) for chunk in first.chunks]
    second_sig = [(chunk.chunk_id, chunk.char_start, chunk.char_end) for chunk in second.chunks]

    assert first_sig == second_sig
