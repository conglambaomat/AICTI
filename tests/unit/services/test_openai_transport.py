from __future__ import annotations

from typing import Any, cast

import pytest

from de_forge.services.openai_transport import OpenAICompatibleTransport, OpenAITransportError


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
            "model": "cx/gpt-5.5",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }


def test_openai_transport_builds_authorized_json_request() -> None:
    sent: dict[str, Any] = {}

    class FakeHttpClient:
        def post(
            self,
            url: str,
            headers: dict[str, str],
            json: dict[str, Any],
            timeout: int,
        ) -> FakeResponse:
            sent["url"] = url
            sent["headers"] = headers
            sent["json"] = json
            sent["timeout"] = timeout
            return FakeResponse()

    transport = OpenAICompatibleTransport(
        base_url="https://shopapikey.com/v1",
        api_key="key",
        http_client=FakeHttpClient(),
    )
    response = transport.send(
        {
            "prompt": "Return JSON",
            "model": "cx/gpt-5.5",
            "temperature": 0,
            "max_tokens": 10,
            "response_format": {"type": "json_object"},
            "metadata": {"trace_id": "trace-1"},
        },
        timeout_seconds=30,
    )

    assert sent["url"].endswith("/chat/completions")
    assert sent["headers"]["Authorization"] == "Bearer key"
    assert sent["json"]["model"] == "cx/gpt-5.5"
    assert sent["json"]["messages"] == [{"role": "user", "content": "Return JSON"}]
    assert sent["json"]["response_format"] == {"type": "json_object"}
    assert sent["json"]["metadata"] == {"trace_id": "trace-1"}
    assert sent["timeout"] == 30
    assert response.content == "{}"
    assert response.model == "cx/gpt-5.5"
    assert response.usage == {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}


def test_openai_transport_closes_owned_http_client() -> None:
    class ClosableHttpClient:
        closed = False

        def close(self) -> None:
            self.closed = True

    transport = OpenAICompatibleTransport(base_url="https://shopapikey.com/v1", api_key="key")
    closable = ClosableHttpClient()
    transport.http_client = cast("Any", closable)

    transport.close()

    assert closable.closed is True


def test_openai_transport_rejects_malformed_provider_response() -> None:
    class MalformedResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"choices": [], "model": "cx/gpt-5.5", "usage": {}}

    class FakeHttpClient:
        def post(
            self,
            url: str,
            headers: dict[str, str],
            json: dict[str, Any],
            timeout: int,
        ) -> MalformedResponse:
            return MalformedResponse()

    transport = OpenAICompatibleTransport(
        base_url="https://shopapikey.com/v1",
        api_key="key",
        http_client=FakeHttpClient(),
    )

    with pytest.raises(OpenAITransportError, match="malformed provider response"):
        transport.send(
            {
                "prompt": "Return JSON",
                "model": "cx/gpt-5.5",
                "temperature": 0,
                "max_tokens": 10,
                "response_format": {"type": "json_object"},
                "metadata": {},
            },
            timeout_seconds=30,
        )
