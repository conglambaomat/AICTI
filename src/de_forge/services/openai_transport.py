from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class HttpResponse(Protocol):
    def raise_for_status(self) -> None: ...

    def json(self) -> dict[str, Any]: ...


class HttpClient(Protocol):
    def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: int,
    ) -> HttpResponse: ...


class OpenAITransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAITransportResponse:
    content: str
    model: str
    finish_reason: str
    usage: dict[str, int]


class OpenAICompatibleTransport:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        http_client: HttpClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.http_client = http_client or httpx.Client()
        self._owns_http_client = http_client is None

    def close(self) -> None:
        if self._owns_http_client and hasattr(self.http_client, "close"):
            self.http_client.close()

    def __enter__(self) -> OpenAICompatibleTransport:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def send(self, payload: dict[str, Any], timeout_seconds: int) -> OpenAITransportResponse:
        response = self.http_client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": payload["model"],
                "messages": [{"role": "user", "content": payload["prompt"]}],
                "temperature": payload["temperature"],
                "max_tokens": payload["max_tokens"],
                "response_format": payload["response_format"],
                "metadata": payload["metadata"],
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice["finish_reason"]
            model = data["model"]
            usage = data["usage"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenAITransportError("malformed provider response") from exc
        return OpenAITransportResponse(
            content=content,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
        )


__all__ = ["OpenAICompatibleTransport", "OpenAITransportError", "OpenAITransportResponse"]
