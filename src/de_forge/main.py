"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
