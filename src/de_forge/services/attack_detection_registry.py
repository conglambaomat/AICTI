from __future__ import annotations

from de_forge.schemas.attack_detection import TechniqueDetectionLink


class AttackDetectionRegistry:
    def __init__(self, links: list[TechniqueDetectionLink]) -> None:
        self.links = links

    @classmethod
    def default(cls) -> AttackDetectionRegistry:
        return cls(
            links=[
                TechniqueDetectionLink(
                    technique_id="T1059.001",
                    detection_strategy_id="ds_command_line_behavior",
                    analytic_id="analytic_encoded_powershell",
                    data_component_id="process_creation",
                )
            ]
        )

    def links_for_technique(self, technique_id: str) -> list[TechniqueDetectionLink]:
        return [link for link in self.links if link.technique_id == technique_id]
