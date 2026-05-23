from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from de_forge.schemas.run import RunMode, RunSummary
from de_forge.services.orchestrator import Orchestrator

router = APIRouter(prefix="/runs", tags=["runs"])


class GoldenRunRequest(BaseModel):
    report_id: str
    report_text: str
    mode: RunMode


@router.post("/golden", response_model=RunSummary)
def start_golden_run(request: GoldenRunRequest) -> RunSummary:
    return Orchestrator().run_golden_path(request.report_id, request.report_text, request.mode)
