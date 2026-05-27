from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from de_forge.agents.base import AgentOutputValidationError, BaseAgent, JsonLlmClient
from de_forge.schemas.agent_io import Citation
from de_forge.services.prompt_registry import PromptRegistry


class EvidenceAgent(BaseAgent):
    agent_name = "evidence_agent"
    prompt_version = "v1"
    response_schema_name = "EvidenceOutput"
    requires_citations = True

    def __init__(self, llm_client: JsonLlmClient) -> None:
        prompt = PromptRegistry.default().get(self.agent_name, self.prompt_version)
        super().__init__(llm_client=llm_client, system_prompt=prompt.system_prompt)

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Extract evidence from chunks: {input_payload['chunks']}"

    def extract_citations(self, content: dict[str, Any]) -> list[Citation]:
        evidence_quotes = content.get("evidence_quotes") if "evidence_quotes" in content else []
        if evidence_quotes is None:
            evidence_quotes = []
        if not isinstance(evidence_quotes, list):
            raise AgentOutputValidationError("citations must be a list")
        try:
            return [
                Citation.model_validate(
                    {
                        "chunk_id": item["chunk_id"],
                        "quote": item["quote"],
                        "start_offset": item["start_offset"],
                        "end_offset": item["end_offset"],
                    }
                )
                for item in evidence_quotes
            ]
        except (KeyError, TypeError, ValidationError) as exc:
            raise AgentOutputValidationError("citations malformed") from exc
