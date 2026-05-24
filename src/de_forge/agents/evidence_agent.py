from __future__ import annotations

from typing import Any

from de_forge.agents.base import BaseAgent, JsonLlmClient
from de_forge.schemas.agent_io import AgentOutputEnvelope, Citation
from de_forge.services.prompt_registry import PromptRegistry


class EvidenceAgent(BaseAgent):
    agent_name = "evidence_agent"
    prompt_version = "v1"
    response_schema_name = "EvidenceOutput"

    def __init__(self, llm_client: JsonLlmClient) -> None:
        prompt = PromptRegistry.default().get(self.agent_name, self.prompt_version)
        super().__init__(llm_client=llm_client, system_prompt=prompt.system_prompt)

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Extract evidence from chunks: {input_payload['chunks']}"

    def run(
        self, run_id: str, input_artifact_ids: list[str], input_payload: dict[str, Any]
    ) -> AgentOutputEnvelope:
        envelope = super().run(run_id, input_artifact_ids, input_payload)
        citations = [
            Citation(
                chunk_id=item["chunk_id"],
                quote=item["quote"],
                start_offset=item["start_offset"],
                end_offset=item["end_offset"],
            )
            for item in envelope.output.get("evidence_quotes", [])
        ]
        return envelope.model_copy(update={"citations": citations})
