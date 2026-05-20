"""API request and response schemas for pipeline endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReportIngestRequest(BaseModel):
    """Request schema for POST /v1/reports:ingest."""

    source_type: Literal["txt", "pdf"] = Field(description="Report source type")
    content: str = Field(min_length=1, description="Report text content")
    external_ref: str | None = Field(default=None, description="External reference ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ReportIngestResponse(BaseModel):
    """Response schema for POST /v1/reports:ingest."""

    report_id: str = Field(description="Generated report ID")
    status: Literal["ingested"] = Field(description="Ingestion status")
    trace_id: str = Field(description="Trace ID for observability")


class PipelineRunRequest(BaseModel):
    """Request schema for POST /v1/pipeline:run."""

    report_id: str = Field(description="Report ID to process")
    profile: Literal["strict", "balanced", "exploratory"] = Field(
        default="balanced", description="Profile for KPI thresholds"
    )
    idempotency_key: str | None = Field(default=None, description="Optional idempotency key")


class PipelineRunResponse(BaseModel):
    """Response schema for POST /v1/pipeline:run."""

    run_id: str = Field(description="Pipeline run ID")
    status: Literal["ok", "abstain", "failed"] = Field(description="Run status")
    abstain: bool = Field(description="Whether pipeline abstained")
    stage: str | None = Field(default=None, description="Last completed stage")
    abstain_code: str | None = Field(default=None, description="Abstain code if applicable")
    reason: str | None = Field(default=None, description="Abstain or failure reason")
    detection_spec_id: str | None = Field(default=None, description="DetectionSpec ID if generated")
    rule_id: str | None = Field(default=None, description="Rule ID if generated")
    canary: dict[str, Any] | None = Field(default=None, description="Canary decision if applicable")
