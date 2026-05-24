from __future__ import annotations

import pytest
from pydantic import ValidationError

from de_forge.services.rule_generation import RuleGenerationService


def _spec() -> dict[str, object]:
    return {
        "report_id": "rep_rule_authoring",
        "behavior_rules": [
            {
                "evidence": ["e1"],
                "attack_ids": ["T1059.001"],
                "required_telemetry": ["process_creation"],
                "detection_logic": "CommandLine contains '-enc'",
            }
        ],
        "false_positive_hypotheses": ["admin scripts"],
        "test_plan": "malicious powershell",
        "evidence_ids": ["ev-1"],
        "behavior_ids": ["bh-1"],
        "detection_strategy": "behavioral",
        "analytic": "process analytic",
        "data_component": "process_creation",
        "allowed_telemetry_fields": ["CommandLine"],
        "rationale_traceability": ["ev-1 -> bh-1"],
    }


def test_generate_rule_returns_sigma_package() -> None:
    service = RuleGenerationService()
    result = service.generate_rule(_spec(), profile="balanced")

    assert result["abstain"] is False
    assert isinstance(result["sigma_rule"], dict)
    assert result["sigma_rule"]["logsource"]["category"] == "process_creation"


def test_generate_rule_abstains_when_spec_abstains() -> None:
    service = RuleGenerationService()
    result = service.generate_rule(
        {"abstain": True, "abstain_reason": "unsafe"}, profile="balanced"
    )

    assert result["abstain"] is True
    assert result["sigma_rule"] == {}
    assert result["abstain_reason"] == "unsafe"


def test_generate_rule_rejects_missing_behavior_rules() -> None:
    service = RuleGenerationService()
    bad_spec = _spec()
    bad_spec.pop("behavior_rules")

    with pytest.raises(ValidationError):
        service.generate_rule(bad_spec, profile="balanced")
