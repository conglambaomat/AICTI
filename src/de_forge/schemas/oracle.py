from __future__ import annotations

from pydantic import BaseModel, Field


class OracleCase(BaseModel):
    id: str
    expected_techniques: list[str] = Field(min_length=1)
    expected_behaviors: list[str] = Field(default_factory=list)
    expected_telemetry: list[str] = Field(min_length=1)
    expected_positive_event_ids: list[str] = Field(default_factory=list)
    must_not_match_benign_event_ids: list[str] = Field(default_factory=list)
    expected_logic_family: list[str] = Field(default_factory=list)


class OracleEvaluationResult(BaseModel):
    technique_score: float
    telemetry_score: float
    event_score: float
    benign_avoidance_score: float
    logic_family_score: float
    overall_score: float
