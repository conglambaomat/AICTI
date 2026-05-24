from __future__ import annotations

from de_forge.schemas.sigma import SigmaRule


class SigmaValidator:
    def validate(self, rule: SigmaRule) -> bool:
        if not rule.title.strip():
            return False
        if "condition" not in rule.detection:
            return False
        selection_names = [key for key in rule.detection if key != "condition"]
        if not selection_names:
            return False
        condition = str(rule.detection["condition"])
        return all(selection_name in condition for selection_name in selection_names)
