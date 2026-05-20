"""Deterministic synthetic dynamic validation service."""

from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class DynamicValidationResult:
    """Deterministic dynamic validation result."""

    true_positives: int
    false_positives: int
    attack_total: int
    benign_total: int


class DynamicValidationService:
    """Service for deterministic synthetic dynamic validation of Sigma rules."""

    def run_synthetic_validation(
        self,
        rule: str,
        attack_events: list[dict],
        benign_events: list[dict],
    ) -> DynamicValidationResult:
        """Run deterministic synthetic validation against attack and benign event corpus."""
        try:
            parsed = yaml.safe_load(rule)
        except yaml.YAMLError:
            return DynamicValidationResult(
                true_positives=0,
                false_positives=0,
                attack_total=len(attack_events),
                benign_total=len(benign_events),
            )

        if not isinstance(parsed, dict):
            return DynamicValidationResult(
                true_positives=0,
                false_positives=0,
                attack_total=len(attack_events),
                benign_total=len(benign_events),
            )

        detection = parsed.get("detection", {})
        if not isinstance(detection, dict):
            return DynamicValidationResult(
                true_positives=0,
                false_positives=0,
                attack_total=len(attack_events),
                benign_total=len(benign_events),
            )

        selection = detection.get("selection", {})
        if not isinstance(selection, dict):
            return DynamicValidationResult(
                true_positives=0,
                false_positives=0,
                attack_total=len(attack_events),
                benign_total=len(benign_events),
            )

        tp = sum(1 for event in attack_events if self._matches(event, selection))
        fp = sum(1 for event in benign_events if self._matches(event, selection))

        return DynamicValidationResult(
            true_positives=tp,
            false_positives=fp,
            attack_total=len(attack_events),
            benign_total=len(benign_events),
        )

    def _matches(self, event: dict, selection: dict) -> bool:
        """Check if event matches selection criteria deterministically."""
        for key, value in selection.items():
            if "|contains" in key:
                field_name = key.split("|", 1)[0]
                event_value = event.get(field_name, "")
                if not isinstance(event_value, str):
                    return False
                if value.lower() not in event_value.lower():
                    return False
            else:
                if event.get(key) != value:
                    return False
        return True
