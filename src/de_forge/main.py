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
from de_forge.api.routes.pipeline import seed_router as pipeline_seed_router
from de_forge.api.routes.review import router as review_router
from de_forge.core.config import REQUIRED_OPENAI_BASE_URL, REQUIRED_OPENAI_MODEL, Settings, settings
from de_forge.db.session import check_database_connection, engine
from de_forge.services.schema_guard import SchemaContractError, SchemaGuard

_started_at = monotonic()


async def build_health_payload(
    fastapi_app: FastAPI | None = None,
    app_settings: Settings = settings,
) -> dict[str, object]:
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
        "version": fastapi_app.version if fastapi_app else "0.1.0",
        "env": app_settings.env,
        "model": app_settings.openai_model,
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


async def health() -> dict[str, object]:
    return await build_health_payload()


def create_app(app_settings: Settings = settings) -> FastAPI:
    """Create the FastAPI application."""
    fastapi_app = FastAPI(
        title="DE-Forge",
        description="Evidence-Grounded AI-assisted Detection Rule Generation",
        version="0.1.0",
    )

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fastapi_app.include_router(pipeline_router)
    if app_settings.enable_dev_seed_routes and app_settings.env in {"development", "test"}:
        fastapi_app.include_router(pipeline_seed_router)
    fastapi_app.include_router(pipeline_legacy_router)
    fastapi_app.include_router(ingestion_router)
    fastapi_app.include_router(review_router)
    fastapi_app.include_router(api_router)

    @fastapi_app.get("/")
    async def root() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "service": "DE-Forge", "env": app_settings.env}

    @fastapi_app.get("/ready")
    async def ready() -> dict[str, object]:
        health_payload = await build_health_payload(fastapi_app, app_settings)
        raw_checks = health_payload["checks"]
        raw_errors = health_payload["errors"]
        if not isinstance(raw_checks, dict) or not isinstance(raw_errors, list):
            raise TypeError("invalid health payload")
        checks = dict(raw_checks)
        errors = list(raw_errors)
        seed_routes_check = (
            "failed"
            if app_settings.enable_dev_seed_routes
            and app_settings.env not in {"development", "test"}
            else "ok"
        )
        provider_errors: list[str] = []
        if app_settings.env == "production":
            if not app_settings.openai_api_key:
                provider_errors.append("provider_config_missing")
            if app_settings.openai_model != REQUIRED_OPENAI_MODEL:
                provider_errors.append("provider_model_policy_mismatch")
            if app_settings.openai_base_url != REQUIRED_OPENAI_BASE_URL:
                provider_errors.append("provider_base_url_policy_mismatch")
        provider_config_check = "failed" if provider_errors else "ok"
        checks["seed_routes"] = seed_routes_check
        checks["provider_config"] = provider_config_check
        if seed_routes_check == "failed":
            errors.append("seed_routes_enabled_outside_dev")
        errors.extend(provider_errors)
        is_ready = (
            bool(health_payload["ready"])
            and seed_routes_check == "ok"
            and provider_config_check == "ok"
        )
        return {
            "ready": is_ready,
            "readiness": "ready" if is_ready else "not_ready",
            "checks": checks,
            "errors": errors,
        }

    @fastapi_app.get("/health")
    async def app_health() -> dict[str, object]:
        return await build_health_payload(fastapi_app, app_settings)

    return fastapi_app


app = create_app()
