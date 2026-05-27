from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from de_forge.services.llm_client import (
    ConfigurationError,
    LLMClient,
    LLMRequest,
    TransportResponse,
)


@dataclass
class DummyResponse:
    content: str = "{}"
    model: str = "cx/gpt-5.5"
    finish_reason: str = "stop"
    usage: dict[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
    )


class DummyTransport:
    def send(self, payload: dict[str, Any], timeout_seconds: int) -> TransportResponse:
        return DummyResponse()


def _request(model: str = "cx/gpt-5.5") -> LLMRequest:
    return LLMRequest(
        prompt="{}",
        model=model,
        metadata={
            "agent_name": "policy-test",
            "stage": "llm_policy",
            "run_id": "run-test",
            "trace_id": "trace-test",
            "prompt_version": "v1",
        },
    )


def test_model_override_is_rejected() -> None:
    client = LLMClient(transport=DummyTransport(), model="cx/gpt-5.5", api_key="key")

    with pytest.raises(ConfigurationError, match="model override"):
        client.call(_request(model="other-model"))
