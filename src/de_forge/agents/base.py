from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from de_forge.core.config import settings
from de_forge.schemas.agent_io import AgentMetadata, AgentOutputEnvelope
from de_forge.services.llm_client import LlmRequest, LlmResponse


class JsonLlmClient(Protocol):
    def complete_json(self, request: LlmRequest) -> LlmResponse: ...


class BaseAgent(ABC):
    agent_name: str
    prompt_version: str
    response_schema_name: str

    def __init__(self, llm_client: JsonLlmClient, system_prompt: str) -> None:
        self.llm_client = llm_client
        self.system_prompt = system_prompt

    def run(
        self,
        run_id: str,
        input_artifact_ids: list[str],
        input_payload: dict[str, Any],
    ) -> AgentOutputEnvelope:
        request = LlmRequest(
            system_prompt=self.system_prompt,
            user_prompt=self.build_user_prompt(input_payload),
            response_schema_name=self.response_schema_name,
        )
        response = self.llm_client.complete_json(request)
        return AgentOutputEnvelope(
            run_id=run_id,
            agent_name=self.agent_name,
            input_artifact_ids=input_artifact_ids,
            output=response.content,
            confidence=float(response.content.get("confidence", 1.0)),
            citations=[],
            abstain=bool(response.content.get("abstain", False)),
            abstain_reason=response.content.get("abstain_reason"),
            metadata=AgentMetadata(
                model=settings.openai_model,
                prompt_version=f"{self.agent_name}:{self.prompt_version}",
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                latency_ms=response.latency_ms,
                cost_usd=response.cost_usd,
            ),
        )

    @abstractmethod
    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        raise NotImplementedError
