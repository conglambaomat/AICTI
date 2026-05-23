"""Pure gate predicates for orchestration decisions."""

from collections.abc import Mapping

from de_forge.schemas.proof_obligation import ProofObligation, ProofObligationStatus

REQUIRED_LINEAGE_FIELDS: tuple[str, ...] = (
    "report_id",
    "trace_id",
    "run_id",
    "agent_run_id",
)


def can_generate_rule(detection_spec_verified: bool | str) -> bool:
    if isinstance(detection_spec_verified, str):
        return detection_spec_verified == "validated"
    return detection_spec_verified


def can_enter_final_review(static_valid: bool, proof_obligations: list[ProofObligation]) -> bool:
    if not static_valid:
        return False
    return all(
        obligation.status == ProofObligationStatus.PROVEN for obligation in proof_obligations
    )


def has_required_lineage_fields(lineage: Mapping[str, str]) -> bool:
    for field in REQUIRED_LINEAGE_FIELDS:
        value = lineage.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    return True
