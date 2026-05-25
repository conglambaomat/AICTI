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
from de_forge.db.session import check_database_connection, engine
from de_forge.services.schema_guard import SchemaContractError, SchemaGuard

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

    schema_check = "failed"
    try:
        check_database_connection()
        database_status = "connected"
        database_check = "ok"
    except Exception:
        database_status = "disconnected"
        database_check = "failed"
        errors.append("database_probe_failed")

    if database_check == "ok":
        try:
            SchemaGuard(engine).assert_contract_current()
            schema_check = "ok"
        except SchemaContractError:
            errors.append("schema_contract_drift")
        except Exception:
            errors.append("schema_probe_failed")

    readiness = "ready" if database_check == "ok" and schema_check == "ok" else "not_ready"
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
            "schema": schema_check,
        },
        "errors": errors,
        "run_id": run_id,
        "trace_id": trace_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "uptime_seconds": int(monotonic() - _started_at),
        "policy": {
            "human_review_required_for_export": True,
            "detection_spec_required": True,
            "proof_obligation_required": True,
            "citation_exact_required": True,
            "raw_report_to_rule_forbidden": True,
            "agent_loops_bounded": True,
        },
        "details": {
            "db_probe": "select_1" if database_check == "ok" else None,
            "schema_guard": "current" if schema_check == "ok" else "drift_or_unavailable",
            "lifecycle": {
                "state": "running",
                "mode": "auto",
                "gate": "operational",
            },
        },
    }
