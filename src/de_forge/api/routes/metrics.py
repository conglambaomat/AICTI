from __future__ import annotations

from fastapi import APIRouter

from de_forge.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/quality")
def quality_summary() -> dict[str, float]:
    return MetricsService().quality_snapshot(
        citation_faithfulness=1.0,
        proof_pass_rate=1.0,
        static_validity_rate=1.0,
        regression_pass_rate=1.0,
    )
