from __future__ import annotations

import re

from de_forge.core.errors import ValidationGateError
from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.detection_ast import (
    DetectionAst,
    FieldConditionNode,
    LogicGroupNode,
    LogicOperator,
)
from de_forge.schemas.detection_spec import DetectionSpec
from de_forge.services.telemetry_registry import field_exists, is_supported_telemetry_type


class DetectionAstService:
    _CONTAINS_PATTERN = re.compile(r"^([A-Za-z0-9_]+)\s+contains\s+'([^']+)'$")

    def _parse_contains_clauses(self, detection_logic: str) -> list[tuple[str, str]]:
        if " or " in detection_logic.lower():
            raise ValidationGateError("unsupported detection logic: OR conditions not supported")

        clauses = [segment.strip() for segment in detection_logic.split(" and ") if segment.strip()]
        if not clauses:
            raise ValidationGateError("unsupported detection logic: empty")

        parsed: list[tuple[str, str]] = []
        for clause in clauses:
            match = self._CONTAINS_PATTERN.fullmatch(clause)
            if match is None:
                raise ValidationGateError("unsupported detection logic")
            parsed.append((match.group(1), match.group(2)))
        return parsed

    def _validate_telemetry_and_fields(
        self, telemetry_source_id: str, parsed_conditions: list[tuple[str, str]]
    ) -> None:
        if not is_supported_telemetry_type(telemetry_source_id):
            raise ValidationGateError(f"unsupported telemetry type: {telemetry_source_id}")

        for field_name, _ in parsed_conditions:
            if not field_exists(telemetry_source_id, field_name):
                raise ValidationGateError(f"unsupported telemetry field: {field_name}")

    def _build_condition_nodes(
        self, parsed_conditions: list[tuple[str, str]], evidence_ids: list[str]
    ) -> list[FieldConditionNode]:
        children: list[FieldConditionNode] = []
        for field_name, needle in parsed_conditions:
            node_id = f"cond_{snapshot_hash({'field': field_name, 'needle': needle})[:10]}"
            children.append(
                FieldConditionNode(
                    id=node_id,
                    field=field_name,
                    operator="contains_any",
                    values=[needle],
                    evidence_ids=evidence_ids,
                )
            )
        return children

    def from_detection_spec_model(self, spec_model: object) -> DetectionAst:
        spec_payload = getattr(spec_model, "spec_payload", None)
        if not spec_payload:
            raise ValidationGateError(
                "DetectionSpec must include spec_payload before AST generation"
            )
        spec = DetectionSpec.model_validate_json(spec_payload)
        return self.from_spec(spec)

    def from_spec(self, spec: DetectionSpec) -> DetectionAst:
        if not spec.behavior_rules:
            raise ValidationGateError(
                "DetectionSpec must include behavior rules before AST generation"
            )

        rule = spec.behavior_rules[0]
        telemetry_source_id = rule.required_telemetry[0]
        parsed_conditions = self._parse_contains_clauses(rule.detection_logic)
        self._validate_telemetry_and_fields(telemetry_source_id, parsed_conditions)
        children = self._build_condition_nodes(parsed_conditions, rule.evidence)

        root = LogicGroupNode(
            id=f"group_{snapshot_hash(spec.report_id)[:10]}",
            operator=LogicOperator.ALL,
            children=children,
        )

        return DetectionAst(
            id=f"ast_{snapshot_hash(spec.model_dump(mode='json'))[:12]}",
            detection_spec_id=spec.report_id,
            root=root,
            telemetry_source_id=telemetry_source_id,
            attack_techniques=rule.attack_ids,
        )
