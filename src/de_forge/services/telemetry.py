"""Telemetry grounding service with registry-backed field enforcement."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from de_forge.models import TelemetrySelection
from de_forge.schemas.abstain import AbstainDecision
from de_forge.services.telemetry_registry import (
    is_supported_telemetry_type,
    validate_required_fields,
)


class TelemetryFieldValidationError(Exception):
    """Raised when telemetry grounding violates registry constraints."""

    pass


@dataclass(frozen=True)
class TelemetryGroundingInput:
    """Input contract for telemetry grounding selection."""

    selection_id: str
    attack_mapping_id: str
    telemetry_type: str
    required_fields: list[str]


class TelemetryGroundingService:
    """Service for telemetry grounding with strict allowlist enforcement."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def persist_selections(
        self,
        report_id: str,
        selections: list[TelemetryGroundingInput],
    ) -> list[str]:
        """Persist telemetry selections atomically after registry validation."""
        for selection in selections:
            self._validate_selection(selection)

        try:
            selection_ids: list[str] = []
            for selection in selections:
                row = TelemetrySelection(
                    id=selection.selection_id,
                    report_id=report_id,
                    attack_mapping_id=selection.attack_mapping_id,
                )
                self.db.add(row)
                selection_ids.append(selection.selection_id)

            self.db.commit()
            return selection_ids
        except Exception:
            self.db.rollback()
            raise

    def _validate_selection(self, selection: TelemetryGroundingInput) -> None:
        """Validate telemetry type and required fields against registry."""
        if not is_supported_telemetry_type(selection.telemetry_type):
            raise TelemetryFieldValidationError(
                f"Selection {selection.selection_id}: telemetry_type {selection.telemetry_type} is not supported in MVP"
            )

        disallowed_fields = validate_required_fields(
            selection.telemetry_type,
            selection.required_fields,
        )
        if disallowed_fields:
            raise TelemetryFieldValidationError(
                f"Selection {selection.selection_id}: fields {disallowed_fields} are not allowed for {selection.telemetry_type}"
            )

    def abstain_for_no_supported_telemetry(
        self,
        report_id: str,
        attack_mapping_id: str,
        requested_telemetry_types: list[str],
    ) -> AbstainDecision:
        """Build deterministic NO_TELEMETRY abstain decision."""
        requested = ",".join(requested_telemetry_types) if requested_telemetry_types else "none"
        return AbstainDecision(
            abstain_code="NO_TELEMETRY",
            abstain_context=(
                f"report_id={report_id}, attack_mapping_id={attack_mapping_id}, "
                f"requested_telemetry_types={requested}"
            ),
            human_message=(
                "No supported telemetry available for detection grounding in MVP "
                f"for attack mapping {attack_mapping_id}."
            ),
        )
