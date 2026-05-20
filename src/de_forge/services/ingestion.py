"""Report ingestion service."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.core.idempotency import make_idempotency_key
from de_forge.models import Report, ReportChunk


@dataclass(frozen=True)
class IngestionChunk:
    """Chunk metadata returned by ingestion."""

    chunk_id: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class IngestionResult:
    """Result payload returned by ingestion."""

    report_id: str
    chunks: list[IngestionChunk]


class IngestionService:
    """Service for ingesting report content and persisting deterministic chunks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest(self, source_type: str, filename: str, content_bytes: bytes) -> IngestionResult:
        """Ingest report bytes and persist report with deterministic chunks."""
        try:
            raw_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("content_bytes must be valid UTF-8") from exc
        content_hash = sha256(content_bytes).hexdigest()

        # Idempotency policy: reports are deduplicated by content_hash only.
        # Same content with different filename/source_type returns the existing report.
        existing_report = self.db.execute(
            select(Report).where(Report.content_hash == content_hash)
        ).scalar_one_or_none()

        if existing_report:
            # Return existing report and its chunks
            existing_chunks = self.db.execute(
                select(ReportChunk)
                .where(ReportChunk.report_id == existing_report.id)
                .order_by(ReportChunk.chunk_index)
            ).scalars().all()

            return IngestionResult(
                report_id=existing_report.id,
                chunks=[
                    IngestionChunk(
                        chunk_id=chunk.id,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                    )
                    for chunk in existing_chunks
                ],
            )

        report = Report(
            id=make_idempotency_key("report", {"source_type": source_type, "filename": filename, "content_hash": content_hash}),
            source_type=source_type,
            source_uri=filename,
            title=filename,
            raw_text=raw_text,
            content_hash=content_hash,
            metadata_json="{}",
            status="ingested",
            created_at="1970-01-01T00:00:00Z",
            updated_at="1970-01-01T00:00:00Z",
        )

        chunks = self._build_chunks(report_id=report.id, text=raw_text)

        try:
            self.db.add(report)
            for idx, chunk in enumerate(chunks):
                self.db.add(
                    ReportChunk(
                        id=chunk.chunk_id,
                        report_id=report.id,
                        chunk_index=idx,
                        section_title=None,
                        chunk_text=raw_text[chunk.char_start:chunk.char_end],
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                        chunk_type="paragraph",
                        created_at="1970-01-01T00:00:00Z",
                    )
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return IngestionResult(report_id=report.id, chunks=chunks)

    def _build_chunks(self, report_id: str, text: str) -> list[IngestionChunk]:
        parts = text.split("\n\n")
        chunks: list[IngestionChunk] = []
        cursor = 0

        for index, part in enumerate(parts):
            start = text.find(part, cursor)
            end = start + len(part)
            cursor = end + 2
            chunk_id = make_idempotency_key(
                "chunk",
                {
                    "report_id": report_id,
                    "chunk_index": index,
                    "chunk_text": part,
                    "char_start": start,
                    "char_end": end,
                },
            )
            chunks.append(IngestionChunk(chunk_id=chunk_id, char_start=start, char_end=end))

        return chunks
