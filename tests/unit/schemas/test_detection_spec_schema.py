"""
Unit tests for DetectionSpec, AgentIO, and abstain schemas.

Tests the strict validation contracts for detection rule generation.
"""

import pytest
from pydantic import ValidationError

from de_forge.schemas.abstain import AbstainDecision
from de_forge.schemas.agent_io import RuleGenerationRequest
from de_forge.schemas.detection_spec import (
    BehaviorRule,
    DetectionSpec,
)


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
    assert any(e["loc"] == ("evidence",) and e["type"] == "too_short" for e in errors)

    # Missing ATT&CK IDs should fail
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["The malware executes powershell.exe"],
            attack_ids=[],
            required_telemetry=["process_creation"],
            detection_logic="Process creation with powershell.exe",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("attack_ids",) and e["type"] == "too_short" for e in errors)

    # Missing telemetry should fail
    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["The malware executes powershell.exe"],
            attack_ids=["T1059.001"],
            required_telemetry=[],
            detection_logic="Process creation with powershell.exe",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("required_telemetry",) and e["type"] == "too_short" for e in errors)


def test_abstain_decision_valid_construction():
    """AbstainDecision accepts valid structured abstain payloads."""
    abstain = AbstainDecision(
        abstain_code="NO_EVIDENCE",
        abstain_context="Report only mentions CVE-2023-1234 without behavioral indicators",
        human_message="Unable to generate a detection rule due to missing observable behavior.",
    )

    assert abstain.model_dump() == {
        "abstain_code": "NO_EVIDENCE",
        "abstain_context": "Report only mentions CVE-2023-1234 without behavioral indicators",
        "human_message": "Unable to generate a detection rule due to missing observable behavior.",
    }


def test_abstain_decision_rejects_invalid_abstain_code():
    """AbstainDecision rejects values outside the allowed abstain_code enum."""
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="INVALID_CODE",
            abstain_context="Some reason",
            human_message="Human readable message",
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("abstain_code",) for e in errors)


def test_abstain_decision_enforces_required_fields():
    """AbstainDecision requires abstain_context and human_message."""
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(abstain_code="NO_EVIDENCE", human_message="Human readable message")
    assert any(
        e["loc"] == ("abstain_context",) and e["type"] == "missing" for e in exc_info.value.errors()
    )

    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="Some context")
    assert any(
        e["loc"] == ("human_message",) and e["type"] == "missing" for e in exc_info.value.errors()
    )


def test_abstain_decision_rejects_blank_strings():
    """AbstainDecision rejects blank/whitespace-only context and human message."""
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="   ",
            human_message="Human readable message",
        )
    assert any(e["loc"] == ("abstain_context",) for e in exc_info.value.errors())

    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="Some reason",
            human_message="   ",
        )
    assert any(e["loc"] == ("human_message",) for e in exc_info.value.errors())


def test_abstain_decision_rejects_legacy_context_and_extra_fields():
    """AbstainDecision rejects legacy `context` alias and undeclared input fields."""
    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "abstain_context": "Report only lists CVE IDs without observable behavior.",
                "human_message": "Cannot generate a safe rule without evidence-backed behaviors.",
                "context": "legacy alias",
                "unknown_field": "unexpected",
            }
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("context",) and e["type"] == "extra_forbidden" for e in errors)
    assert any(e["loc"] == ("unknown_field",) and e["type"] == "extra_forbidden" for e in errors)

    schema = AbstainDecision.model_json_schema()
    assert "context" not in schema["properties"]
    assert set(schema["required"]) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(AttributeError):
        _ = AbstainDecision(
            abstain_code="NO_TELEMETRY",
            abstain_context="Sysmon process_creation data is unavailable for this environment.",
            human_message="Cannot generate a safe detection rule with available telemetry.",
        ).context

    assert set(AbstainDecision.model_fields.keys()) == {
        "abstain_code",
        "abstain_context",
        "human_message",
    }


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

    accepted = BehaviorRule(
        evidence=["valid evidence"],
        attack_ids=["T1547"],
        required_telemetry=["file_event"],
        detection_logic="valid logic",
    )
    assert accepted.attack_ids == ["T1547"]
    assert accepted.required_telemetry == ["file_event"]

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
        evidence_ids=["ev-1"],
        behavior_ids=["bh-1"],
        detection_strategy="behavioral",
        analytic="process correlation",
        data_component="process_creation",
        allowed_telemetry_fields=["Image"],
        rationale_traceability=["ev-1 -> bh-1"],
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
                required_telemetry=["process_creation"],
                detection_logic="Process creation with suspicious payload execution",
            )
        ],
        false_positive_hypotheses=["Legitimate software updates may trigger this"],
        test_plan="Test with benign software installers and known malware samples",
        evidence_ids=["ev-1"],
        behavior_ids=["bh-1"],
        detection_strategy="behavioral",
        analytic="payload execution analytic",
        data_component="process_creation",
        allowed_telemetry_fields=["Image", "CommandLine"],
        rationale_traceability=["ev-1 -> bh-1 -> rule"],
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
        DetectionSpec(
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
