from __future__ import annotations

from de_forge.services.detection_spec import DetectionSpecService


def _evidence() -> list[dict[str, object]]:
    return [
        {
            "evidence_id": "e1",
            "behavior_label": "process_execution",
            "quote": "powershell.exe -enc ...",
            "chunk_id": "chunk-1",
        }
    ]


def _mappings() -> list[dict[str, object]]:
    return [
        {
            "technique_id": "T1059.001",
            "technique_name": "Command and Scripting Interpreter: PowerShell",
            "confidence": 0.9,
            "evidence_ids": ["e1"],
            "rationale": "Evidence supports PowerShell execution",
        }
    ]


def test_build_detection_spec_returns_complete_behavior_branch() -> None:
    service = DetectionSpecService()
    spec = service.build_detection_spec(
        evidence_spans=_evidence(),
        attack_mappings=_mappings(),
        telemetry_registry={"process_creation": ["Image", "CommandLine"]},
        profile="balanced",
    )
    assert isinstance(spec, dict)

    assert spec["abstain"] is False
    assert spec["behavior"]
    assert spec["attack_mappings"]
    assert spec["telemetry_requirements"]
    assert spec["logic"]
    assert spec["false_positive_hypotheses"]
    assert spec["test_plan"]


def test_build_detection_spec_abstains_on_missing_inputs() -> None:
    service = DetectionSpecService()
    spec = service.build_detection_spec(
        evidence_spans=[],
        attack_mappings=[],
        telemetry_registry={"process_creation": ["Image", "CommandLine"]},
        profile="balanced",
    )

    assert isinstance(spec, dict)

    assert spec["abstain"] is True
    assert isinstance(spec["abstain_reason"], str)
    assert spec["abstain_reason"]
    assert spec["behavior"] == []
