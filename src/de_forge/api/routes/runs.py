from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.schemas.run import RunMode, RunSummary
from de_forge.services.orchestrator import Orchestrator
from de_forge.services.retrieval_audit import RetrievalAuditService
from de_forge.services.run_state import RunStateService

router = APIRouter(prefix="/runs", tags=["runs"])


class GoldenRunRequest(BaseModel):
    report_id: str
    report_text: str
    mode: RunMode


@router.post("/golden", response_model=RunSummary)
def start_golden_run(request: GoldenRunRequest) -> RunSummary:
    return Orchestrator().run_golden_path(request.report_id, request.report_text, request.mode)


@router.get("")
def list_runs(db: Session = Depends(get_db)) -> dict[str, list[dict[str, object]]]:
    return RunStateService(db).list_runs()


@router.get("/{run_id}")
def run_detail(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    detail = RunStateService(db).get_run_detail(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return detail


@router.get("/{run_id}/evidence")
def run_evidence(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        lineage = RetrievalAuditService(db).get_run_evidence_lineage(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not lineage["items"] and RunStateService(db).get_run_detail(run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return lineage


@router.get("/{run_id}/spec")
def run_spec(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    spec = RunStateService(db).get_run_spec(run_id)
    if spec is None:
        raise HTTPException(status_code=404, detail="Run spec not found")
    return spec


@router.get("/{run_id}/portfolio")
def run_portfolio(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    portfolio = RunStateService(db).get_run_portfolio(run_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Run portfolio not found")
    return portfolio


@router.get("/{run_id}/validation")
def run_validation(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    validation = RunStateService(db).get_run_validation(run_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Run validation not found")
    return validation
