"""Canonical orchestration state transitions for DE-Forge."""

from collections.abc import Mapping


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


def can_transition(state_from: str, state_to: str, transitions: Mapping[str, tuple[str, ...]] | None = None) -> bool:
    """Return True if state_to is a permitted transition from state_from."""
    transition_map = transitions or CANONICAL_TRANSITIONS
    return state_to in transition_map.get(state_from, tuple())
