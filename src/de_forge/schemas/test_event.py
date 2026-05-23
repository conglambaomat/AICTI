from __future__ import annotations

from pydantic import BaseModel


class ValidationEvent(BaseModel):
    id: str
    fields: dict[str, str | int | float | bool]
    expected_match: bool


class DynamicValidationResult(BaseModel):
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
