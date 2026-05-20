"""Schemas for structured abstain decisions."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AbstainCode = Literal[
    "NO_EVIDENCE",
    "NO_EVIDENCE_BACKED_BEHAVIOR",
    "NO_TELEMETRY",
    "CVE_ONLY_NO_BEHAVIOR",
    "TOOL_NAME_ONLY",
    "OVERBROAD_AFTER_REFINEMENT",
    "UNSAFE_GENERATION",
]


class AbstainDecision(BaseModel):
    """Structured abstain decision with mandatory code, context, and human message."""

    model_config = ConfigDict(extra="forbid")

    abstain_code: AbstainCode
    abstain_context: str = Field(min_length=1)
    human_message: str = Field(min_length=1)

    @field_validator("abstain_context", "human_message")
    @classmethod
    def validate_strings_not_blank(cls, value: str) -> str:
        """Ensure abstain_context and human_message are not empty or whitespace-only."""
        if not value.strip():
            raise ValueError("field must not be empty or whitespace-only")
        return value
