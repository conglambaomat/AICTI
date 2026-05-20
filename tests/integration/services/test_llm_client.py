from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from de_forge.services.llm_client import (
    InternalServerError,
    LLMClient,
    LLMRequest,
    ParseError,
    SchemaValidationError,
    TimeoutError,
    TokenUsage,
    calculate_backoff,
)


@dataclass
class FakeHTTPResponse:
    content: str
    usage: dict[str, int]
    finish_reason: str = "stop"
    model: str = "cx/gpt-5.5"


class FakeTransport:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.calls = 0

    def send(self, payload: dict, timeout_seconds: int) -> FakeHTTPResponse:
        self.calls += 1
        event = self.events.pop(0)
        if isinstance(event, Exception):
            raise event
        return event


def _req() -> LLMRequest:
    return LLMRequest(
        prompt="hello",
        metadata={
            "agent_name": "x",
            "stage": "y",
            "run_id": "r",
            "trace_id": "t",
            "prompt_version": "p",
        },
    )


def test_retry_on_transient_error_then_success() -> None:
    transport = FakeTransport(
        [
            InternalServerError("500"),
            FakeHTTPResponse(
                content='{"ok": true}',
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            ),
        ]
    )
    client = LLMClient(transport=transport)

    response = client.call(_req())

    assert transport.calls == 2
    assert response.content == '{"ok": true}'


def test_timeout_behavior_raises_timeout_error() -> None:
    transport = FakeTransport([TimeoutError("request timed out")])
    client = LLMClient(transport=transport)

    with pytest.raises(TimeoutError):
        client.call(_req())


def test_schema_validation_raises_contract_error() -> None:
    transport = FakeTransport(
        [
            FakeHTTPResponse(
                content=json.dumps({"name": "abc"}),
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            )
        ]
    )
    client = LLMClient(transport=transport)

    schema = {
        "type": "object",
        "properties": {"id": {"type": "integer"}},
        "required": ["id"],
        "additionalProperties": False,
    }

    with pytest.raises(SchemaValidationError):
        client.call_with_schema(_req(), schema)


def test_token_accounting_and_cost_in_metadata() -> None:
    transport = FakeTransport(
        [
            FakeHTTPResponse(
                content='{"id": 1}',
                usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
            )
        ]
    )
    client = LLMClient(transport=transport)

    response = client.call(_req())

    assert response.usage == TokenUsage(prompt_tokens=1000, completion_tokens=1000, total_tokens=2000)
    assert response.metadata["cost_usd"] == pytest.approx(0.04)


def test_parse_error_retries_once_then_fails() -> None:
    transport = FakeTransport(
        [
            FakeHTTPResponse(content="not-json", usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}),
            FakeHTTPResponse(content="still-not-json", usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}),
        ]
    )
    client = LLMClient(transport=transport)

    with pytest.raises(ParseError):
        client.call_with_schema(_req(), {"type": "object"})

    assert transport.calls == 2


def test_backoff_policy_values() -> None:
    assert calculate_backoff(attempt=1, error_type="transient", jitter=False) == 0.0
    assert calculate_backoff(attempt=2, error_type="transient", jitter=False) == 2.0
    assert calculate_backoff(attempt=3, error_type="transient", jitter=False) == 4.0
    assert calculate_backoff(attempt=1, error_type="rate_limit", jitter=False, retry_after=120) == 60.0
    assert calculate_backoff(attempt=2, error_type="rate_limit", jitter=False) == 30.0
