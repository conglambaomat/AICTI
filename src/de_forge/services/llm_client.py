"""Unified LLM client for OpenAI-compatible API calls."""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import jsonschema

# Retry policy constants
MAX_RETRIES = 3
TRANSIENT_BACKOFF_ATTEMPT_2 = 2.0
TRANSIENT_BACKOFF_ATTEMPT_3 = 4.0
RATE_LIMIT_BACKOFF_ATTEMPT_2 = 30.0
RATE_LIMIT_BACKOFF_ATTEMPT_3 = 60.0
RATE_LIMIT_MAX_RETRY_AFTER = 60.0
BACKOFF_JITTER_RANGE = 0.2


class LLMError(Exception):
    """Base class for all LLM client errors."""


class RateLimitError(LLMError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.retryable = True


class TimeoutError(LLMError):
    """Request timeout."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = True


class ServiceUnavailableError(LLMError):
    """Service unavailable (503)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = True


class InternalServerError(LLMError):
    """Internal server error (500)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = True


class AuthenticationError(LLMError):
    """Authentication failed (401)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = False


class InvalidRequestError(LLMError):
    """Invalid request (400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = False


class ModelNotFoundError(LLMError):
    """Model not found (404)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = False


class ContentFilterError(LLMError):
    """Content policy violation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = False


class SchemaValidationError(LLMError):
    """Response does not match expected schema."""

    def __init__(
        self, message: str, validation_error: jsonschema.ValidationError | None = None
    ) -> None:
        super().__init__(message)
        self.validation_error = validation_error
        self.retryable = False


class ParseError(LLMError):
    """Cannot parse JSON response."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.retryable = False


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


class TransportResponse(Protocol):
    """Transport response contract."""

    content: str
    model: str
    finish_reason: str
    usage: dict[str, int]


class Transport(Protocol):
    """Transport interface for OpenAI-compatible calls."""

    def send(self, payload: dict[str, Any], timeout_seconds: int) -> TransportResponse: ...


def build_parse_retry_prompt(prompt: str, parse_error: str) -> str:
    """Append parse error context for one retry attempt."""
    return (
        f"{prompt}\n\nPrevious response parse error: {parse_error}\nReturn strict JSON object only."
    )


def with_parse_context(request: LLMRequest, parse_error: str) -> LLMRequest:
    """Return request copy with parse error context appended."""
    return LLMRequest(
        prompt=build_parse_retry_prompt(request.prompt, parse_error),
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        response_format=request.response_format,
        timeout_seconds=request.timeout_seconds,
        metadata=request.metadata,
    )


def ensure_json_object(parsed: Any) -> dict[str, Any]:
    """Ensure parsed JSON root is an object."""
    if not isinstance(parsed, dict):
        raise ParseError("JSON response root must be an object")
    return parsed


def calculate_backoff(
    attempt: int,
    error_type: str,
    jitter: bool = True,
    retry_after: int | None = None,
) -> float:
    """Calculate retry backoff delay in seconds."""
    if error_type == "rate_limit":
        if attempt == 1:
            base = float(min(retry_after or 0, RATE_LIMIT_MAX_RETRY_AFTER))
        elif attempt == 2:
            base = RATE_LIMIT_BACKOFF_ATTEMPT_2
        elif attempt == 3:
            base = RATE_LIMIT_BACKOFF_ATTEMPT_3
        else:
            base = 0.0
    else:
        if attempt == 1:
            base = 0.0
        elif attempt == 2:
            base = TRANSIENT_BACKOFF_ATTEMPT_2
        elif attempt == 3:
            base = TRANSIENT_BACKOFF_ATTEMPT_3
        else:
            base = 0.0

    if not jitter:
        return base

    jitter_factor = 1 + random.uniform(-BACKOFF_JITTER_RANGE, BACKOFF_JITTER_RANGE)
    return max(base * jitter_factor, 0.0)


def calculate_cost(usage: TokenUsage) -> float:
    """Calculate USD cost from token usage."""
    return (usage.prompt_tokens / 1000) * 0.01 + (usage.completion_tokens / 1000) * 0.03


class LLMClient:
    """Unified OpenAI-compatible LLM client with retries and schema validation."""

    def __init__(
        self,
        transport: Transport,
        model: str = "cx/gpt-5.5",
        base_url: str = "https://shopapikey.com/v1",
        api_key: str | None = None,
    ) -> None:
        """Initialize client with provider configuration and transport."""
        self._transport = transport
        self._model = model
        self._base_url = base_url
        self._api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        if self._api_key is None:
            raise AuthenticationError("OPENAI_API_KEY environment variable is required")

    def call(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM call with retry/backoff/timeout handling."""
        self._validate_metadata(request.metadata)

        for attempt in range(1, MAX_RETRIES + 2):
            started = time.perf_counter()
            try:
                raw = self._transport.send(
                    {
                        "prompt": request.prompt,
                        "model": request.model or self._model,
                        "base_url": self._base_url,
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
            except (
                TimeoutError,
                RateLimitError,
                ServiceUnavailableError,
                InternalServerError,
            ) as exc:
                if attempt > MAX_RETRIES:
                    raise exc
                err_type = "rate_limit" if isinstance(exc, RateLimitError) else "transient"
                retry_after = exc.retry_after if isinstance(exc, RateLimitError) else None
                delay = calculate_backoff(
                    attempt=attempt, error_type=err_type, retry_after=retry_after
                )
                if delay > 0:
                    time.sleep(delay)

        raise InternalServerError("retry loop exhausted")

    def call_with_schema(
        self, request: LLMRequest, schema: dict[str, Any]
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Execute LLM call, parse JSON object, and validate against schema."""
        current_request = request
        for parse_attempt in range(2):
            response = self.call(current_request)
            try:
                parsed = json.loads(response.content)
                parsed_obj = ensure_json_object(parsed)
            except (json.JSONDecodeError, ParseError) as exc:
                if parse_attempt == 1:
                    raise ParseError("cannot parse JSON response") from exc
                current_request = with_parse_context(request, str(exc))
                continue

            try:
                jsonschema.validate(parsed_obj, schema)
            except jsonschema.ValidationError as exc:
                message = f"schema validation failed at {list(exc.path)}: {exc.message}"
                raise SchemaValidationError(message, validation_error=exc) from exc

            return parsed_obj, response

        raise ParseError("cannot parse JSON response")

    @staticmethod
    def _validate_metadata(metadata: dict[str, Any]) -> None:
        """Validate required metadata fields for traceability."""
        required = {"agent_name", "stage", "run_id", "trace_id", "prompt_version"}
        missing = required - set(metadata.keys())
        if missing:
            raise InvalidRequestError(f"missing metadata fields: {sorted(missing)}")


__all__ = [
    "AuthenticationError",
    "ContentFilterError",
    "InternalServerError",
    "InvalidRequestError",
    "LLMClient",
    "LLMError",
    "LLMRequest",
    "LLMResponse",
    "ModelNotFoundError",
    "ParseError",
    "RateLimitError",
    "SchemaValidationError",
    "ServiceUnavailableError",
    "TimeoutError",
    "TokenUsage",
    "calculate_backoff",
    "calculate_cost",
]
