"""Schemas for persisted pipeline artifacts and lineage."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ArtifactKind(StrEnum):
    REPORT = "report"
    CHUNK = "chunk"
    EVIDENCE_GRAPH = "evidence_graph"
    DETECTION_SPEC = "detection_spec"
    PROOF_OBLIGATION = "proof_obligation"
    RULE_CANDIDATE = "rule_candidate"
    VALIDATION_RESULT = "validation_result"


class ArtifactCreate(BaseModel):
    run_id: str
    kind: ArtifactKind
    stage: str
    payload: dict[str, Any]
    input_hash: str
    output_hash: str
    parent_artifact_ids: list[str] = Field(default_factory=list)
    created_by: str

    @field_validator("run_id", "stage", "input_hash", "output_hash", "created_by")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value
