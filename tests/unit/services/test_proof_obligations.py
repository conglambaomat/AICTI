import pytest

from de_forge.core.errors import ProofObligationError
from de_forge.schemas.proof_obligation import ProofObligationStatus, ProofObligationType
from de_forge.services.proof_obligation_service import ProofObligationService


def test_required_proof_obligations_are_generated() -> None:
    service = ProofObligationService()

    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")

    obligation_types = {obligation.claim_type for obligation in obligations}
    assert ProofObligationType.DETECTS_REPORT_BEHAVIOR in obligation_types
    assert ProofObligationType.NOT_OVERBROAD in obligation_types
    assert ProofObligationType.TELEMETRY_FIELDS_EXIST in obligation_types
    assert ProofObligationType.CITATION_FAITHFUL in obligation_types


def test_candidate_not_selectable_when_unproven() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")

    with pytest.raises(ProofObligationError):
        service.verify_selectable(obligations)


def test_candidate_selectable_when_all_required_are_proven() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    proven = [
        obligation.model_copy(update={"status": ProofObligationStatus.PROVEN})
        for obligation in obligations
    ]

    assert service.verify_selectable(proven) is True
