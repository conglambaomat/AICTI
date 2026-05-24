"""Evidence services for fail-fast persistence and retrieval-grounded extraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from de_forge.models import EvidenceSpan, ReportChunk
from de_forge.services.citation_verifier import verify_citation


class EvidenceExtractionError(Exception):
    """Raised when evidence extraction fails contract validation."""


@dataclass(frozen=True)
class EvidenceInput:
    """Input contract for a single evidence span."""

    evidence_id: str
    chunk_id: str
    quote: str
    char_start: int
    char_end: int
    supports_claim: str
    confidence: float


class EvidenceService:
    """Service for validating and persisting evidence spans with fail-fast semantics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def persist_evidence(
        self,
        report_id: str,
        run_id: str,
        created_by_agent: str,
        evidence: list[EvidenceInput],
    ) -> list[str]:
        if not evidence:
            raise EvidenceExtractionError("Empty evidence payload: cannot proceed with generation")

        for ev in evidence:
            self._validate_evidence_span(ev)

        try:
            created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            evidence_ids = []
            for ev in evidence:
                span = EvidenceSpan(
                    id=ev.evidence_id,
                    report_id=report_id,
                    chunk_id=ev.chunk_id,
                    quote=ev.quote,
                    char_start=ev.char_start,
                    char_end=ev.char_end,
                    supports_claim=ev.supports_claim,
                    confidence=ev.confidence,
                    created_by_agent=created_by_agent,
                    run_id=run_id,
                    created_at=created_at,
                )
                self.db.add(span)
                evidence_ids.append(ev.evidence_id)

            self.db.commit()
            return evidence_ids
        except Exception:
            self.db.rollback()
            raise

    def _validate_evidence_span(self, ev: EvidenceInput) -> None:
        if not ev.quote:
            raise EvidenceExtractionError(f"Evidence {ev.evidence_id}: quote must be non-empty")
        if not ev.supports_claim:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: supports_claim must be non-empty"
            )
        if not (0.0 <= ev.confidence <= 1.0):
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: confidence must be between 0.0 and 1.0, got {ev.confidence}"
            )
        if ev.char_start < 0:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_start must be >= 0, got {ev.char_start}"
            )
        if ev.char_end < ev.char_start:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_end must be >= char_start, got char_start={ev.char_start}, char_end={ev.char_end}"
            )

        chunk = self.db.get(ReportChunk, ev.chunk_id)
        if not chunk:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: chunk_id {ev.chunk_id} not found"
            )
        if ev.char_start < chunk.char_start:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_start {ev.char_start} is before chunk start {chunk.char_start}"
            )
        if ev.char_end > chunk.char_end:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_end {ev.char_end} exceeds chunk end {chunk.char_end}"
            )

        relative_start = ev.char_start - chunk.char_start
        relative_end = ev.char_end - chunk.char_start
        try:
            quote_matches = verify_citation(
                chunk.chunk_text, ev.quote, relative_start, relative_end
            )
        except ValueError as exc:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: invalid citation offsets for chunk {ev.chunk_id}"
            ) from exc
        if not quote_matches:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: quote does not match chunk text at char_start={ev.char_start}, char_end={ev.char_end}"
            )


@dataclass(slots=True)
class EvidenceAgentService:
    """Evidence extraction service using retrieval grounding and structured LLM output."""

    retrieval_service: Any
    llm_client: Any

    def extract(self, *, report_id: str, report_text: str) -> dict[str, Any]:
        query_plan = {"query": report_text}
        chunks = self.retrieval_service.retrieve(query_plan["query"], report_id)

        llm_output = self.llm_client.generate_structured(
            schema_name="evidence_output",
            payload={"report_id": report_id, "report_text": report_text, "chunks": chunks},
        )

        evidence = llm_output.get("evidence", [])
        grounded: list[dict[str, Any]] = []
        chunk_map = {chunk["chunk_id"]: chunk["text"] for chunk in chunks}

        for item in evidence:
            chunk_id = item.get("chunk_id")
            quote = item.get("quote")
            start_offset = item.get("start_offset")
            end_offset = item.get("end_offset")
            if not isinstance(chunk_id, str) or not isinstance(quote, str):
                continue
            if not isinstance(start_offset, int) or not isinstance(end_offset, int):
                continue
            chunk_text = chunk_map.get(chunk_id)
            if not isinstance(chunk_text, str):
                continue
            if start_offset < 0 or end_offset > len(chunk_text) or start_offset >= end_offset:
                continue
            if chunk_text[start_offset:end_offset] != quote:
                continue
            grounded.append(item)

        if not grounded:
            return {
                "status": "abstain",
                "abstain_code": "NO_EVIDENCE_BACKED_BEHAVIOR",
                "query_plan": query_plan,
                "evidence": [],
            }

        return {"status": "ok", "query_plan": query_plan, "evidence": grounded}
