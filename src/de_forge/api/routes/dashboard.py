from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary() -> dict[str, dict[str, float]]:
    return {
        "queue": {"pending": 1, "in_review": 1},
        "quality": {"overall": 0.96, "citation": 1.0},
        "throughput": {"runs_24h": 12},
    }
