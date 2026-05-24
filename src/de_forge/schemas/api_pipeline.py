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
    chunk_count: int = Field(description="Number of persisted report chunks")


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


class RunStatusResponse(BaseModel):
    """Response schema for GET /v1/runs/{run_id}."""

    run_id: str = Field(description="Pipeline run ID")
    status: Literal["pending", "running", "completed", "failed"] = Field(description="Run status")
    created_at: str = Field(description="ISO 8601 timestamp of run creation")
    report_id: str | None = Field(default=None, description="Associated report ID")
    stage: str | None = Field(default=None, description="Current or last completed stage")
    detection_spec_id: str | None = Field(default=None, description="DetectionSpec ID if generated")
    rule_id: str | None = Field(default=None, description="Rule ID if generated")


class ReviewRequest(BaseModel):
    """Request schema for POST /v1/reviews."""

    run_id: str = Field(description="Run ID to review")
    reviewer: str = Field(description="Reviewer identifier")
    decision: Literal["approved", "rejected"] = Field(description="Review decision")
    comments: str = Field(description="Review comments")


class ReviewResponse(BaseModel):
    """Response schema for POST /v1/reviews."""

    review_id: str = Field(description="Generated review ID")
    run_id: str = Field(description="Reviewed run ID")
    decision: Literal["approved", "rejected"] = Field(description="Review decision")
    created_at: str = Field(description="ISO 8601 timestamp of review creation")


class ExportSigmaRequest(BaseModel):
    """Request schema for POST /v1/exports/sigma."""

    run_id: str = Field(description="Run ID to export")


class ExportSigmaResponse(BaseModel):
    """Response schema for POST /v1/exports/sigma."""

    rule_id: str = Field(description="Exported rule ID")
    format: Literal["sigma"] = Field(description="Export format")
    content: str = Field(description="Sigma rule YAML content")
