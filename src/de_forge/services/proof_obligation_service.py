from __future__ import annotations

from de_forge.core.errors import ProofObligationError
from de_forge.schemas.proof_obligation import (
    ProofObligation,
    ProofObligationStatus,
    ProofObligationType,
)


class ProofObligationService:
    def generate_required(self, rule_candidate_id: str, run_id: str) -> list[ProofObligation]:
        return [
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.DETECTS_REPORT_BEHAVIOR,
                claim_text="Rule detects report behavior.",
                required_artifact_types=["evidence_quote"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.NOT_OVERBROAD,
                claim_text="Rule is not overbroad.",
                required_artifact_types=["false_positive_analysis"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.TELEMETRY_FIELDS_EXIST,
                claim_text="Telemetry fields exist.",
                required_artifact_types=["telemetry_registry_check"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.CITATION_FAITHFUL,
                claim_text="Citations are faithful.",
                required_artifact_types=["citation_verification"],
            ),
        ]

    def verify_selectable(self, obligations: list[ProofObligation]) -> bool:
        for obligation in obligations:
            if obligation.status == ProofObligationStatus.PROVEN:
                continue
            if (
                obligation.status == ProofObligationStatus.NOT_APPLICABLE
                and obligation.justification
            ):
                continue
            raise ProofObligationError(
                f"proof obligation {obligation.claim_type.value} is {obligation.status.value}"
            )
        return True
