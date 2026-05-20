"""Schemas for DetectionSpec-first detection contracts."""

from pydantic import BaseModel, Field


class BehaviorRule(BaseModel):
    """Evidence-grounded behavior rule contract."""

    evidence: list[str] = Field(min_length=1)
    attack_ids: list[str] = Field(min_length=1)
    required_telemetry: list[str] = Field(min_length=1)
    detection_logic: str = Field(min_length=1)


class DetectionSpec(BaseModel):
    """Mandatory intermediate representation before rule generation."""

    report_id: str = Field(min_length=1)
    behavior_rules: list[BehaviorRule] = Field(min_length=1)
    false_positive_hypotheses: list[str] = Field(min_length=1)
    test_plan: str = Field(min_length=1)
