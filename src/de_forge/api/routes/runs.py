from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.schemas.run import RunMode, RunSummary
from de_forge.services.orchestrator import Orchestrator
from de_forge.services.retrieval_audit import RetrievalAuditService

router = APIRouter(prefix="/runs", tags=["runs"])


class GoldenRunRequest(BaseModel):
    report_id: str
    report_text: str
    mode: RunMode


@router.post("/golden", response_model=RunSummary)
def start_golden_run(request: GoldenRunRequest) -> RunSummary:
    return Orchestrator().run_golden_path(request.report_id, request.report_text, request.mode)


@router.get("")
def list_runs() -> dict[str, list[dict[str, str]]]:
    return {
        "items": [
            {
                "run_id": "run_1",
                "state": "awaiting_review",
                "mode": "auto",
            }
        ]
    }


@router.get("/{run_id}")
def run_detail(run_id: str) -> dict[str, str]:
    return {
        "run_id": run_id,
        "state": "awaiting_review",
        "stage": "review",
    }


@router.get("/{run_id}/evidence")
def run_evidence(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return RetrievalAuditService(db).get_run_evidence_lineage(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{run_id}/spec")
def run_spec(run_id: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "telemetry_requirements": ["sysmon_eid_1", "security_4688"],
    }


@router.get("/{run_id}/portfolio")
def run_portfolio(run_id: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "items": [
            {
                "candidate_id": "candidate_1",
                "profile": "high_precision",
                "proof_status": "proven",
            }
        ],
    }


@router.get("/{run_id}/validation")
def run_validation(run_id: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "static_valid": True,
        "dynamic_score": 0.96,
    }
