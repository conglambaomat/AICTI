"""Integration tests for memory service policy behavior."""

from de_forge.services.memory_policy import MemoryPolicyEngine


def test_policy_default_deny_unknown_role() -> None:
    policy = MemoryPolicyEngine()

    allowed = policy.can_access(
        role="unknown_role",
        namespace="evidence.working_set",
        operation="read",
        stage="evidence",
        run_state="ingested",
    )

    assert allowed is False


def test_policy_allows_whitelisted_role_namespace_operation() -> None:
    policy = MemoryPolicyEngine()

    allowed = policy.can_access(
        role="attack_mapping_agent",
        namespace="evidence.working_set",
        operation="read",
        stage="attack_mapping",
        run_state="evidence_ready",
    )

    assert allowed is True
