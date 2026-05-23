from __future__ import annotations

from fastapi import APIRouter

from de_forge.api.routes import metrics, review, runs, ui

api_router = APIRouter(prefix="/api")
api_router.include_router(runs.router)
api_router.include_router(review.router)
api_router.include_router(metrics.router)
api_router.include_router(ui.router)
