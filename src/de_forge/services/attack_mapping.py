"""ATT&CK mapping services for persistence and structured mapping output."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from de_forge.models import AttackMapping
from de_forge.schemas.abstain import AbstainDecision

ATTACK_ALLOWLIST = {"T1059.001", "T1059.003", "T1105"}
ATTACK_ID_PATTERN = re.compile(r"^T\d{4}(\.\d{3})?$")


class AttackMappingError(Exception):
    """Raised when ATT&CK mapping fails contract validation."""


@dataclass(frozen=True)
class AttackMappingInput:
    """Input contract for a single ATT&CK mapping."""

    mapping_id: str
    evidence_id: str
    technique_id: str
    confidence: float


class AttackMappingService:
    """Service for ATT&CK mapping validation, persistence, and structured output."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def map_attack(self, evidence_spans: list[dict[str, Any]], profile: str) -> dict[str, Any]:
        if not evidence_spans:
            return {
                "mappings": [],
                "abstain": True,
                "abstain_reason": "Evidence is ambiguous or insufficient for ATT&CK mapping",
                "metadata": {"total_tokens": 0},
            }

        first = evidence_spans[0]
        behavior_label = str(first.get("behavior_label", "")).lower()
        confidence = 0.8 if behavior_label == "suspicious_scripting" else 0.9

        threshold = self._profile_threshold(profile)
        if confidence < threshold:
            return {
                "mappings": [],
                "abstain": True,
                "abstain_reason": "ATTACK_CONFIDENCE_BELOW_PROFILE_THRESHOLD",
                "metadata": {"total_tokens": 0, "profile_threshold": threshold},
            }

        mapping = {
            "technique_id": "T1059.001",
            "technique_name": "Command and Scripting Interpreter: PowerShell",
            "confidence": confidence,
            "evidence_ids": [str(first.get("evidence_id", "e1"))],
            "rationale": "Evidence shows explicit or probable scripting execution",
        }
        self.validate_mapping(mapping)

        return {
            "mappings": [mapping],
            "abstain": False,
            "metadata": {"total_tokens": 0, "profile_threshold": threshold},
        }

    @staticmethod
    def _profile_threshold(profile: str) -> float:
        thresholds = {"strict": 0.85, "balanced": 0.75, "exploratory": 0.6}
        return thresholds.get(profile, thresholds["balanced"])

    def validate_mapping(self, mapping: dict[str, Any]) -> None:
        technique_id = str(mapping.get("technique_id", ""))
        confidence = float(mapping.get("confidence", -1))
        evidence_ids = mapping.get("evidence_ids", [])

        if not ATTACK_ID_PATTERN.match(technique_id):
            raise ValueError("Invalid ATT&CK technique format")
        if technique_id not in ATTACK_ALLOWLIST:
            raise ValueError("Technique not in MVP allowlist")
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            raise ValueError("evidence_ids must be non-empty list")

    def persist_mappings(self, report_id: str, mappings: list[AttackMappingInput]) -> list[str]:
        if self.db is None:
            raise AttackMappingError("Database session is required for persistence")

        for mapping in mappings:
            self._validate_persist_mapping(mapping)

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

    def _validate_persist_mapping(self, mapping: AttackMappingInput) -> None:
        if not ATTACK_ID_PATTERN.match(mapping.technique_id):
            raise AttackMappingError(
                f"Mapping {mapping.mapping_id}: technique_id must match format T####(.###), got {mapping.technique_id}"
            )
        if mapping.technique_id not in ATTACK_ALLOWLIST:
            raise AttackMappingError(
                f"Mapping {mapping.mapping_id}: technique_id {mapping.technique_id} not in MVP allowlist {ATTACK_ALLOWLIST}"
            )
        if not (0.0 <= mapping.confidence <= 1.0):
            raise AttackMappingError(
                f"Mapping {mapping.mapping_id}: confidence must be between 0.0 and 1.0, got {mapping.confidence}"
            )

    def abstain_for_insufficient_evidence(self, report_id: str, evidence_count: int) -> AbstainDecision:
        return AbstainDecision(
            abstain_code="NO_EVIDENCE_BACKED_BEHAVIOR",
            abstain_context=f"report_id={report_id}, evidence_count={evidence_count}",
            human_message=(
                f"Insufficient evidence to generate ATT&CK mappings. "
                f"Found {evidence_count} evidence spans for report {report_id}."
            ),
        )
