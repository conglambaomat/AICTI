import yaml

from de_forge.schemas.detection_ast import (
    DetectionAst,
    FieldConditionNode,
    LogicGroupNode,
    LogicOperator,
)
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.sigma_compiler import SigmaCompiler
from de_forge.services.sigma_validator import SigmaValidator


def _ast() -> DetectionAst:
    return DetectionAst(
        id="ast_1",
        detection_spec_id="spec_1",
        telemetry_source_id="process_creation",
        attack_techniques=["T1059.001"],
        root=LogicGroupNode(
            id="group_1",
            operator=LogicOperator.ALL,
            children=[
                FieldConditionNode(
                    id="cond_1",
                    field="CommandLine",
                    operator="contains_any",
                    values=["-enc", "-EncodedCommand"],
                    evidence_ids=["evidence_1"],
                )
            ],
        ),
    )


def test_sigma_rule_schema_tracks_detection_and_provenance() -> None:
    rule = SigmaRule(
        title="Suspicious Encoded PowerShell Command",
        id="rule_1",
        status="experimental",
        description="Detects encoded PowerShell command execution.",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation", service=None),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}, "condition": "selection_1"},
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )

    assert rule.logsource.category == "process_creation"
    assert rule.provenance["selection_1"] == ["evidence_1"]


def test_sigma_compiler_emits_process_creation_rule_from_ast() -> None:
    rule = SigmaCompiler().compile(
        _ast(),
        title="Suspicious Encoded PowerShell Command",
        description="Detects encoded PowerShell command execution.",
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
    )

    assert rule.logsource.product == "windows"
    assert rule.logsource.category == "process_creation"
    assert rule.detection["selection_cond_1"] == {
        "CommandLine|contains": ["-enc", "-EncodedCommand"]
    }
    assert rule.detection["condition"] == "selection_cond_1"
    assert "attack.t1059.001" in rule.tags
    assert rule.provenance["selection_cond_1"] == ["evidence_1"]


def test_sigma_validator_rejects_missing_condition() -> None:
    rule = SigmaRule(
        title="Bad Rule",
        id="rule_bad",
        status="experimental",
        description="missing condition",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}},
        falsepositives=["admin usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )

    assert SigmaValidator().validate(rule) is False


def test_sigma_compiler_serializes_rule_to_yaml() -> None:
    compiler = SigmaCompiler()
    rule = compiler.compile(
        _ast(),
        title="Suspicious Encoded PowerShell Command",
        description="Detects encoded PowerShell command execution.",
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
    )

    serialized = compiler.to_yaml(rule)
    parsed = yaml.safe_load(serialized)

    assert parsed["title"] == "Suspicious Encoded PowerShell Command"
    assert parsed["detection"]["condition"] == "selection_cond_1"
