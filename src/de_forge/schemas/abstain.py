"""Schemas for structured abstain decisions."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


AbstainCode = Literal[
    "NO_EVIDENCE",
    "NO_TELEMETRY",
    "CVE_ONLY_NO_BEHAVIOR",
    "TOOL_NAME_ONLY",
    "OVERBROAD_AFTER_REFINEMENT",
    "UNSAFE_GENERATION",
]


class AbstainDecision(BaseModel):
    """Structured abstain decision with mandatory code and context."""

    abstain_code: AbstainCode
    context: str = Field(min_length=1)

    @field_validator("context")
    @classmethod
    def validate_context_not_blank(cls, value: str) -> str:
        """Ensure context is not empty or whitespace-only."""
        if not value.strip():
            raise ValueError("context must not be empty or whitespace-only")
        return value
