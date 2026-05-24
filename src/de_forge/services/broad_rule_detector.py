from __future__ import annotations

from de_forge.schemas.sigma import SigmaRule


class BroadRuleDetector:
    def is_overbroad(self, rule: SigmaRule) -> bool:
        selection_items = [
            (key, value) for key, value in rule.detection.items() if key != "condition"
        ]
        if len(selection_items) != 1:
            return False
        _, selection = selection_items[0]
        if not isinstance(selection, dict) or len(selection) != 1:
            return False
        field_expr, values = next(iter(selection.items()))
        normalized_values = (
            [str(value).lower() for value in values]
            if isinstance(values, list)
            else [str(values).lower()]
        )
        return field_expr.lower().startswith("image") and any(
            "powershell" in value for value in normalized_values
        )
