from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class FeedbackDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"


class ReviewFeedback(BaseModel):
    rule_candidate_id: str
    decision: FeedbackDecision
    reason: str
    pattern: str
