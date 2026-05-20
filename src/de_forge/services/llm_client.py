"""Unified LLM client for OpenAI-compatible API calls."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from typing import Any

import jsonschema


class LLMError(Exception):
    """Base class for all LLM client errors."""


class RateLimitError(LLMError):
    pass


class TimeoutError(LLMError):
    pass


class ServiceUnavailableError(LLMError):
    pass


class InternalServerError(LLMError):
    pass


class AuthenticationError(LLMError):
    pass


class InvalidRequestError(LLMError):
    pass


class ModelNotFoundError(LLMError):
    pass


class ContentFilterError(LLMError):
    pass


class SchemaValidationError(LLMError):
    pass


class ParseError(LLMError):
    pass


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMRequest:
    prompt: str
    model: str = "cx/gpt-5.5"
    temperature: float = 0.0
    max_tokens: int = 4096
    response_format: dict[str, Any] | None = None
    timeout_seconds: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: TokenUsage
    finish_reason: str
    latency_ms: int
    metadata: dict[str, Any]


def calculate_backoff(
    attempt: int,
    error_type: str,
    jitter: bool = True,
    retry_after: int | None = None,
) -> float:
    if error_type == "rate_limit":
        if attempt == 1:
            base = float(min(retry_after or 0, 60))
        elif attempt == 2:
            base = 30.0
        elif attempt == 3:
            base = 60.0
        else:
            base = 0.0
    else:
        if attempt == 1:
            base = 0.0
        elif attempt == 2:
            base = 2.0
        elif attempt == 3:
            base = 4.0
        else:
            base = 0.0

    if not jitter:
        return base
    return base * (1 + random.uniform(-0.2, 0.2))


def calculate_cost(usage: TokenUsage) -> float:
    return (usage.prompt_tokens / 1000) * 0.01 + (usage.completion_tokens / 1000) * 0.03


class LLMClient:
    def __init__(self, transport: Any, model: str = "cx/gpt-5.5") -> None:
        self._transport = transport
        self._model = model

    def call(self, request: LLMRequest) -> LLMResponse:
        self._validate_metadata(request.metadata)
        max_retries = 3

        for attempt in range(1, max_retries + 2):
            started = time.perf_counter()
            try:
                raw = self._transport.send(
                    {
                        "prompt": request.prompt,
                        "model": request.model or self._model,
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                        "response_format": request.response_format,
                        "metadata": request.metadata,
                    },
                    timeout_seconds=request.timeout_seconds,
                )
                usage = TokenUsage(**raw.usage)
                return LLMResponse(
                    content=raw.content,
                    model=raw.model,
                    usage=usage,
                    finish_reason=raw.finish_reason,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    metadata={**request.metadata, "cost_usd": calculate_cost(usage)},
                )
            except TimeoutError:
                raise
            except (RateLimitError, ServiceUnavailableError, InternalServerError) as exc:
                if attempt > max_retries:
                    raise exc
                err_type = "rate_limit" if isinstance(exc, RateLimitError) else "transient"
                delay = calculate_backoff(attempt=attempt, error_type=err_type)
                if delay > 0:
                    time.sleep(delay)

        raise InternalServerError("retry loop exhausted")

    def call_with_schema(self, request: LLMRequest, schema: dict[str, Any]) -> tuple[dict[str, Any], LLMResponse]:
        for parse_attempt in range(2):
            response = self.call(request)
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError as exc:
                if parse_attempt == 1:
                    raise ParseError("cannot parse JSON response") from exc
                continue

            try:
                jsonschema.validate(parsed, schema)
            except jsonschema.ValidationError as exc:
                raise SchemaValidationError(str(exc)) from exc

            return parsed, response

        raise ParseError("cannot parse JSON response")

    @staticmethod
    def _validate_metadata(metadata: dict[str, Any]) -> None:
        required = {"agent_name", "stage", "run_id", "trace_id", "prompt_version"}
        missing = required - set(metadata.keys())
        if missing:
            raise InvalidRequestError(f"missing metadata fields: {sorted(missing)}")
