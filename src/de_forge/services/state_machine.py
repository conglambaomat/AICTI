"""Canonical orchestration state transitions for DE-Forge."""

from collections.abc import Mapping

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.run import RunState

CANONICAL_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "INGESTED": ("CHUNKED",),
    "CHUNKED": ("EVIDENCE_EXTRACTED",),
    "EVIDENCE_EXTRACTED": ("ATTACK_MAPPED", "ABSTAINED"),
    "ATTACK_MAPPED": ("TELEMETRY_GROUNDED",),
    "TELEMETRY_GROUNDED": ("SPEC_BUILT", "ABSTAINED"),
    "SPEC_BUILT": ("QUERY_PORTFOLIO_READY",),
    "QUERY_PORTFOLIO_READY": ("QUERY_SELECTED",),
    "QUERY_SELECTED": ("RULE_DRAFTED",),
    "RULE_DRAFTED": ("STATIC_VALIDATED",),
    "STATIC_VALIDATED": ("DYNAMIC_VALIDATED", "FAILED_VALIDATION"),
    "DYNAMIC_VALIDATED": ("RULE_VALIDATED", "FAILED_VALIDATION"),
    "RULE_VALIDATED": ("AWAITING_REVIEW",),
    "AWAITING_REVIEW": ("APPROVED", "REJECTED"),
    "APPROVED": tuple(),
    "EXPORTED": tuple(),
    "ABSTAINED": tuple(),
    "FAILED_VALIDATION": tuple(),
    "FAILED_GENERATION": tuple(),
    "REJECTED": tuple(),
}


def can_transition(
    state_from: str, state_to: str, transitions: Mapping[str, tuple[str, ...]] | None = None
) -> bool:
    """Return True if state_to is a permitted transition from state_from."""
    transition_map = transitions or CANONICAL_TRANSITIONS
    return state_to in transition_map.get(state_from, tuple())


class StateMachine:
    def __init__(self) -> None:
        self.allowed: dict[RunState, set[RunState]] = {
            RunState.CREATED: {RunState.INGESTED, RunState.FAILED},
            RunState.INGESTED: {RunState.EVIDENCE_READY, RunState.ABSTAINED, RunState.FAILED},
            RunState.EVIDENCE_READY: {
                RunState.DETECTION_SPEC_READY,
                RunState.ABSTAINED,
                RunState.FAILED,
            },
            RunState.DETECTION_SPEC_READY: {
                RunState.DETECTION_SPEC_VERIFIED,
                RunState.AWAITING_REVIEW,
                RunState.FAILED,
            },
            RunState.DETECTION_SPEC_VERIFIED: {
                RunState.RULE_CANDIDATES_READY,
                RunState.ABSTAINED,
                RunState.FAILED,
            },
            RunState.RULE_CANDIDATES_READY: {
                RunState.VALIDATED,
                RunState.ABSTAINED,
                RunState.FAILED,
            },
            RunState.VALIDATED: {RunState.AWAITING_REVIEW, RunState.ABSTAINED, RunState.FAILED},
            RunState.AWAITING_REVIEW: {RunState.APPROVED, RunState.REJECTED},
        }

    def transition(self, current: RunState, target: RunState) -> RunState:
        if target not in self.allowed.get(current, set()):
            raise ValidationGateError(f"illegal transition from {current.value} to {target.value}")
        return target
