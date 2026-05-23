from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from de_forge.schemas.sigma import SigmaRule


class CandidateType(StrEnum):
    HIGH_PRECISION = "high_precision"
    BALANCED = "balanced"
    HIGH_RECALL = "high_recall"


class CandidateScore(BaseModel):
    evidence_support: float = Field(default=0.0, ge=0.0, le=1.0)
    citation_faithfulness: float = Field(default=0.0, ge=0.0, le=1.0)
    telemetry_fit: float = Field(default=0.0, ge=0.0, le=1.0)
    static_validity: float = Field(default=0.0, ge=0.0, le=1.0)
    false_positive_risk: float = Field(default=0.0, ge=0.0, le=1.0)


class RuleCandidate(BaseModel):
    id: str
    detection_spec_id: str
    candidate_type: CandidateType
    sigma_rule: SigmaRule
    score: CandidateScore
    passed_static_validation: bool = False
