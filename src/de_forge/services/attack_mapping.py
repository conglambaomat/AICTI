"""ATT&CK mapping service with structured abstain."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from de_forge.models import AttackMapping
from de_forge.schemas.abstain import AbstainDecision


class AttackMappingError(Exception):
    """Raised when ATT&CK mapping fails contract validation."""

    pass


# MVP allowlist from CLAUDE.md
ATTACK_ALLOWLIST = {"T1059.001", "T1059.003", "T1105"}

# ATT&CK ID format: T followed by 4 digits, optionally followed by .3 digits
ATTACK_ID_PATTERN = re.compile(r"^T\d{4}(\.\d{3})?$")


@dataclass(frozen=True)
class AttackMappingInput:
    """Input contract for a single ATT&CK mapping."""

    mapping_id: str
    evidence_id: str
    technique_id: str
    confidence: float


class AttackMappingService:
    """Service for validating and persisting ATT&CK mappings with fail-fast semantics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def persist_mappings(
        self,
        report_id: str,
        mappings: list[AttackMappingInput],
    ) -> list[str]:
        """
        Persist ATT&CK mappings with strict contract validation.

        Args:
            report_id: Parent report ID for lineage
            mappings: List of ATT&CK mappings to persist

        Returns:
            List of persisted mapping IDs

        Raises:
            AttackMappingError: If mappings violate contract
        """
        # Validate each mapping before persisting
        for mapping in mappings:
            self._validate_mapping(mapping)

        # Persist all mappings atomically
        try:
            mapping_ids = []
            for mapping in mappings:
                attack_mapping = AttackMapping(
                    id=mapping.mapping_id,
                    report_id=report_id,
                    evidence_id=mapping.evidence_id,
                )
                self.db.add(attack_mapping)
                mapping_ids.append(mapping.mapping_id)

            self.db.commit()
            return mapping_ids

        except Exception:
            self.db.rollback()
            raise

    def _validate_mapping(self, mapping: AttackMappingInput) -> None:
        """
        Validate ATT&CK mapping contract.

        Raises:
            AttackMappingError: If validation fails
        """
        # Validate ATT&CK ID format
        if not ATTACK_ID_PATTERN.match(mapping.technique_id):
            raise AttackMappingError(
                f"Mapping {mapping.mapping_id}: technique_id must match format T####(.###), got {mapping.technique_id}"
            )

        # Validate against MVP allowlist
        if mapping.technique_id not in ATTACK_ALLOWLIST:
            raise AttackMappingError(
                f"Mapping {mapping.mapping_id}: technique_id {mapping.technique_id} not in MVP allowlist {ATTACK_ALLOWLIST}"
            )

        # Validate confidence bounds
        if not (0.0 <= mapping.confidence <= 1.0):
            raise AttackMappingError(
                f"Mapping {mapping.mapping_id}: confidence must be between 0.0 and 1.0, got {mapping.confidence}"
            )

    def abstain_for_insufficient_evidence(
        self,
        report_id: str,
        evidence_count: int,
    ) -> AbstainDecision:
        """
        Create structured abstain decision for insufficient evidence.

        Args:
            report_id: Report ID for context
            evidence_count: Number of evidence spans found

        Returns:
            Structured abstain decision
        """
        return AbstainDecision(
            abstain_code="NO_EVIDENCE_BACKED_BEHAVIOR",
            abstain_context=f"report_id={report_id}, evidence_count={evidence_count}",
            human_message=f"Insufficient evidence to generate ATT&CK mappings. Found {evidence_count} evidence spans for report {report_id}.",
        )
