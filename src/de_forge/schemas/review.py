from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    ABSTAIN = "abstain"


class ReviewRequest(BaseModel):
    run_id: str
    rule_candidate_id: str
    action: ReviewAction
    reviewer_notes: str


class ReviewDecision(BaseModel):
    run_id: str
    rule_candidate_id: str
    action: ReviewAction
    reviewer_notes: str
    export_allowed: bool
