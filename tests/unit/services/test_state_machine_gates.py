import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.proof_obligation import (
    ProofObligation,
    ProofObligationStatus,
    ProofObligationType,
)
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.gates import can_enter_final_review, can_generate_rule
from de_forge.services.state_machine import StateMachine


def test_state_machine_allows_ingestion_to_evidence_transition() -> None:
    machine = StateMachine()

    assert machine.transition(RunState.INGESTED, RunState.EVIDENCE_READY) == RunState.EVIDENCE_READY


def test_state_machine_rejects_raw_report_to_rule_candidate_transition() -> None:
    machine = StateMachine()

    with pytest.raises(ValidationGateError):
        machine.transition(RunState.INGESTED, RunState.RULE_CANDIDATES_READY)


def test_run_mode_values_include_auto_and_cautious() -> None:
    assert RunMode.AUTO == "auto"
    assert RunMode.CAUTIOUS == "cautious"


def test_can_generate_rule_requires_verified_detection_spec() -> None:
    assert can_generate_rule(detection_spec_verified=True) is True
    assert can_generate_rule(detection_spec_verified=False) is False


def test_can_enter_final_review_requires_proven_obligations_and_validation() -> None:
    obligations = [
        ProofObligation(
            run_id="run_1",
            rule_candidate_id="candidate_1",
            claim_type=ProofObligationType.CITATION_FAITHFUL,
            claim_text="citations exact",
            required_artifact_types=["citation_verification"],
            status=ProofObligationStatus.PROVEN,
        )
    ]

    assert can_enter_final_review(static_valid=True, proof_obligations=obligations) is True
    assert can_enter_final_review(static_valid=False, proof_obligations=obligations) is False
