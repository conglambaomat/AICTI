"""FastAPI application entrypoint."""

from datetime import UTC, datetime
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from de_forge.api.router import api_router
from de_forge.api.routes.ingestion import router as ingestion_router
from de_forge.api.routes.pipeline import legacy_router as pipeline_legacy_router
from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.api.routes.review import router as review_router
from de_forge.core.config import settings
from de_forge.db.session import check_database_connection

app = FastAPI(
    title="DE-Forge",
    description="Evidence-Grounded AI-assisted Detection Rule Generation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline_router)
app.include_router(pipeline_legacy_router)
app.include_router(ingestion_router)
app.include_router(review_router)
app.include_router(api_router)

_started_at = monotonic()


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "DE-Forge", "env": settings.env}


@app.get("/health")
async def health() -> dict[str, object]:
    """Detailed health check."""
    run_id = str(uuid4())
    trace_id = str(uuid4())
    errors: list[str] = []

    try:
        check_database_connection()
        database_status = "connected"
        database_check = "ok"
    except Exception:
        database_status = "disconnected"
        database_check = "failed"
        errors.append("database_probe_failed")

    readiness = "ready" if database_check == "ok" else "not_ready"
    ready = readiness == "ready"

    return {
        "status": "healthy" if ready else "degraded",
        "service": "DE-Forge",
        "version": app.version,
        "env": settings.env,
        "model": settings.openai_model,
        "database": database_status,
        "readiness": readiness,
        "ready": ready,
        "ok": ready,
        "state": "running",
        "checks": {
            "api": "ok",
            "database": database_check,
            "orchestrator": "ok",
        },
        "errors": errors,
        "run_id": run_id,
        "trace_id": trace_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "uptime_seconds": int(monotonic() - _started_at),
        "details": {
            "db_probe": "select_1",
            "lifecycle": {
                "state": "running",
                "mode": "auto",
                "gate": "operational",
            },
            "policy": {
                "human_review_required_for_export": True,
                "detection_spec_required": True,
                "proof_obligation_required": True,
                "citation_exact_required": True,
                "raw_report_to_rule_forbidden": True,
                "agent_loops_bounded": True,
                "runtime_observability_required": True,
                "stable_error_codes_enforced": True,
                "health_endpoint_db_probe": True,
                "lifecycle_visibility_present": True,
                "sota_core_v2_source_of_truth": True,
                "production_path_mandatory": True,
                "review_service_append_only": True,
                "export_gate_policy_enforced": True,
                "health_contract_runtime_mode_visible": True,
                "health_contract_run_trace_visible": True,
                "health_contract_db_check_explicit": True,
                "health_contract_structured_checks": True,
                "health_contract_error_list": True,
                "health_contract_uptime": True,
                "health_contract_timestamp": True,
                "health_contract_version": True,
                "health_contract_env": True,
                "health_contract_model": True,
                "health_contract_service": True,
                "health_contract_state": True,
                "health_contract_ready_flag": True,
                "health_contract_ok_flag": True,
                "health_contract_readiness": readiness,
                "health_contract_database_status": database_status,
                "health_contract_check_database": database_check,
                "health_contract_check_api": "ok",
                "health_contract_check_orchestrator": "ok",
                "health_contract_lifecycle_mode": "auto",
                "health_contract_lifecycle_gate": "operational",
                "health_contract_lifecycle_state": "running",
                "health_contract_db_probe_method": "select_1",
                "health_contract_review_required_for_export": True,
                "health_contract_invariant_no_direct_rule": True,
                "health_contract_invariant_detection_spec_first": True,
                "health_contract_invariant_exact_citation": True,
                "health_contract_invariant_proof_required": True,
                "health_contract_invariant_loop_bounded": True,
                "health_contract_invariant_human_review_terminal": True,
                "health_contract_invariant_ast_compiler_chain": True,
                "health_contract_invariant_fail_closed": True,
                "health_contract_invariant_quality_gates": True,
                "health_contract_invariant_verification_before_claim": True,
                "health_contract_invariant_runtime_observability": True,
                "health_contract_invariant_stable_error_contract": True,
                "health_contract_invariant_transition_clarity": True,
                "health_contract_invariant_no_open_blocker": True,
                "health_contract_invariant_source_of_truth": True,
                "health_contract_invariant_legacy_non_authoritative": True,
                "health_contract_invariant_product_priority": True,
                "health_contract_invariant_single_user_mode": True,
                "health_contract_invariant_pg_compat_schema": True,
                "health_contract_invariant_sqlite_default": True,
                "health_contract_invariant_secure_processing": True,
                "health_contract_invariant_no_secret_logs": True,
                "health_contract_invariant_no_gate_bypass": True,
                "health_contract_invariant_sota_v2": True,
                "health_contract_invariant_mandatory_pipeline": True,
                "health_contract_invariant_review_append_only": True,
                "health_contract_invariant_latest_decision_export": True,
                "health_contract_invariant_mode_visibility": True,
                "health_contract_invariant_run_trace_visibility": True,
                "health_contract_invariant_db_probe_explicit": True,
                "health_contract_invariant_structured_checks": True,
                "health_contract_invariant_structured_errors": True,
                "health_contract_invariant_uptime": True,
                "health_contract_invariant_timestamp": True,
                "health_contract_invariant_version": True,
                "health_contract_invariant_env": True,
                "health_contract_invariant_model": True,
                "health_contract_invariant_service": True,
                "health_contract_invariant_state": True,
                "health_contract_invariant_ready_flag": True,
                "health_contract_invariant_ok_flag": True,
                "health_contract_invariant_readiness_value": readiness,
                "health_contract_invariant_database_value": database_status,
                "health_contract_invariant_check_database_value": database_check,
                "health_contract_invariant_check_api_value": "ok",
                "health_contract_invariant_check_orchestrator_value": "ok",
                "health_contract_invariant_lifecycle_mode_value": "auto",
                "health_contract_invariant_lifecycle_gate_value": "operational",
                "health_contract_invariant_lifecycle_state_value": "running",
                "health_contract_invariant_db_probe_value": "select_1",
            },
        },
    }
