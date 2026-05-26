"""Pipeline API routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import EvidenceSpan as EvidenceSpanModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.models import PipelineRunRecord as PipelineRunRecordModel
from de_forge.models import Report as ReportModel
from de_forge.models import ReportChunk as ReportChunkModel
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
from de_forge.services.ingestion import IngestionService
from de_forge.services.orchestrator import PipelineOrchestrator, PipelineTransitionError
from de_forge.services.review import ExportBlockedError, ReviewService
from de_forge.services.schema_guard import assert_schema_contract_current

router = APIRouter(prefix="/v1", tags=["pipeline"])
seed_router = APIRouter(prefix="/v1", tags=["pipeline-seed"])
legacy_router = APIRouter(tags=["pipeline-legacy"])


@router.post("/reports:ingest", response_model=ReportIngestResponse, status_code=201)
async def ingest_report(
    payload: ReportIngestRequest, db: Session = Depends(get_db)
) -> ReportIngestResponse:
    assert_schema_contract_current(db)
    if payload.source_type == "pdf":
        raise HTTPException(status_code=415, detail="PDF ingestion is not supported")

    try:
        result = IngestionService(db).ingest(
            source_type=payload.source_type,
            filename=payload.external_ref or "inline-report.txt",
            content_bytes=payload.content.encode("utf-8"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportIngestResponse(
        report_id=result.report_id,
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
        chunk_count=len(result.chunks),
    )


@router.post("/pipeline:run", response_model=PipelineRunResponse)
async def run_pipeline(
    payload: PipelineRunRequest, db: Session = Depends(get_db)
) -> PipelineRunResponse | JSONResponse:
    assert_schema_contract_current(db)
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

    orchestrator = PipelineOrchestrator(db)
    try:
        record = orchestrator.run_report_pipeline(
            report_id=payload.report_id,
            run_id=run_id,
        )
    except PipelineTransitionError as exc:
        failed_record = (
            db.query(PipelineRunRecordModel)
            .filter(PipelineRunRecordModel.run_id == run_id)
            .first()
        )
        if failed_record is not None and failed_record.status == "abstain":
            detection_spec = db.get(DetectionSpecModel, failed_record.detection_spec_id)
            return PipelineRunResponse(
                run_id=run_id,
                status=failed_record.status,
                abstain=True,
                stage=failed_record.stage,
                abstain_code=detection_spec.abstain_code if detection_spec else None,
                reason=(
                    detection_spec.abstain_human_message or detection_spec.abstain_context
                    if detection_spec
                    else str(exc)
                ),
                detection_spec_id=failed_record.detection_spec_id,
            )
        failed = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message=str(exc),
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        ).model_dump()
        failed["status"] = failed_record.status if failed_record is not None else "failed"
        status_code = 400
        if failed_record is not None:
            failed["stage"] = failed_record.stage
            failed["detection_spec_id"] = failed_record.detection_spec_id
            failed["rule_id"] = failed_record.rule_id
            if failed_record.stage == "report_not_found":
                status_code = 404
        return JSONResponse(status_code=status_code, content=failed)

    if record.status == "abstain":
        detection_spec = db.get(DetectionSpecModel, record.detection_spec_id)
        return PipelineRunResponse(
            run_id=run_id,
            status=record.status,
            abstain=True,
            stage=record.stage,
            abstain_code=detection_spec.abstain_code if detection_spec else None,
            reason=(
                detection_spec.abstain_human_message or detection_spec.abstain_context
                if detection_spec
                else None
            ),
            detection_spec_id=record.detection_spec_id,
        )

    return PipelineRunResponse(
        run_id=run_id,
        status=record.status,
        abstain=False,
        stage=record.stage,
        detection_spec_id=record.detection_spec_id,
        rule_id=record.rule_id,
    )


@seed_router.post("/pipeline:seed", status_code=201)
async def seed_pipeline_run_data(db: Session = Depends(get_db)) -> dict[str, str]:
    assert_schema_contract_current(db)
    spec_id = f"spec_{uuid4().hex[:12]}"
    rule_id = f"rule_{uuid4().hex[:12]}"
    report_id = f"report_{uuid4().hex[:12]}"
    chunk_id = f"chunk_{uuid4().hex[:12]}"
    evidence_id = f"ev_{uuid4().hex[:12]}"
    now = datetime.now(UTC).isoformat()

    db.add(
        ReportModel(
            id=report_id,
            source_type="txt",
            source_uri="seed://pipeline",
            title="Seed pipeline report",
            raw_text="PowerShell launch behavior observed",
            content_hash=f"seed-{report_id}",
            metadata_json="{}",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    db.add(
        ReportChunkModel(
            id=chunk_id,
            report_id=report_id,
            chunk_index=0,
            section_title=None,
            chunk_text="PowerShell launch behavior observed",
            char_start=0,
            char_end=35,
            chunk_type="paragraph",
            created_at=now,
        )
    )
    db.add(
        EvidenceSpanModel(
            id=evidence_id,
            report_id=report_id,
            chunk_id=chunk_id,
            quote="PowerShell launch behavior observed",
            char_start=0,
            char_end=35,
            supports_claim="PowerShell launch behavior observed",
            confidence=0.9,
            created_by_agent="seed",
            run_id=f"seed-run-{spec_id}",
            created_at=now,
        )
    )
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id=report_id,
            spec_payload=f'{{"report_id":"{report_id}","behavior_rules":[{{"evidence":["{evidence_id}"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect encoded powershell"}}],"false_positive_hypotheses":["admin scripts"],"test_plan":"seed","evidence_ids":["{evidence_id}"],"behavior_ids":["behavior-1"],"detection_strategy":"detect encoded powershell","analytic":"powershell command line analytic","data_component":"process creation","allowed_telemetry_fields":["CommandLine","Image"],"rationale_traceability":["{evidence_id}"]}}',
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
            created_at=now,
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


@seed_router.post("/pipeline:seed-abstain", status_code=201)
async def seed_pipeline_abstain_data(db: Session = Depends(get_db)) -> dict[str, str]:
    assert_schema_contract_current(db)
    spec_id = f"spec_{uuid4().hex[:12]}"
    report_id = f"report_{uuid4().hex[:12]}"
    chunk_id = f"chunk_{uuid4().hex[:12]}"
    evidence_id = f"ev_{uuid4().hex[:12]}"
    now = datetime.now(UTC).isoformat()
    db.add(
        ReportModel(
            id=report_id,
            source_type="txt",
            source_uri="seed://pipeline",
            title="Seed pipeline report",
            raw_text="PowerShell launch behavior observed",
            content_hash=f"seed-{report_id}",
            metadata_json="{}",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    db.add(
        ReportChunkModel(
            id=chunk_id,
            report_id=report_id,
            chunk_index=0,
            section_title=None,
            chunk_text="PowerShell launch behavior observed",
            char_start=0,
            char_end=35,
            chunk_type="paragraph",
            created_at=now,
        )
    )
    db.add(
        EvidenceSpanModel(
            id=evidence_id,
            report_id=report_id,
            chunk_id=chunk_id,
            quote="PowerShell launch behavior observed",
            char_start=0,
            char_end=35,
            supports_claim="No quote-backed behavior found",
            confidence=0.1,
            created_by_agent="seed",
            run_id=f"seed-run-{spec_id}",
            created_at=now,
        )
    )
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


@router.post("/pipeline:approve", response_model=None, status_code=201)
async def approve_rule_for_export(
    rule_id: str,
    run_id: str,
    reviewer: str = "api-reviewer",
    db: Session = Depends(get_db),
) -> dict[str, str] | JSONResponse:
    record = _resolve_run_record(db, run_id)
    if record is None or record.rule_id != rule_id:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})

    service = ReviewService(db)
    decision_id = service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer=reviewer,
        run_id=run_id,
        comments="pipeline approval helper",
    )
    return {"decision_id": decision_id}


@router.post("/pipeline:reject", response_model=None, status_code=201)
async def reject_rule_for_export(
    rule_id: str,
    run_id: str,
    reviewer: str = "api-reviewer",
    db: Session = Depends(get_db),
) -> dict[str, str] | JSONResponse:
    record = _resolve_run_record(db, run_id)
    if record is None or record.rule_id != rule_id:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})

    service = ReviewService(db)
    decision_id = service.record_decision(
        rule_id=rule_id,
        decision="rejected",
        reviewer=reviewer,
        run_id=run_id,
        comments="pipeline rejection helper",
    )
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
    assert_schema_contract_current(db)
    record = _resolve_run_record(db, payload.run_id)
    rule_id = record.rule_id if record is not None else None
    if rule_id is None:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})

    service = ReviewService(db)
    decision_id = service.record_decision(
        rule_id=rule_id,
        decision=payload.decision,
        reviewer=payload.reviewer,
        run_id=payload.run_id,
        comments=payload.comments,
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
    assert_schema_contract_current(db)
    record = _resolve_run_record(db, payload.run_id)
    rule_id = record.rule_id if record is not None else None
    if rule_id is None:
        return JSONResponse(status_code=404, content={"detail": "Run mapping not found"})

    service = ReviewService(db)
    try:
        service.assert_can_export(rule_id=rule_id, rule_status=record.stage or "", run_id=payload.run_id)
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
async def legacy_run_pipeline(
    payload: PipelineRunRequest, db: Session = Depends(get_db)
) -> PipelineRunResponse | JSONResponse:
    return await run_pipeline(payload, db=db)


@legacy_router.post("/review/decision", response_model=None, status_code=201)
async def legacy_review_decision(
    payload: ReviewRequest, db: Session = Depends(get_db)
) -> ReviewResponse | JSONResponse:
    return await create_review(payload, db=db)


@legacy_router.post("/review/assert-export", response_model=None)
async def legacy_assert_export(
    payload: ExportSigmaRequest, db: Session = Depends(get_db)
) -> ExportSigmaResponse | JSONResponse:
    return await export_sigma(payload, db=db)


@legacy_router.post("/ingest", response_model=ReportIngestResponse, status_code=201)
async def legacy_ingest(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ReportIngestResponse:
    assert_schema_contract_current(db)
    filename = file.filename or "unknown"
    if filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="PDF ingestion is not supported")

    content_bytes = await file.read()
    try:
        result = IngestionService(db).ingest(
            source_type="txt",
            filename=filename,
            content_bytes=content_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportIngestResponse(
        report_id=result.report_id,
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
        chunk_count=len(result.chunks),
    )
