"""
Unit tests for DetectionSpec, AgentIO, and abstain schemas.

Tests the strict validation contracts for detection rule generation.
"""

import pytest
from pydantic import ValidationError

from de_forge.schemas.detection_spec import (
    BehaviorRule,
    DetectionSpec,
)
from de_forge.schemas.abstain import AbstainDecision
from de_forge.schemas.agent_io import RuleGenerationRequest


def test_behavior_rule_requires_evidence_attack_telemetry():
    """
    Test that BehaviorRule requires evidence quotes, ATT&CK mapping, and telemetry.

    A valid behavior rule must contain:
    - evidence: non-empty list of evidence quotes
    - attack_ids: non-empty list of ATT&CK technique IDs
    - required_telemetry: non-empty list of telemetry sources
    """
    # Valid behavior rule should pass
    valid_rule = BehaviorRule(
        evidence=["The malware executes powershell.exe with encoded commands"],
        attack_ids=["T1059.001"],
        required_telemetry=["process_creation"],
        detection_logic="Process creation with powershell.exe and -EncodedCommand flag",
    )
    assert valid_rule.evidence == ["The malware executes powershell.exe with encoded commands"]
    assert valid_rule.attack_ids == ["T1059.001"]
    assert valid_rule.required_telemetry == ["process_creation"]

    # Missing evidence should fail
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=[],
            attack_ids=["T1059.001"],
            required_telemetry=["process_creation"],
            detection_logic="Process creation with powershell.exe",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("evidence",) for e in errors)

    # Missing ATT&CK IDs should fail
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["The malware executes powershell.exe"],
            attack_ids=[],
            required_telemetry=["process_creation"],
            detection_logic="Process creation with powershell.exe",
        )
    assert "attack_ids" in str(exc_info.value).lower()

    # Missing telemetry should fail
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["The malware executes powershell.exe"],
            attack_ids=["T1059.001"],
            required_telemetry=[],
            detection_logic="Process creation with powershell.exe",
        )
    assert "required_telemetry" in str(exc_info.value).lower()


def test_abstain_requires_structured_abstain_code_and_context():
    """
    Test that AbstainDecision requires structured abstain_code and context.

    A valid abstain decision must contain:
    - abstain_code: one of the predefined codes (NO_EVIDENCE, NO_TELEMETRY, etc.)
    - context: non-empty explanation string
    """
    # Valid abstain decision should pass
    valid_abstain = AbstainDecision(
        abstain_code="NO_EVIDENCE",
        context="Report only mentions CVE-2023-1234 without any behavioral indicators",
    )
    assert valid_abstain.abstain_code == "NO_EVIDENCE"
    assert "CVE-2023-1234" in valid_abstain.context

    # Invalid abstain code should fail
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="INVALID_CODE",
            context="Some reason",
        )
    assert "abstain_code" in str(exc_info.value).lower()

    # Empty context should fail
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            context="",
        )
    assert "context" in str(exc_info.value).lower()

    # Missing context should fail
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="NO_TELEMETRY",
            context="   ",  # whitespace-only
        )
    assert "context" in str(exc_info.value).lower()


def test_behavior_rule_strict_validation_for_attack_ids_telemetry_and_blank_strings():
    """Test strict validation for ATT&CK IDs, telemetry normalization, and blank strings."""
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["valid evidence"],
            attack_ids=["INVALID"],
            required_telemetry=["process_creation"],
            detection_logic="valid logic",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("attack_ids",) for e in errors)

    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["valid evidence"],
            attack_ids=["T1059.001"],
            required_telemetry=["   "],
            detection_logic="valid logic",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("required_telemetry",) for e in errors)

    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["   "],
            attack_ids=["T1059.001"],
            required_telemetry=["process_creation"],
            detection_logic="valid logic",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("evidence",) for e in errors)

    normalized = BehaviorRule(
        evidence=["  valid evidence  "],
        attack_ids=[" T1105 "],
        required_telemetry=[" Process_Creation "],
        detection_logic="  detect suspicious process  ",
    )
    assert normalized.evidence == ["valid evidence"]
    assert normalized.attack_ids == ["T1105"]
    assert normalized.required_telemetry == ["process_creation"]
    assert normalized.detection_logic == "detect suspicious process"


def test_contract_schemas_forbid_extra_fields():
    """Test contract schemas reject undeclared fields via extra='forbid'."""
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["ev"],
            attack_ids=["T1105"],
            required_telemetry=["process_creation"],
            detection_logic="logic",
            unknown_field="boom",
        )
    assert any(e["type"] == "extra_forbidden" for e in exc_info.value.errors())

    with pytest.raises(ValidationError) as exc_info:
        DetectionSpec(
            report_id="report-1",
            behavior_rules=[
                BehaviorRule(
                    evidence=["ev"],
                    attack_ids=["T1105"],
                    required_telemetry=["process_creation"],
                    detection_logic="logic",
                )
            ],
            false_positive_hypotheses=["fp"],
            test_plan="plan",
            extra_field=True,
        )
    assert any(e["type"] == "extra_forbidden" for e in exc_info.value.errors())

    valid_spec = DetectionSpec(
        report_id="report-1",
        behavior_rules=[
            BehaviorRule(
                evidence=["ev"],
                attack_ids=["T1105"],
                required_telemetry=["process_creation"],
                detection_logic="logic",
            )
        ],
        false_positive_hypotheses=["fp"],
        test_plan="plan",
    )

    with pytest.raises(ValidationError) as exc_info:
        RuleGenerationRequest(
            detection_spec=valid_spec,
            target_format="sigma",
            surprise="nope",
        )
    assert any(e["type"] == "extra_forbidden" for e in exc_info.value.errors())


def test_detection_spec_first_gate_rejects_missing_validated_spec():
    """
    Test that RuleGenerationRequest enforces DetectionSpec-first gate.

    The system must reject requests that:
    - Provide raw report text without a validated DetectionSpec
    - Have a DetectionSpec without required fields

    Valid requests must contain a fully validated DetectionSpec object.
    """
    # Valid request with complete DetectionSpec should pass
    valid_spec = DetectionSpec(
        report_id="report-001",
        behavior_rules=[
            BehaviorRule(
                evidence=["Malware drops payload.exe to temp directory"],
                attack_ids=["T1105"],
                required_telemetry=["file_creation"],
                detection_logic="File creation in temp directory with suspicious name",
            )
        ],
        false_positive_hypotheses=["Legitimate software updates may trigger this"],
        test_plan="Test with benign software installers and known malware samples",
    )

    valid_request = RuleGenerationRequest(
        detection_spec=valid_spec,
        target_format="sigma",
    )
    assert valid_request.detection_spec.report_id == "report-001"
    assert len(valid_request.detection_spec.behavior_rules) == 1

    # Request without DetectionSpec should fail
    with pytest.raises(ValidationError) as exc_info:
        RuleGenerationRequest(
            target_format="sigma",
        )
    assert "detection_spec" in str(exc_info.value).lower()

    # Request with invalid DetectionSpec (missing behavior_rules) should fail
    with pytest.raises(ValidationError) as exc_info:
        invalid_spec = DetectionSpec(
            report_id="report-002",
            behavior_rules=[],  # Empty behavior rules
            false_positive_hypotheses=["Some hypothesis"],
            test_plan="Some test plan",
        )
    assert "behavior_rules" in str(exc_info.value).lower()

    # Request with DetectionSpec missing required fields should fail during spec creation
    with pytest.raises(ValidationError) as exc_info:
        DetectionSpec(
            report_id="report-003",
            behavior_rules=[
                BehaviorRule(
                    evidence=["Some evidence"],
                    attack_ids=["T1059.001"],
                    required_telemetry=["process_creation"],
                    detection_logic="Some logic",
                )
            ],
            # Missing false_positive_hypotheses and test_plan
        )
    errors = str(exc_info.value).lower()
    assert "false_positive_hypotheses" in errors or "test_plan" in errors
