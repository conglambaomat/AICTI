from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/quality")
def quality_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return MetricsService(db).quality_summary()


@router.get("/ops")
def ops_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return MetricsService(db).ops_summary()
