import pytest
from pydantic import ValidationError

from de_forge.schemas.detection_spec import BehaviorRule, DetectionSpec
from de_forge.services.detection_spec_verifier import DetectionSpecVerifier


def _valid_spec() -> DetectionSpec:
    return DetectionSpec(
        report_id="report_1",
        behavior_rules=[
            BehaviorRule(
                evidence=["PowerShell executed an encoded command"],
                attack_ids=["T1059.001"],
                required_telemetry=["process_creation"],
                detection_logic="CommandLine contains '-enc'",
            )
        ],
        false_positive_hypotheses=["admin script"],
        test_plan="positive + benign",
    )


def test_detection_spec_verifier_accepts_valid_spec() -> None:
    verifier = DetectionSpecVerifier()

    assert verifier.verify(_valid_spec()) is True


def test_behavior_rule_schema_rejects_unknown_telemetry() -> None:
    with pytest.raises(ValidationError):
        BehaviorRule(
            evidence=["x"],
            attack_ids=["T1059.001"],
            required_telemetry=["unknown_telemetry"],
            detection_logic="x",
        )
