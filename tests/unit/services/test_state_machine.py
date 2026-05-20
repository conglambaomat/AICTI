"""Unit tests for canonical orchestration state transitions."""

import pytest

from de_forge.services.state_machine import CANONICAL_TRANSITIONS, can_transition


@pytest.mark.parametrize(
    ("state_from", "state_to"),
    [
        ("INGESTED", "CHUNKED"),
        ("EVIDENCE_EXTRACTED", "ATTACK_MAPPED"),
        ("EVIDENCE_EXTRACTED", "ABSTAINED"),
        ("AWAITING_REVIEW", "APPROVED"),
        ("AWAITING_REVIEW", "REJECTED"),
    ],
)
def test_allowed_transitions(state_from: str, state_to: str) -> None:
    """Returns True for allowed canonical transitions."""
    assert can_transition(state_from, state_to)


@pytest.mark.parametrize(
    ("state_from", "state_to"),
    [
        ("INGESTED", "EVIDENCE_EXTRACTED"),
        ("RULE_VALIDATED", "APPROVED"),
        ("APPROVED", "EXPORTED"),
        ("ABSTAINED", "INGESTED"),
    ],
)
def test_disallowed_transitions(state_from: str, state_to: str) -> None:
    """Returns False for disallowed canonical transitions."""
    assert not can_transition(state_from, state_to)


@pytest.mark.parametrize(
    "terminal_state",
    [
        "APPROVED",
        "EXPORTED",
        "ABSTAINED",
        "FAILED_VALIDATION",
        "FAILED_GENERATION",
        "REJECTED",
    ],
)
def test_terminal_states_have_no_outgoing_transitions(terminal_state: str) -> None:
    """Terminal states define no outbound transitions."""
    assert CANONICAL_TRANSITIONS[terminal_state] == tuple()


@pytest.mark.parametrize(
    ("state_from", "state_to"),
    [
        ("UNKNOWN", "CHUNKED"),
        ("INGESTED", "UNKNOWN"),
        ("UNKNOWN", "UNKNOWN"),
    ],
)
def test_unknown_state_handling(state_from: str, state_to: str) -> None:
    """Unknown states are handled safely as non-transitionable."""
    assert not can_transition(state_from, state_to)
