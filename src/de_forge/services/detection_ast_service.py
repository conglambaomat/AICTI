from __future__ import annotations

from de_forge.core.errors import ValidationGateError
from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.detection_ast import (
    DetectionAst,
    FieldConditionNode,
    LogicGroupNode,
    LogicOperator,
)
from de_forge.schemas.detection_spec import DetectionSpec


class DetectionAstService:
    def from_spec(self, spec: DetectionSpec) -> DetectionAst:
        if not spec.behavior_rules:
            raise ValidationGateError(
                "DetectionSpec must include behavior rules before AST generation"
            )

        rule = spec.behavior_rules[0]
        children = [
            FieldConditionNode(
                id=f"cond_{snapshot_hash({'field': 'CommandLine', 'logic': rule.detection_logic})[:10]}",
                field="CommandLine",
                operator="contains_any",
                values=[rule.detection_logic],
                evidence_ids=rule.evidence,
            )
        ]
        root = LogicGroupNode(
            id=f"group_{snapshot_hash(spec.report_id)[:10]}",
            operator=LogicOperator.ALL,
            children=children,
        )

        return DetectionAst(
            id=f"ast_{snapshot_hash(spec.model_dump(mode='json'))[:12]}",
            detection_spec_id=spec.report_id,
            root=root,
            telemetry_source_id=rule.required_telemetry[0],
            attack_techniques=rule.attack_ids,
        )
