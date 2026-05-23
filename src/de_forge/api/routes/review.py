"""Review API routes for human decision recording and export checks."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.schemas.review import ReviewDecision, ReviewRequest
from de_forge.services.review import ExportBlockedError, ReviewService

router = APIRouter(prefix="/review", tags=["review"])


class ReviewDecisionRequest(BaseModel):
    rule_id: str
    decision: str
    reviewer: str


class ReviewDecisionResponse(BaseModel):
    decision_id: str


@router.post("/decision", response_model=ReviewDecisionResponse)
def record_decision(
    request: ReviewDecisionRequest, db: Session = Depends(get_db)
) -> ReviewDecisionResponse:
    service = ReviewService(db)
    decision_id = service.record_decision(
        rule_id=request.rule_id,
        decision=request.decision,
        reviewer=request.reviewer,
    )
    return ReviewDecisionResponse(decision_id=decision_id)


class ExportCheckRequest(BaseModel):
    rule_id: str
    rule_status: str


@router.post("/assert-export")
def assert_export(request: ExportCheckRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    service = ReviewService(db)
    try:
        service.assert_can_export(rule_id=request.rule_id, rule_status=request.rule_status)
    except ExportBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@router.post("", response_model=ReviewDecision)
def decide_review(request: ReviewRequest) -> ReviewDecision:
    return ReviewService().decide(request)


@router.get("/queue")
def review_queue() -> dict[str, list[dict[str, str]]]:
    return {
        "items": [
            {
                "run_id": "run_1",
                "rule_candidate_id": "candidate_1",
                "state": "awaiting_review",
            }
        ]
    }
