"""Evidence extraction service with fail-fast contract validation."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from de_forge.models import EvidenceSpan, ReportChunk


class EvidenceExtractionError(Exception):
    """Raised when evidence extraction fails contract validation."""

    pass


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
        """
        Persist evidence spans with strict contract validation.

        Args:
            report_id: Parent report ID for lineage
            run_id: Execution run ID for traceability
            created_by_agent: Agent name that extracted evidence
            evidence: List of evidence spans to persist

        Returns:
            List of persisted evidence IDs

        Raises:
            EvidenceExtractionError: If evidence payload is empty or violates contract
        """
        # Fail-fast: empty evidence list
        if not evidence:
            raise EvidenceExtractionError("Empty evidence payload: cannot proceed with generation")

        # Validate each evidence span before persisting
        for ev in evidence:
            self._validate_evidence_span(ev)

        # Persist all evidence spans atomically
        try:
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
                    created_at="1970-01-01T00:00:00Z",
                )
                self.db.add(span)
                evidence_ids.append(ev.evidence_id)

            self.db.commit()
            return evidence_ids

        except Exception:
            self.db.rollback()
            raise

    def _validate_evidence_span(self, ev: EvidenceInput) -> None:
        """
        Validate evidence span contract.

        Raises:
            EvidenceExtractionError: If validation fails
        """
        # Quote must be non-empty
        if not ev.quote or len(ev.quote) == 0:
            raise EvidenceExtractionError(f"Evidence {ev.evidence_id}: quote must be non-empty")

        # Support claim must be non-empty
        if not ev.supports_claim or len(ev.supports_claim) == 0:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: supports_claim must be non-empty"
            )

        # Confidence must be in [0.0, 1.0]
        if not (0.0 <= ev.confidence <= 1.0):
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: confidence must be between 0.0 and 1.0, got {ev.confidence}"
            )

        # Quote offsets must be valid
        if ev.char_start < 0:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_start must be >= 0, got {ev.char_start}"
            )

        if ev.char_end < ev.char_start:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_end must be >= char_start, got char_start={ev.char_start}, char_end={ev.char_end}"
            )

        # Verify chunk exists and offsets are within chunk bounds (absolute coordinates)
        chunk = self.db.get(ReportChunk, ev.chunk_id)
        if not chunk:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: chunk_id {ev.chunk_id} not found"
            )

        # Evidence offsets are absolute (same coordinate space as chunk offsets)
        if ev.char_start < chunk.char_start:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_start {ev.char_start} is before chunk start {chunk.char_start}"
            )

        if ev.char_end > chunk.char_end:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: char_end {ev.char_end} exceeds chunk end {chunk.char_end}"
            )
