"""Review API routes for human decision recording and export checks."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.schemas.review import ReviewDecision, ReviewRequest
from de_forge.services.export_eligibility import (
    ExportBlockedReason,
    ExportEligibilityService,
    SqlAlchemyExportEligibilityRepository,
)
from de_forge.services.review import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


class ReviewDecisionRequest(BaseModel):
    rule_id: str
    run_id: str
    decision: str
    reviewer: str
    comments: str


class ReviewDecisionResponse(BaseModel):
    decision_id: str


@router.post("/decision", response_model=ReviewDecisionResponse)
def record_decision(
    request: ReviewDecisionRequest, db: Session = Depends(get_db)
) -> ReviewDecisionResponse:
    service = ReviewService(db)
    try:
        decision_id = service.record_decision(
            rule_id=request.rule_id,
            decision=request.decision,
            reviewer=request.reviewer,
            run_id=request.run_id,
            comments=request.comments,
        )
    except ValueError as exc:
        if str(exc) == "explicit human reviewer is required":
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        raise
    return ReviewDecisionResponse(decision_id=decision_id)


class ExportCheckRequest(BaseModel):
    run_id: str


@router.post("/assert-export")
def assert_export(request: ExportCheckRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    repository = SqlAlchemyExportEligibilityRepository(db)
    run = repository.get_run(request.run_id)
    rule_id = getattr(run, "rule_id", None) if run is not None else ""
    try:
        ExportEligibilityService(repository).assert_exportable(
            run_id=request.run_id, rule_id=rule_id if isinstance(rule_id, str) else ""
        )
    except ExportBlockedReason as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"status": "ok"}


@router.post("", response_model=ReviewDecision)
def decide_review(request: ReviewRequest) -> ReviewDecision:
    return ReviewService().decide(request)


@router.get("/queue")
def review_queue() -> dict[str, list[dict[str, str]]]:
    return {"items": []}
