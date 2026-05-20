"""Schemas for DetectionSpec-first detection contracts."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

ATTACK_ID_PATTERN = re.compile(r"^T\d{4}(?:\.\d{3})?$")
MVP_ALLOWED_ATTACK_IDS = {"T1059.001", "T1059.003", "T1105"}
MVP_ALLOWED_TELEMETRY = {"process_creation"}


class BehaviorRule(BaseModel):
    """Evidence-grounded behavior rule contract."""

    model_config = ConfigDict(extra="forbid")

    evidence: list[str] = Field(min_length=1)
    attack_ids: list[str] = Field(min_length=1)
    required_telemetry: list[str] = Field(min_length=1)
    detection_logic: str = Field(min_length=1)

    @field_validator("evidence", mode="after")
    @classmethod
    def validate_evidence_items(cls, value: list[str]) -> list[str]:
        """Ensure evidence quotes are non-empty after trimming."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("evidence items must not be empty or whitespace-only")
        return cleaned

    @field_validator("attack_ids", mode="after")
    @classmethod
    def validate_attack_ids(cls, value: list[str]) -> list[str]:
        """Ensure ATT&CK IDs match T#### or T####.### formats and are in MVP allowlist."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("attack_ids must not contain empty or whitespace-only values")
        if any(not ATTACK_ID_PATTERN.fullmatch(item) for item in cleaned):
            raise ValueError("attack_ids must match ATT&CK format T#### or T####.###")
        invalid_ids = [item for item in cleaned if item not in MVP_ALLOWED_ATTACK_IDS]
        if invalid_ids:
            raise ValueError(
                f"attack_ids must be in MVP allowlist {sorted(MVP_ALLOWED_ATTACK_IDS)}, "
                f"got invalid: {invalid_ids}"
            )
        return cleaned

    @field_validator("required_telemetry", mode="after")
    @classmethod
    def validate_required_telemetry(cls, value: list[str]) -> list[str]:
        """Ensure telemetry values are normalized, non-empty, and in MVP allowlist."""
        cleaned = [item.strip().lower() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("required_telemetry items must not be empty or whitespace-only")
        invalid_telemetry = [item for item in cleaned if item not in MVP_ALLOWED_TELEMETRY]
        if invalid_telemetry:
            raise ValueError(
                f"required_telemetry must be in MVP allowlist {sorted(MVP_ALLOWED_TELEMETRY)}, "
                f"got invalid: {invalid_telemetry}"
            )
        return cleaned

    @field_validator("detection_logic")
    @classmethod
    def validate_detection_logic(cls, value: str) -> str:
        """Ensure detection logic is not whitespace-only."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("detection_logic must not be empty or whitespace-only")
        return stripped


class DetectionSpec(BaseModel):
    """Mandatory intermediate representation before rule generation."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(min_length=1)
    behavior_rules: list[BehaviorRule] = Field(min_length=1)
    false_positive_hypotheses: list[str] = Field(min_length=1)
    test_plan: str = Field(min_length=1)

    @field_validator("report_id", "test_plan")
    @classmethod
    def validate_critical_strings_not_blank(cls, value: str) -> str:
        """Ensure critical string fields are not whitespace-only."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty or whitespace-only")
        return stripped

    @field_validator("false_positive_hypotheses", mode="after")
    @classmethod
    def validate_hypotheses_items_not_blank(cls, value: list[str]) -> list[str]:
        """Ensure each hypothesis is non-empty after trimming."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("false_positive_hypotheses items must not be empty or whitespace-only")
        return cleaned
