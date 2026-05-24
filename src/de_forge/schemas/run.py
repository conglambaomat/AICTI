from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class RunMode(StrEnum):
    AUTO = "auto"
    CAUTIOUS = "cautious"


class RunState(StrEnum):
    CREATED = "created"
    INGESTED = "ingested"
    EVIDENCE_READY = "evidence_ready"
    DETECTION_SPEC_READY = "detection_spec_ready"
    DETECTION_SPEC_VERIFIED = "detection_spec_verified"
    RULE_CANDIDATES_READY = "rule_candidates_ready"
    VALIDATED = "validated"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ABSTAINED = "abstained"
    FAILED = "failed"


class RunSummary(BaseModel):
    id: str
    mode: RunMode
    state: RunState
    report_id: str
