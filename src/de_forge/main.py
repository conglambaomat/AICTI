"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from de_forge.api.routes.ingestion import router as ingestion_router
from de_forge.api.routes.pipeline import legacy_router as pipeline_legacy_router
from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.api.routes.review import router as review_router
from de_forge.core.config import settings

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


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "DE-Forge", "env": settings.env}


@app.get("/health")
async def health() -> dict[str, str]:
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected" if settings.database_url else "not_configured",
        "model": settings.openai_model,
    }
