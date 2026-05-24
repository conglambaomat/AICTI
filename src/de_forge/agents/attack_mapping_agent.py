from __future__ import annotations

from typing import Any

from de_forge.agents.base import BaseAgent, JsonLlmClient


class AttackMappingAgent(BaseAgent):
    agent_name = "attack_mapping_agent"
    prompt_version = "v1"
    response_schema_name = "AttackMappingOutput"

    def __init__(self, llm_client: JsonLlmClient) -> None:
        super().__init__(
            llm_client=llm_client,
            system_prompt="Map behaviors to ATT&CK techniques using strict JSON.",
        )

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Map behaviors to ATT&CK techniques using only supplied evidence: {input_payload}"
