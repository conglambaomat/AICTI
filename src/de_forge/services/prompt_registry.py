from __future__ import annotations

from pydantic import BaseModel


class PromptDefinition(BaseModel):
    prompt_id: str
    agent_name: str
    version: str
    system_prompt: str


class PromptRegistry:
    def __init__(self, prompts: list[PromptDefinition]) -> None:
        self.prompts = {(prompt.agent_name, prompt.version): prompt for prompt in prompts}

    @classmethod
    def default(cls) -> PromptRegistry:
        return cls(
            prompts=[
                PromptDefinition(
                    prompt_id="evidence_agent:v1",
                    agent_name="evidence_agent",
                    version="v1",
                    system_prompt="Extract only explicitly supported behavioral evidence from provided chunks. Return strict JSON only.",
                ),
                PromptDefinition(
                    prompt_id="attack_mapping_agent:v1",
                    agent_name="attack_mapping_agent",
                    version="v1",
                    system_prompt="Map extracted behaviors to ATT&CK techniques using only supplied evidence. Return strict JSON only.",
                ),
            ]
        )

    def get(self, agent_name: str, version: str) -> PromptDefinition:
        return self.prompts[(agent_name, version)]
