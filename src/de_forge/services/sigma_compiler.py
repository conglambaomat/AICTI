from __future__ import annotations

from typing import Any

import yaml

from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.detection_ast import DetectionAst, LogicOperator
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule


class SigmaCompiler:
    def compile(
        self,
        ast: DetectionAst,
        title: str,
        description: str,
        falsepositives: list[str],
        level: str,
    ) -> SigmaRule:
        detection: dict[str, Any] = {}
        provenance: dict[str, list[str]] = {}
        selection_names: list[str] = []

        for condition in ast.root.children:
            selection_name = f"selection_{condition.id}"
            selection_names.append(selection_name)
            detection[selection_name] = {f"{condition.field}|contains": condition.values}
            provenance[selection_name] = condition.evidence_ids

        if ast.root.operator == LogicOperator.ALL:
            condition_expr = " and ".join(selection_names)
        elif ast.root.operator == LogicOperator.ANY:
            condition_expr = " or ".join(selection_names)
        else:
            condition_expr = f"not ({' or '.join(selection_names)})"
        detection["condition"] = condition_expr

        return SigmaRule(
            title=title,
            id=f"sigma_{snapshot_hash(ast.model_dump(mode='json'))[:16]}",
            status="experimental",
            description=description,
            references=[],
            tags=[f"attack.{technique.lower()}" for technique in ast.attack_techniques],
            logsource=SigmaLogsource(product="windows", category="process_creation"),
            detection=detection,
            falsepositives=falsepositives,
            level=level,
            provenance=provenance,
        )

    def to_yaml(self, rule: SigmaRule) -> str:
        payload = rule.model_dump(exclude={"provenance"}, exclude_none=True)
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
