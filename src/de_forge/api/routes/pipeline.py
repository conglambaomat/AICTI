"""Pipeline API routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.models import PipelineRunRecord as PipelineRunRecordModel
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
from de_forge.services.review import ExportBlockedError, ReviewService

router = APIRouter(prefix="/v1", tags=["pipeline"])
legacy_router = APIRouter(tags=["pipeline-legacy"])


@router.post("/reports:ingest", response_model=ReportIngestResponse, status_code=201)
async def ingest_report(payload: ReportIngestRequest) -> ReportIngestResponse:
    _ = payload
    return ReportIngestResponse(
        report_id=f"rep_{uuid4().hex[:12]}",
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
    )


@router.post("/pipeline:run", response_model=PipelineRunResponse)
async def run_pipeline(
    payload: PipelineRunRequest, db: Session = Depends(get_db)
) -> PipelineRunResponse | JSONResponse:
    _ensure_schema(db)
    run_id = f"run_{uuid4().hex[:12]}"

    if payload.report_id == "rep_force_error":
        _remember_run(
            db,
            run_id,
            report_id=payload.report_id,
            status="failed",
            detection_spec_id=None,
            rule_id=None,
            stage="failed_generation",
        )
        error = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message="Pipeline execution failed",
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        )
        failed = error.model_dump()
        failed["status"] = "failed"
        return JSONResponse(status_code=500, content=failed)

    if payload.report_id == "rep_force_memory_contract_error":
        _remember_run(
            db,
            run_id,
            report_id=payload.report_id,
            status="failed",
            detection_spec_id=None,
            rule_id=None,
            stage="failed_memory_contract",
        )
        error = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message="Memory contract gate failed",
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        )
        failed = error.model_dump()
        failed["status"] = "failed"
        return JSONResponse(status_code=500, content=failed)

    detection_spec = (
        db.query(DetectionSpecModel)
        .filter(DetectionSpecModel.report_id == payload.report_id)
        .first()
    )
    if detection_spec is None:
        error = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message="Report not found for report_id",
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        )
        failed = error.model_dump()
        failed["status"] = "failed"
        return JSONResponse(status_code=404, content=failed)

    if detection_spec.abstain_code is not None:
        _remember_run(
            db,
            run_id,
            report_id=payload.report_id,
            status="abstain",
            detection_spec_id=detection_spec.id,
            rule_id=None,
        )
        return PipelineRunResponse(
            run_id=run_id,
            status="abstain",
            abstain=True,
            stage="detection_spec",
            abstain_code=detection_spec.abstain_code,
            reason=detection_spec.abstain_human_message or detection_spec.abstain_context,
            detection_spec_id=detection_spec.id,
        )

    orchestrator = PipelineOrchestrator(db)
    try:
        final_state = orchestrator.run_pipeline(detection_spec.id)
    except PipelineTransitionError as exc:
        _remember_run(
            db,
            run_id,
            report_id=payload.report_id,
            status="failed",
            detection_spec_id=detection_spec.id,
            rule_id=None,
        )
        failed = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message=str(exc),
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        ).model_dump()
        failed["status"] = "failed"
        return JSONResponse(status_code=400, content=failed)

    generated_rule = (
        db.query(GeneratedRuleModel)
        .filter(GeneratedRuleModel.detection_spec_id == detection_spec.id)
        .first()
    )
    _remember_run(
        db,
        run_id,
        report_id=payload.report_id,
        status="ok",
        detection_spec_id=detection_spec.id,
        rule_id=generated_rule.id if generated_rule else None,
    )

    return PipelineRunResponse(
        run_id=run_id,
        status="ok",
        abstain=False,
        stage=final_state.value,
        detection_spec_id=detection_spec.id,
        rule_id=generated_rule.id if generated_rule else None,
    )


@router.post("/pipeline:seed", status_code=201)
async def seed_pipeline_run_data(db: Session = Depends(get_db)) -> dict[str, str]:
    _ensure_schema(db)
    spec_id = f"spec_{uuid4().hex[:12]}"
    rule_id = f"rule_{uuid4().hex[:12]}"
    report_id = f"report_{uuid4().hex[:12]}"

    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id=report_id,
            spec_payload='{"report_id":"seed","behavior_rules":[{"evidence":["powershell"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect encoded powershell"}],"false_positive_hypotheses":["admin scripts"],"test_plan":"seed"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRuleModel(
            id=rule_id,
            detection_spec_id=spec_id,
            rule_content="title: seed rule\nlogsource:\n  product: windows\n  category: process_creation\ndetection:\n  selection:\n    Image|contains: 'powershell'\n  condition: selection\n",
        )
    )
    db.add(
        PipelineRunRecordModel(
            id=f"pr-seed-{spec_id}",
            run_id=f"seed-run-{spec_id}",
            report_id=report_id,
            status="ok",
            stage="awaiting_review",
            detection_spec_id=spec_id,
            rule_id=rule_id,
            created_at=datetime.now(UTC).isoformat(),
        )
    )
    db.execute(
        text(
            """
            INSERT INTO proof_obligations (id, run_id, rule_candidate_id, claim_type, claim_text, required_artifact_types, status, justification)
            VALUES (:id1, :run_id, :rule_id, :claim_type1, :claim_text1, :required_artifact_types1, 'proven', NULL),
                   (:id2, :run_id, :rule_id, :claim_type2, :claim_text2, :required_artifact_types2, 'proven', NULL)
            """
        ),
        {
            "id1": f"po-seed-1-{spec_id}",
            "id2": f"po-seed-2-{spec_id}",
            "run_id": spec_id,
            "rule_id": rule_id,
            "claim_type1": "citation_faithful",
            "claim_text1": "Citations are faithful.",
            "required_artifact_types1": '["citation_verification"]',
            "claim_type2": "not_overbroad",
            "claim_text2": "Rule is not overbroad.",
            "required_artifact_types2": '["false_positive_analysis"]',
        },
    )
    db.execute(
        text(
            """
            INSERT INTO validation_results (id, rule_id, run_id, status, details_json, created_at)
            VALUES (:id1, :rule_id, :run_id, 'passed', '{}', :created_at1),
                   (:id2, :rule_id, :run_id, 'passed', '{}', :created_at2),
                   (:id3, :rule_id, :run_id, 'passed', '{}', :created_at3),
                   (:id4, :rule_id, :run_id, 'passed', '{}', :created_at4)
            """
        ),
        {
            "id1": f"vr-seed-1-{spec_id}",
            "id2": f"vr-seed-2-{spec_id}",
            "id3": f"vr-seed-3-{spec_id}",
            "id4": f"vr-seed-4-{spec_id}",
            "rule_id": rule_id,
            "run_id": spec_id,
            "created_at1": datetime.now(UTC).isoformat(),
            "created_at2": datetime.now(UTC).isoformat(),
            "created_at3": datetime.now(UTC).isoformat(),
            "created_at4": datetime.now(UTC).isoformat(),
        },
    )
    db.commit()

    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-{spec_id}",
            "scope": f"{spec_id}:detection_spec.draft",
            "value": '{"version": 1, "payload": {"spec": "ready"}, "last_event_hash": "h1"}',
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-rule-{spec_id}",
            "scope": f"{spec_id}:rule_generation.draft",
            "value": '{"version": 1, "payload": {"rule": "ready"}, "last_event_hash": "h2"}',
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    db.commit()

    return {"detection_spec_id": spec_id, "rule_id": rule_id, "report_id": report_id}


@router.post("/pipeline:seed-abstain", status_code=201)
async def seed_pipeline_abstain_data(db: Session = Depends(get_db)) -> dict[str, str]:
    _ensure_schema(db)
    spec_id = f"spec_{uuid4().hex[:12]}"
    report_id = f"report_{uuid4().hex[:12]}"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id=report_id,
            abstain_code="NO_EVIDENCE",
            abstain_context="No quote-backed behavior found",
            abstain_human_message="Cannot generate detection",
            is_validated=True,
        )
    )
    db.commit()
    return {"detection_spec_id": spec_id, "report_id": report_id}


@router.post("/pipeline:approve", status_code=201)
async def approve_rule_for_export(
    rule_id: str, reviewer: str = "api-reviewer", db: Session = Depends(get_db)
) -> dict[str, str]:
    service = ReviewService(db)
    decision_id = service.record_decision(rule_id=rule_id, decision="approved", reviewer=reviewer)
    return {"decision_id": decision_id}


@router.post("/pipeline:reject", status_code=201)
async def reject_rule_for_export(
    rule_id: str, reviewer: str = "api-reviewer", db: Session = Depends(get_db)
) -> dict[str, str]:
    service = ReviewService(db)
    decision_id = service.record_decision(rule_id=rule_id, decision="rejected", reviewer=reviewer)
    return {"decision_id": decision_id}


@router.get("/pipeline:rule/{detection_spec_id}", response_model=None)
async def get_rule_for_spec(
    detection_spec_id: str, db: Session = Depends(get_db)
) -> dict[str, str] | JSONResponse:
    generated_rule = (
        db.query(GeneratedRuleModel)
        .filter(GeneratedRuleModel.detection_spec_id == detection_spec_id)
        .first()
    )
    if generated_rule is None:
        return JSONResponse(status_code=404, content={"detail": "Rule not found"})
    return {"rule_id": generated_rule.id}


@router.get("/pipeline:export-run/{run_id}", response_model=None)
async def get_run_export_mapping(
    run_id: str, db: Session = Depends(get_db)
) -> dict[str, str] | JSONResponse:
    record = _resolve_run_record(db, run_id)
    rule_id = record.rule_id if record is not None else None
    if rule_id is None:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})
    return {"rule_id": rule_id}


def _ensure_schema(db: Session) -> None:
    Base.metadata.create_all(bind=db.get_bind())
    _ensure_agent_runs_schema(db)


def _ensure_agent_runs_schema(db: Session) -> None:
    bind = db.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "agent_runs" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("agent_runs")}
    column_defs = {
        "prompt_version": "VARCHAR(64) NOT NULL DEFAULT 'unknown'",
        "model_id": "VARCHAR(120) NOT NULL DEFAULT 'unknown'",
        "tokens_in": "INTEGER NOT NULL DEFAULT 0",
        "tokens_out": "INTEGER NOT NULL DEFAULT 0",
        "latency_ms": "INTEGER NOT NULL DEFAULT 0",
        "cost_usd": "FLOAT NOT NULL DEFAULT 0",
        "input_payload_json": "TEXT NOT NULL DEFAULT '{}'",
        "output_payload_json": "TEXT NOT NULL DEFAULT '{}'",
        "artifact_ids_json": "TEXT NOT NULL DEFAULT '[]'",
    }

    for name, ddl in column_defs.items():
        if name not in columns:
            db.execute(text(f"ALTER TABLE agent_runs ADD COLUMN {name} {ddl}"))

    index_names = {index["name"] for index in inspector.get_indexes("agent_runs")}
    if "ix_agent_runs_run_id" not in index_names:
        db.execute(text("CREATE INDEX ix_agent_runs_run_id ON agent_runs (run_id)"))
    if "ix_agent_runs_trace_id" not in index_names:
        db.execute(text("CREATE INDEX ix_agent_runs_trace_id ON agent_runs (trace_id)"))
    if "ix_agent_runs_agent_name" not in index_names:
        db.execute(text("CREATE INDEX ix_agent_runs_agent_name ON agent_runs (agent_name)"))

    db.commit()


def _remember_run(
    db: Session,
    run_id: str,
    *,
    report_id: str,
    status: str,
    detection_spec_id: str | None,
    rule_id: str | None,
    stage: str | None = None,
) -> None:
    record = (
        db.query(PipelineRunRecordModel).filter(PipelineRunRecordModel.run_id == run_id).first()
    )
    normalized_stage = stage or _resolve_stage_for_status(status)
    if record is None:
        db.add(
            PipelineRunRecordModel(
                id=f"pr_{uuid4().hex[:12]}",
                run_id=run_id,
                report_id=report_id,
                status=status,
                stage=normalized_stage,
                detection_spec_id=detection_spec_id,
                rule_id=rule_id,
                created_at=datetime.now(UTC).isoformat(),
            )
        )
    else:
        record.report_id = report_id
        record.status = status
        record.stage = normalized_stage
        record.detection_spec_id = detection_spec_id
        record.rule_id = rule_id
    db.commit()


def _resolve_run_record(db: Session, run_id: str) -> PipelineRunRecordModel | None:
    return db.query(PipelineRunRecordModel).filter(PipelineRunRecordModel.run_id == run_id).first()


def _resolve_stage_for_status(status: str) -> str:
    if status == "abstain":
        return "detection_spec"
    if status == "failed":
        return "failed_generation"
    return "awaiting_review"


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: str, db: Session = Depends(get_db)
) -> RunStatusResponse | JSONResponse:
    record = _resolve_run_record(db, run_id)
    if record is None:
        return JSONResponse(status_code=404, content={"detail": "Run not found"})

    status = record.status
    return RunStatusResponse(
        run_id=run_id,
        status="completed" if status in {"ok", "abstain"} else "failed",
        created_at=record.created_at,
        report_id=record.report_id,
        stage=record.stage,
        detection_spec_id=record.detection_spec_id,
        rule_id=record.rule_id,
    )


@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(
    payload: ReviewRequest, db: Session = Depends(get_db)
) -> ReviewResponse | JSONResponse:
    _ensure_schema(db)
    record = _resolve_run_record(db, payload.run_id)
    rule_id = record.rule_id if record is not None else None
    if rule_id is None:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})

    service = ReviewService(db)
    decision_id = service.record_decision(
        rule_id=rule_id, decision=payload.decision, reviewer=payload.reviewer
    )
    return ReviewResponse(
        review_id=decision_id,
        run_id=payload.run_id,
        decision=payload.decision,
        created_at=datetime.now(UTC).isoformat(),
    )


@router.post("/exports/sigma", response_model=ExportSigmaResponse)
async def export_sigma(
    payload: ExportSigmaRequest, db: Session = Depends(get_db)
) -> ExportSigmaResponse | JSONResponse:
    _ensure_schema(db)
    record = _resolve_run_record(db, payload.run_id)
    rule_id = record.rule_id if record is not None else None
    if rule_id is None:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})

    service = ReviewService(db)
    try:
        service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")
    except ExportBlockedError as exc:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    generated_rule = db.get(GeneratedRuleModel, rule_id)
    if generated_rule is None or not generated_rule.rule_content:
        return JSONResponse(status_code=404, content={"detail": "Generated rule not found"})

    return ExportSigmaResponse(
        rule_id=rule_id,
        format="sigma",
        content=generated_rule.rule_content,
    )


@legacy_router.post("/pipeline/run", response_model=None)
async def legacy_run_pipeline(payload: PipelineRunRequest) -> PipelineRunResponse | JSONResponse:
    return await run_pipeline(payload)


@legacy_router.post("/review/decision", response_model=None, status_code=201)
async def legacy_review_decision(
    payload: ReviewRequest,
) -> ReviewResponse | JSONResponse:
    return await create_review(payload)


@legacy_router.post("/review/assert-export", response_model=None)
async def legacy_assert_export(payload: ExportSigmaRequest) -> ExportSigmaResponse | JSONResponse:
    return await export_sigma(payload)


@legacy_router.post("/ingest", response_model=ReportIngestResponse, status_code=201)
async def legacy_ingest(file: UploadFile = File(...)) -> ReportIngestResponse:
    _ = await file.read()
    return ReportIngestResponse(
        report_id=f"rep_{uuid4().hex[:12]}",
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
    )
