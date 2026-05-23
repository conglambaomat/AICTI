from __future__ import annotations

from typing import Any

from de_forge.agents.base import BaseAgent, JsonLlmClient


class CriticAgent(BaseAgent):
    agent_name = "critic_agent"
    prompt_version = "v1"
    response_schema_name = "CriticOutput"

    def __init__(self, llm_client: JsonLlmClient) -> None:
        super().__init__(
            llm_client=llm_client,
            system_prompt="Critique rule candidates for detection engineering risks.",
        )

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return (
            "Review candidate for false positive risk, false negative risk, bypass risk, "
            f"telemetry gaps, and unsupported claims: {input_payload}"
        )
