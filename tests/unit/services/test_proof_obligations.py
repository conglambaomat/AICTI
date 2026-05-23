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


def test_candidate_not_selectable_when_any_required_failed() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    failed = obligations.copy()
    failed[0] = failed[0].model_copy(update={"status": ProofObligationStatus.FAILED})

    with pytest.raises(ProofObligationError, match="is failed"):
        service.verify_selectable(failed)


def test_candidate_not_selectable_when_any_required_unknown() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    unknown = [
        obligation.model_copy(update={"status": ProofObligationStatus.PROVEN})
        for obligation in obligations
    ]
    unknown[0] = unknown[0].model_copy(update={"status": ProofObligationStatus.UNKNOWN})

    with pytest.raises(ProofObligationError, match="is unknown"):
        service.verify_selectable(unknown)


def test_candidate_not_selectable_when_not_applicable_without_justification() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    not_applicable = [
        obligation.model_copy(update={"status": ProofObligationStatus.PROVEN})
        for obligation in obligations
    ]
    not_applicable[0] = not_applicable[0].model_copy(
        update={"status": ProofObligationStatus.NOT_APPLICABLE, "justification": None}
    )

    with pytest.raises(ProofObligationError, match="is not_applicable"):
        service.verify_selectable(not_applicable)


def test_candidate_selectable_when_not_applicable_has_justification() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    justified = [
        obligation.model_copy(update={"status": ProofObligationStatus.PROVEN})
        for obligation in obligations
    ]
    justified[0] = justified[0].model_copy(
        update={
            "status": ProofObligationStatus.NOT_APPLICABLE,
            "justification": "No external telemetry",
        }
    )

    assert service.verify_selectable(justified) is True
