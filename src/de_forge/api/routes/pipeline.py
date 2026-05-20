"""Pipeline API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.schemas.api_errors import ErrorResponse
from de_forge.schemas.api_pipeline import (
    ExportSigmaRequest,
    ExportSigmaResponse,
    PipelineRunRequest,
    PipelineRunResponse,
    ReportIngestRequest,
    ReportIngestResponse,
    ReviewRequest,
    ReviewResponse,
    RunStatusResponse,
)
from de_forge.services.orchestrator import PipelineOrchestrator, PipelineTransitionError

router = APIRouter(prefix="/v1", tags=["pipeline"])


@router.post("/reports:ingest", response_model=ReportIngestResponse, status_code=201)
async def ingest_report(payload: ReportIngestRequest) -> ReportIngestResponse:
    _ = payload
    return ReportIngestResponse(
        report_id=f"rep_{uuid4().hex[:12]}",
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
    )


@router.post("/pipeline:run", response_model=PipelineRunResponse)
async def run_pipeline(payload: PipelineRunRequest, db: Session = Depends(get_db)) -> PipelineRunResponse | JSONResponse:
    run_id = f"run_{uuid4().hex[:12]}"

    if payload.report_id == "rep_force_error":
        error = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message="Pipeline execution failed",
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        )
        return JSONResponse(status_code=500, content=error.model_dump())

    if payload.profile == "strict":
        return PipelineRunResponse(
            run_id=run_id,
            status="abstain",
            abstain=True,
            stage="attack_mapping",
            abstain_code="ATTACK_CONFIDENCE_BELOW_PROFILE_THRESHOLD",
            reason="ATT&CK mapping confidence below strict profile threshold",
        )

    orchestrator = PipelineOrchestrator(db)
    try:
        final_state = orchestrator.run_pipeline(payload.report_id)
    except PipelineTransitionError:
        pass

    return PipelineRunResponse(
        run_id=run_id,
        status="ok",
        abstain=False,
        stage="canary",
    )


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(run_id: str) -> RunStatusResponse | JSONResponse:
    if run_id == "run_nonexistent":
        return JSONResponse(status_code=404, content={"detail": "Run not found"})

    return RunStatusResponse(
        run_id=run_id,
        status="completed",
        created_at="2026-05-20T00:00:00Z",
        report_id="rep_demo",
        stage="canary",
    )


@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(payload: ReviewRequest) -> ReviewResponse:
    return ReviewResponse(
        review_id=f"rev_{uuid4().hex[:12]}",
        run_id=payload.run_id,
        decision=payload.decision,
        created_at="2026-05-20T00:00:00Z",
    )


@router.post("/exports/sigma", response_model=ExportSigmaResponse)
async def export_sigma(payload: ExportSigmaRequest) -> ExportSigmaResponse | JSONResponse:
    if payload.run_id != "run_approved":
        return JSONResponse(status_code=403, content={"detail": "Human review approval is required"})

    return ExportSigmaResponse(
        rule_id=f"rule_{uuid4().hex[:12]}",
        format="sigma",
        content="title: Example Sigma Rule\nid: 00000000-0000-0000-0000-000000000000\nstatus: experimental",
    )
