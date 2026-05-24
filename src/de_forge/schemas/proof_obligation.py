from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ProofObligationType(StrEnum):
    DETECTS_REPORT_BEHAVIOR = "detects_report_behavior"
    NOT_OVERBROAD = "not_overbroad"
    TELEMETRY_FIELDS_EXIST = "telemetry_fields_exist"
    CITATION_FAITHFUL = "citation_faithful"


class ProofObligationStatus(StrEnum):
    PROVEN = "proven"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ProofObligation(BaseModel):
    run_id: str
    rule_candidate_id: str
    claim_type: ProofObligationType
    claim_text: str
    required_artifact_types: list[str] = Field(min_length=1)
    status: ProofObligationStatus = ProofObligationStatus.UNKNOWN
    justification: str | None = None
