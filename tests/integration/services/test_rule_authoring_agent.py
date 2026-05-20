from __future__ import annotations

import pytest

from de_forge.services.rule_generation import RuleGenerationService


def _spec() -> dict[str, object]:
    return {
        "abstain": False,
        "behavior": [{"behavior_label": "process_execution", "evidence_ids": ["e1"]}],
        "attack_mappings": [{"technique_id": "T1059.001"}],
        "telemetry_requirements": [{"source": "process_creation", "allowed_fields": ["Image", "CommandLine"]}],
        "logic": {"selection": "process_creation", "condition": "selection"},
        "false_positive_hypotheses": ["admin scripts"],
        "test_plan": ["malicious powershell"],
    }


def test_generate_rule_returns_sigma_package() -> None:
    service = RuleGenerationService()
    result = service.generate_rule(_spec(), profile="balanced")

    assert result["abstain"] is False
    assert isinstance(result["sigma_rule"], dict)
    assert result["sigma_rule"]["logsource"]["category"] == "process_creation"


def test_generate_rule_abstains_when_spec_abstains() -> None:
    service = RuleGenerationService()
    result = service.generate_rule({"abstain": True, "abstain_reason": "unsafe"}, profile="balanced")

    assert result["abstain"] is True
    assert result["sigma_rule"] == {}
    assert result["abstain_reason"] == "unsafe"


def test_generate_rule_rejects_missing_logic() -> None:
    service = RuleGenerationService()
    bad_spec = _spec()
    bad_spec.pop("logic")

    with pytest.raises(ValueError):
        service.generate_rule(bad_spec, profile="balanced")
