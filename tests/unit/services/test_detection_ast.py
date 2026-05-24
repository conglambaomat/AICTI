from de_forge.schemas.detection_ast import FieldConditionNode, LogicGroupNode, LogicOperator
from de_forge.schemas.detection_spec import BehaviorRule, DetectionSpec
from de_forge.services.detection_ast_service import DetectionAstService


def _verified_spec() -> DetectionSpec:
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
        evidence_ids=["ev-1"],
        behavior_ids=["bh-1"],
        detection_strategy="behavioral",
        analytic="process analytic",
        data_component="process_creation",
        allowed_telemetry_fields=["CommandLine"],
        rationale_traceability=["ev-1 -> bh-1"],
    )


def test_field_condition_node_tracks_evidence_ids() -> None:
    node = FieldConditionNode(
        id="cond_1",
        field="CommandLine",
        operator="contains_any",
        values=["-enc", "-EncodedCommand"],
        evidence_ids=["evidence_1"],
    )

    assert node.field == "CommandLine"
    assert node.evidence_ids == ["evidence_1"]


def test_logic_group_node_contains_child_conditions() -> None:
    condition = FieldConditionNode(
        id="cond_1",
        field="CommandLine",
        operator="contains_any",
        values=["-enc"],
        evidence_ids=["evidence_1"],
    )
    group = LogicGroupNode(id="group_1", operator=LogicOperator.ALL, children=[condition])

    assert group.operator == LogicOperator.ALL
    assert group.children[0].id == "cond_1"


def test_detection_ast_service_converts_verified_spec_to_ast() -> None:
    ast = DetectionAstService().from_spec(_verified_spec())

    assert ast.telemetry_source_id == "process_creation"
    assert ast.root.children[0].field == "CommandLine"
    assert ast.attack_techniques == ["T1059.001"]
