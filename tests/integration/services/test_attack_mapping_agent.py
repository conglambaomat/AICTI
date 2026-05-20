from __future__ import annotations

import pytest

from de_forge.services.attack_mapping import AttackMappingService


def _evidence() -> list[dict[str, object]]:
    return [
        {
            "evidence_id": "e1",
            "behavior_label": "powershell_execution",
            "quote": "powershell.exe -enc ...",
        }
    ]


def test_mapping_returns_valid_structure() -> None:
    service = AttackMappingService()
    result = service.map_attack(_evidence(), profile="balanced")

    assert result["abstain"] is False
    assert isinstance(result["mappings"], list)
    assert len(result["mappings"]) >= 1
    first = result["mappings"][0]
    assert first["technique_id"].startswith("T")
    assert 0.0 <= first["confidence"] <= 1.0
    assert first["evidence_ids"] == ["e1"]


def test_abstain_for_ambiguous_evidence() -> None:
    service = AttackMappingService()
    result = service.map_attack([], profile="balanced")

    assert result["abstain"] is True
    assert result["mappings"] == []
    assert isinstance(result["abstain_reason"], str)
    assert result["abstain_reason"]


def test_invalid_technique_format_rejected() -> None:
    service = AttackMappingService()
    with pytest.raises(ValueError):
        service.validate_mapping(
            {
                "technique_id": "invalid",
                "technique_name": "bad",
                "confidence": 0.5,
                "evidence_ids": ["e1"],
                "rationale": "x",
            }
        )


def test_profile_threshold_abstains_when_confidence_too_low_for_strict() -> None:
    service = AttackMappingService()
    low_confidence_evidence = [
        {
            "evidence_id": "e1",
            "behavior_label": "suspicious_scripting",
            "quote": "script.exe ran",
        }
    ]

    result = service.map_attack(low_confidence_evidence, profile="strict")

    assert result["abstain"] is True
    assert result["mappings"] == []
    assert result["abstain_reason"] == "ATTACK_CONFIDENCE_BELOW_PROFILE_THRESHOLD"


def test_profile_threshold_allows_balanced_for_same_evidence() -> None:
    service = AttackMappingService()
    low_confidence_evidence = [
        {
            "evidence_id": "e1",
            "behavior_label": "suspicious_scripting",
            "quote": "script.exe ran",
        }
    ]

    result = service.map_attack(low_confidence_evidence, profile="balanced")

    assert result["abstain"] is False
    assert result["mappings"]
    assert result["mappings"][0]["confidence"] == 0.8


def test_unknown_profile_falls_back_to_balanced_threshold() -> None:
    service = AttackMappingService()
    low_confidence_evidence = [
        {
            "evidence_id": "e1",
            "behavior_label": "suspicious_scripting",
            "quote": "script.exe ran",
        }
    ]

    result = service.map_attack(low_confidence_evidence, profile="unknown")

    assert result["abstain"] is False
    assert result["mappings"]
