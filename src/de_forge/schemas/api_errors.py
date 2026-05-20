"""API error response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response for hard-fail outcomes."""

    status: str = Field(default="failed", description="Always 'failed' for errors")
    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    trace_id: str = Field(description="Trace ID for observability")
    run_id: str | None = Field(default=None, description="Run ID if available")
