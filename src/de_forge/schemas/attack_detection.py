from __future__ import annotations

from pydantic import BaseModel


class TechniqueDetectionLink(BaseModel):
    technique_id: str
    detection_strategy_id: str
    analytic_id: str
    data_component_id: str
