from __future__ import annotations

from typing import Any

from de_forge.agents.base import BaseAgent, JsonLlmClient


class DetectionSpecAgent(BaseAgent):
    agent_name = "detection_spec_agent"
    prompt_version = "v1"
    response_schema_name = "DetectionSpecOutput"

    def __init__(self, llm_client: JsonLlmClient) -> None:
        super().__init__(
            llm_client=llm_client,
            system_prompt="Build verified DetectionSpec JSON from graph paths.",
        )

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return (
            "Build a DetectionSpec with evidence, ATT&CK, telemetry, allowed fields, "
            f"logic, false positives, and test plan: {input_payload}"
        )
