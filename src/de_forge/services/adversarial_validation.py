from __future__ import annotations

from pydantic import BaseModel

from de_forge.schemas.sigma import SigmaRule
from de_forge.schemas.test_event import ValidationEvent
from de_forge.services.dynamic_validation import DynamicValidationService


class AdversarialValidationResult(BaseModel):
    total_variants: int
    matched_variants: int
    robustness_score: float


class AdversarialValidationService:
    def __init__(self) -> None:
        self.dynamic = DynamicValidationService()

    def evaluate(
        self, rule: SigmaRule, variants: list[ValidationEvent]
    ) -> AdversarialValidationResult:
        matched = sum(1 for variant in variants if self.dynamic._matches(rule, variant))
        total = len(variants)
        return AdversarialValidationResult(
            total_variants=total,
            matched_variants=matched,
            robustness_score=matched / total if total else 0.0,
        )
