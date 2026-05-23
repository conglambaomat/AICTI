from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from de_forge.schemas.detection_spec import DetectionSpec


class Citation(BaseModel):
    chunk_id: str
    quote: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)


class AgentMetadata(BaseModel):
    model: str
    prompt_version: str
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: float | None = Field(default=None, ge=0.0)


class AgentOutputEnvelope(BaseModel):
    run_id: str
    agent_name: str
    input_artifact_ids: list[str]
    output: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)
    abstain: bool = False
    abstain_reason: str | None = None
    metadata: AgentMetadata


class RuleGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detection_spec: DetectionSpec
    target_format: Literal["sigma", "kql"]


__all__ = [
    "Citation",
    "AgentMetadata",
    "AgentOutputEnvelope",
    "RuleGenerationRequest",
]
