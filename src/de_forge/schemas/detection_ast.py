from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class LogicOperator(StrEnum):
    ALL = "all"
    ANY = "any"
    NOT = "not"


class FieldConditionNode(BaseModel):
    id: str
    node_type: Literal["field_condition"] = "field_condition"
    field: str
    operator: str
    values: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class LogicGroupNode(BaseModel):
    id: str
    node_type: Literal["logic_group"] = "logic_group"
    operator: LogicOperator
    children: list[FieldConditionNode] = Field(min_length=1)


class DetectionAst(BaseModel):
    id: str
    detection_spec_id: str
    root: LogicGroupNode
    telemetry_source_id: str
    attack_techniques: list[str]
