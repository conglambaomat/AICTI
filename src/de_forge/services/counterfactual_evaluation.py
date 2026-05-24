from __future__ import annotations

from copy import deepcopy

from de_forge.schemas.sigma import SigmaRule
from de_forge.schemas.test_event import ValidationEvent
from de_forge.services.dynamic_validation import DynamicValidationService


class CounterfactualEvaluationService:
    def __init__(self) -> None:
        self.dynamic = DynamicValidationService()

    def evaluate_condition_importance(
        self,
        rule: SigmaRule,
        positive_events: list[ValidationEvent],
        benign_events: list[ValidationEvent],
    ) -> dict[str, str]:
        baseline = self.dynamic.evaluate(rule, positive_events, benign_events)
        importance: dict[str, str] = {}

        for selection_name in [key for key in rule.detection if key != "condition"]:
            mutated = deepcopy(rule)
            mutated.detection.pop(selection_name, None)
            mutated.detection["condition"] = " or ".join(
                key for key in mutated.detection if key != "condition"
            )
            result = self.dynamic.evaluate(mutated, positive_events, benign_events)
            importance[selection_name] = "important" if result.recall < baseline.recall else "low"

        return importance
