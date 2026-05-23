from __future__ import annotations

from dataclasses import dataclass

import yaml

from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.schemas.test_event import DynamicValidationResult, ValidationEvent


@dataclass(frozen=True)
class SyntheticValidationResult:
    true_positives: int
    false_positives: int
    attack_total: int
    benign_total: int


class DynamicValidationService:
    def evaluate(
        self,
        rule: SigmaRule,
        positive_events: list[ValidationEvent],
        benign_events: list[ValidationEvent],
    ) -> DynamicValidationResult:
        true_positives = sum(1 for event in positive_events if self._matches(rule, event))
        false_negatives = len(positive_events) - true_positives
        false_positives = sum(1 for event in benign_events if self._matches(rule, event))
        true_negatives = len(benign_events) - false_positives

        precision = (
            true_positives / (true_positives + false_positives)
            if true_positives + false_positives
            else 0.0
        )
        recall = true_positives / len(positive_events) if positive_events else 0.0

        return DynamicValidationResult(
            true_positives=true_positives,
            false_positives=false_positives,
            true_negatives=true_negatives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
        )

    def run_synthetic_validation(
        self,
        rule: str,
        attack_events: list[dict[str, object]],
        benign_events: list[dict[str, object]],
    ) -> SyntheticValidationResult:
        parsed = yaml.safe_load(rule)
        sigma_rule = SigmaRule(
            title=parsed.get("title", "synthetic rule"),
            id="synthetic_rule",
            status="experimental",
            description="synthetic validation rule",
            references=[],
            tags=[],
            logsource=SigmaLogsource(
                **parsed.get("logsource", {"product": "windows", "category": "process_creation"})
            ),
            detection=parsed["detection"],
            falsepositives=[],
            level="medium",
            provenance={},
        )

        positive = [
            ValidationEvent(
                id=f"attack-{index}",
                fields={str(key): str(value) for key, value in event.items()},
                expected_match=True,
            )
            for index, event in enumerate(attack_events)
        ]
        benign = [
            ValidationEvent(
                id=f"benign-{index}",
                fields={str(key): str(value) for key, value in event.items()},
                expected_match=False,
            )
            for index, event in enumerate(benign_events)
        ]
        result = self.evaluate(sigma_rule, positive, benign)
        return SyntheticValidationResult(
            true_positives=result.true_positives,
            false_positives=result.false_positives,
            attack_total=len(attack_events),
            benign_total=len(benign_events),
        )

    def _matches(self, rule: SigmaRule, event: ValidationEvent) -> bool:
        for key, selection in rule.detection.items():
            if key == "condition":
                continue
            if not isinstance(selection, dict):
                continue
            if self._selection_matches(selection, event):
                return True
        return False

    def _selection_matches(self, selection: dict[str, object], event: ValidationEvent) -> bool:
        for field_expr, expected in selection.items():
            field, operator = self._split_field_expr(field_expr)
            observed = str(event.fields.get(field, ""))
            values = expected if isinstance(expected, list) else [expected]
            normalized_values = [str(value) for value in values]

            if operator == "contains" and not any(value in observed for value in normalized_values):
                return False
            if operator == "equals" and not any(value == observed for value in normalized_values):
                return False
        return True

    def _split_field_expr(self, field_expr: str) -> tuple[str, str]:
        if "|" not in field_expr:
            return field_expr, "equals"
        field, operator = field_expr.split("|", 1)
        return field, operator
