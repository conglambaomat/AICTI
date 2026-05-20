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
    """Test structured abstain contract uses required new field names."""
    valid_abstain = AbstainDecision(
        abstain_code="NO_EVIDENCE",
        abstain_context="Report only mentions CVE-2023-1234 without behavioral indicators",
        human_message="Unable to generate a detection rule due to missing observable behavior.",
    )
    assert valid_abstain.abstain_code == "NO_EVIDENCE"
    assert "CVE-2023-1234" in valid_abstain.abstain_context

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="INVALID_CODE",
            abstain_context="Some reason",
            human_message="Human readable message",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="",
            human_message="Human readable message",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_TELEMETRY",
            abstain_context="Telemetry requirements not met",
            human_message="   ",
        )

    with pytest.raises(ValidationError) as exc_info:
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            context="legacy field name",
            human_message="Human readable message",
        )
    assert any(e["type"] == "extra_forbidden" for e in exc_info.value.errors())

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", human_message="Human readable message")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="Some context")

    payload = valid_abstain.model_dump()
    assert set(payload.keys()) == {"abstain_code", "abstain_context", "human_message"}
    assert "context" not in payload

    with pytest.raises(AttributeError):
        _ = valid_abstain.context

    assert set(AbstainDecision.model_fields.keys()) == {
        "abstain_code",
        "abstain_context",
        "human_message",
    }

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="valid",
            human_message="valid",
            extra="z",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="valid",
            human_message="valid",
            context="legacy",
        )

    round_trip = AbstainDecision.model_validate(payload)
    assert round_trip == valid_abstain

    schema = AbstainDecision.model_json_schema()
    assert "abstain_context" in schema["required"]
    assert "human_message" in schema["required"]
    assert "context" not in schema["properties"]

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "context": "legacy"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "abstain_context": " ",
                "human_message": "msg",
            }
        )

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "abstain_context": "ctx",
                "human_message": " ",
            }
        )

    minimal = AbstainDecision.model_validate(
        {
            "abstain_code": "NO_TELEMETRY",
            "abstain_context": "No supported telemetry fields identified",
            "human_message": "Cannot safely generate a detection rule from this report.",
        }
    )
    assert sorted(minimal.model_dump().keys()) == ["abstain_code", "abstain_context", "human_message"]

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_TELEMETRY",
                "abstain_context": "ctx",
                "human_message": "msg",
                "foo": "bar",
            }
        )

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "MAYBE",
                "abstain_context": "Some context",
                "human_message": "Some message",
            }
        )

    assert isinstance(minimal.abstain_code, str)
    assert isinstance(minimal.abstain_context, str)
    assert isinstance(minimal.human_message, str)

    assert "abstain_context" in repr(valid_abstain)
    assert "human_message" in repr(valid_abstain)

    final_valid = AbstainDecision(
        abstain_code="UNSAFE_GENERATION",
        abstain_context="Generated rule remains overbroad after bounded refinement",
        human_message="Generation aborted: unable to produce a safe, specific rule.",
    )
    assert final_valid.abstain_code == "UNSAFE_GENERATION"
    assert final_valid.abstain_context.startswith("Generated rule")
    assert final_valid.human_message.startswith("Generation aborted")

    assert set(final_valid.model_dump().keys()) == {
        "abstain_code",
        "abstain_context",
        "human_message",
    }

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="valid",
            human_message="valid",
            human_messsage="typo",
        )

    last_valid = AbstainDecision(
        abstain_code="NO_EVIDENCE",
        abstain_context="No observable actions extracted",
        human_message="Please provide a report with behavior-level indicators.",
    )
    assert last_valid.abstain_code == "NO_EVIDENCE"
    assert last_valid.abstain_context.endswith("extracted")
    assert last_valid.human_message.startswith("Please provide")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", context="old", human_message="new")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="new")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", human_message="new")

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_TELEMETRY",
                "abstain_context": "ctx",
                "human_message": "msg",
                "context": "legacy",
            }
        )

    assert "context" not in schema["properties"]

    valid_again = AbstainDecision(
        abstain_code="NO_TELEMETRY",
        abstain_context="Required telemetry source not present",
        human_message="Cannot generate a safe detection rule with available data.",
    )
    assert valid_again.abstain_code == "NO_TELEMETRY"
    assert valid_again.abstain_context
    assert valid_again.human_message

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NOT_ALLOWED",
            abstain_context="Some context",
            human_message="Some message",
        )

    assert set(AbstainDecision.model_fields.keys()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="x",
            human_message="y",
            context="legacy should be forbidden",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="some context",
            human_message="",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="",
            human_message="some message",
        )

    assert set(valid_abstain.model_dump().keys()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(AttributeError):
        _ = final_valid.context

    assert "abstain_context" in AbstainDecision.model_fields
    assert "human_message" in AbstainDecision.model_fields
    assert "context" not in AbstainDecision.model_fields

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "abstain_context": "valid",
                "human_message": "valid",
                "context": "legacy",
                "foo": "bar",
            }
        )

    assert sorted(valid_abstain.model_dump().keys()) == [
        "abstain_code",
        "abstain_context",
        "human_message",
    ]

    assert round_trip.model_dump() == payload

    assert "abstain_context" in schema["properties"]
    assert "human_message" in schema["properties"]

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "abstain_context": "valid",
                "human_message": "valid",
                "extra": "z",
            }
        )

    assert valid_abstain.human_message.endswith("behavior.")

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_TELEMETRY",
            abstain_context="Telemetry missing",
            human_message="   ",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_TELEMETRY",
            abstain_context="   ",
            human_message="Readable reason",
        )

    assert set(payload) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "human_message": "missing context",
            }
        )

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(
            {
                "abstain_code": "NO_EVIDENCE",
                "abstain_context": "missing message",
            }
        )

    assert payload["abstain_code"] == "NO_EVIDENCE"

    assert valid_abstain.abstain_context.startswith("Report")

    assert valid_abstain.human_message.startswith("Unable")

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "context": "legacy", "human_message": "msg"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "ctx", "context": "legacy", "human_message": "msg"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "ctx", "human_message": "msg", "unknown": 1})

    assert final_valid.model_dump()["abstain_code"] == "UNSAFE_GENERATION"

    assert set(AbstainDecision.model_fields) == {"abstain_code", "abstain_context", "human_message"}

    assert set(valid_abstain.model_dump()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            context="legacy-only",
        )

    assert "context" not in AbstainDecision.model_json_schema()["properties"]

    assert "abstain_context" in AbstainDecision.model_json_schema()["properties"]

    assert "human_message" in AbstainDecision.model_json_schema()["properties"]

    assert "abstain_context" in AbstainDecision.model_json_schema()["required"]

    assert "human_message" in AbstainDecision.model_json_schema()["required"]

    assert "abstain_code" in AbstainDecision.model_json_schema()["required"]

    assert set(AbstainDecision.model_json_schema()["required"]) == {
        "abstain_code",
        "abstain_context",
        "human_message",
    }

    assert isinstance(AbstainDecision.model_json_schema()["properties"], dict)

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "ctx", "human_message": "msg", "context": "legacy should fail"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "INVALID", "abstain_context": "ctx", "human_message": "msg"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "", "human_message": "msg"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "ctx", "human_message": ""})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "ctx"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "human_message": "msg"})

    assert valid_abstain.model_dump() == payload

    assert payload == {
        "abstain_code": "NO_EVIDENCE",
        "abstain_context": "Report only mentions CVE-2023-1234 without behavioral indicators",
        "human_message": "Unable to generate a detection rule due to missing observable behavior.",
    }

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "ctx", "human_message": "msg", "human_messsage": "typo"})

    assert True

    assert set(payload.keys()) == {"abstain_code", "abstain_context", "human_message"}

    assert "context" not in payload

    assert "context" not in AbstainDecision.model_fields

    assert set(AbstainDecision.model_fields.keys()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", context="legacy", human_message="message")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="context", context="legacy", human_message="message")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="context", human_message="message", unknown="x")

    assert valid_abstain.abstain_code == "NO_EVIDENCE"

    assert valid_abstain.abstain_context

    assert valid_abstain.human_message

    assert set(valid_abstain.model_dump().keys()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(AttributeError):
        _ = valid_abstain.context

    assert "context" not in AbstainDecision.model_json_schema()["properties"]

    assert "abstain_context" in AbstainDecision.model_json_schema()["properties"]

    assert "human_message" in AbstainDecision.model_json_schema()["properties"]

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_TELEMETRY", "abstain_context": "ctx", "human_message": "msg", "context": "legacy"})

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_TELEMETRY", "abstain_context": "ctx", "human_message": "msg", "foo": "bar"})

    assert set(AbstainDecision.model_fields.keys()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="INVALID_CODE",
            abstain_context="Some reason",
            human_message="Human readable message",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="",
            human_message="Human readable message",
        )

    with pytest.raises(ValidationError):
        AbstainDecision(
            abstain_code="NO_EVIDENCE",
            abstain_context="Some reason",
            human_message="",
        )

    assert set(payload.keys()) == {"abstain_code", "abstain_context", "human_message"} and "context" not in payload

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate(payload | {"context": "legacy"})

    assert round_trip == valid_abstain

    with pytest.raises(ValidationError):
        AbstainDecision.model_validate({"abstain_code": "NO_EVIDENCE", "abstain_context": "Some reason", "human_message": "Some message", "extra": 1})

    assert set(AbstainDecision.model_fields.keys()) == {"abstain_code", "abstain_context", "human_message"}

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="   ", human_message="x")

    with pytest.raises(ValidationError):
        AbstainDecision(abstain_code="NO_EVIDENCE", abstain_context="x", human_message="   ")

    assert valid_abstain.model_dump()["abstain_code"] == "NO_EVIDENCE"

    assert "abstain_context" in valid_abstain.model_dump()

    assert "human_message" in valid_abstain.model_dump()

    assert "context" not in valid_abstain.model_dump()

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

    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["valid evidence"],
            attack_ids=["T1547"],
            required_telemetry=["process_creation"],
            detection_logic="valid logic",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("attack_ids",) for e in errors)

    with pytest.raises(ValidationError) as exc_info:
        BehaviorRule(
            evidence=["valid evidence"],
            attack_ids=["T1105"],
            required_telemetry=["file_creation"],
            detection_logic="valid logic",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("required_telemetry",) for e in errors)

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
                required_telemetry=["process_creation"],
                detection_logic="Process creation with suspicious payload execution",
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
