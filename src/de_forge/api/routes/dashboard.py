from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.services.metrics import MetricsService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return MetricsService(db).dashboard_summary()
