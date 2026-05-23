"""Default-deny memory ACL policy engine."""

from __future__ import annotations

ACL: dict[str, dict[str, set[str]]] = {
    "evidence_agent": {"evidence.working_set": {"write"}},
    "attack_mapping_agent": {
        "evidence.working_set": {"read"},
        "attack_mapping.hypotheses": {"write"},
    },
    "detection_spec_agent": {
        "evidence.working_set": {"read"},
        "attack_mapping.hypotheses": {"read"},
        "detection_spec.draft": {"write"},
    },
    "rule_generation_agent": {
        "detection_spec.draft": {"read"},
        "rule_generation.draft": {"write"},
    },
    "static_validation": {
        "rule_generation.draft": {"read"},
        "validation.findings": {"write"},
    },
    "critic_agent": {
        "rule_generation.draft": {"read"},
        "validation.findings": {"read"},
        "refinement.plan": {"write"},
    },
    "review_service": {"review.handoff": {"read", "write"}},
}


class MemoryPolicyEngine:
    def can_access(
        self,
        *,
        role: str,
        namespace: str,
        operation: str,
        stage: str,
        run_state: str,
    ) -> bool:
        del stage, run_state
        role_permissions = ACL.get(role)
        if role_permissions is None:
            return False
        namespace_permissions = role_permissions.get(namespace)
        if namespace_permissions is None:
            return False
        return operation in namespace_permissions
