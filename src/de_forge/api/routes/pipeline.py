"""Pipeline orchestration API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.services.orchestrator import PipelineOrchestrator, PipelineTransitionError

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineRunRequest(BaseModel):
    detection_spec_id: str


class PipelineRunResponse(BaseModel):
    state: str


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(request: PipelineRunRequest, db: Session = Depends(get_db)) -> PipelineRunResponse:
    orchestrator = PipelineOrchestrator(db)
    try:
        final_state = orchestrator.run_pipeline(request.detection_spec_id)
    except PipelineTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PipelineRunResponse(state=final_state.value)
