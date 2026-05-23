"""Default-deny memory ACL policy engine."""

from __future__ import annotations

import json

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


REQUIRED_STAGE_CONTRACTS: dict[str, tuple[str, ...]] = {
    "rule_generation": ("detection_spec.draft",),
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

    def stage_contract_missing(
        self, *, stage: str, available_namespaces: set[str]
    ) -> tuple[str, ...]:
        required_namespaces = REQUIRED_STAGE_CONTRACTS.get(stage, ())
        return tuple(
            namespace
            for namespace in required_namespaces
            if namespace not in available_namespaces
        )


def namespace_from_scope(scope: str) -> str:
    payload = scope.split(":", 1)
    if len(payload) != 2:
        return ""
    return payload[1]


def latest_payload_namespaces(rows: list[tuple[str, str]]) -> set[str]:
    namespaces: set[str] = set()
    for scope, value in rows:
        namespace = namespace_from_scope(scope)
        if not namespace:
            continue
        try:
            json.loads(value)
        except json.JSONDecodeError:
            continue
        namespaces.add(namespace)
    return namespaces
