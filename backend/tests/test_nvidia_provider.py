from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from app.config import Settings, build_llm_provider
from app.providers.nvidia import NvidiaLLMProvider


class Answer(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            request = httpx.Request("POST", "https://example.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self) -> dict[str, object]:
        return self.payload


class FakeHTTPClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    async def post(self, _url: str, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "llm_provider": "nvidia",
        "nvidia_api_key": "test-key",
        "nvidia_model": "test-model",
        "nvidia_max_retries": 1,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def response(content: str, usage: dict[str, int] | None = None) -> FakeResponse:
    payload: dict[str, object] = {
        "choices": [{"message": {"content": content}}],
    }
    if usage:
        payload["usage"] = usage
    return FakeResponse(payload)


@pytest.mark.asyncio
async def test_nvidia_provider_validates_structured_json() -> None:
    client = FakeHTTPClient([response(json.dumps({"answer": "verified"}), {"total_tokens": 12})])
    provider = NvidiaLLMProvider(settings(), client)

    result = await provider.generate_structured("system", "user", Answer)

    assert result.status == "available"
    assert result.value is not None
    assert result.value.answer == "verified"
    assert result.usage == {"total_tokens": 12}
    request = client.calls[0]["json"]
    assert request["model"] == "test-model"  # type: ignore[index]
    assert request["response_format"] == {"type": "json_object"}  # type: ignore[index]
    assert request["max_tokens"] == 2048  # type: ignore[index]
    messages = request["messages"]  # type: ignore[index]
    assert messages[1] == {"role": "user", "content": "user"}
    instructions, schema = messages[0]["content"].split("\n", 2)[1:]
    assert "Return only valid JSON" in instructions
    assert "Do not include Markdown fences, commentary" in instructions
    assert json.loads(schema) == Answer.model_json_schema()


@pytest.mark.asyncio
async def test_nvidia_provider_retries_invalid_json() -> None:
    client = FakeHTTPClient([
        response("not json"),
        response(json.dumps({"answer": "recovered"})),
    ])
    provider = NvidiaLLMProvider(settings(), client)

    result = await provider.generate_structured("system", "user", Answer)

    assert result.status == "available"
    assert result.value is not None
    assert result.value.answer == "recovered"
    assert len(client.calls) == 2
    second_messages = client.calls[1]["json"]["messages"]  # type: ignore[index]
    assert "valid JSON" in second_messages[0]["content"]
    for call in client.calls:
        request = call["json"]
        content = request["messages"][0]["content"]  # type: ignore[index]
        schema = content.split("\n", 2)[2]
        decoded_schema, _ = json.JSONDecoder().raw_decode(schema)
        assert decoded_schema == Answer.model_json_schema()
        assert request["max_tokens"] == 2048  # type: ignore[index]


@pytest.mark.asyncio
async def test_nvidia_provider_returns_safe_schema_failure() -> None:
    client = FakeHTTPClient([response(json.dumps({"wrong": "shape"})), response(json.dumps({"wrong": "shape"}))])
    provider = NvidiaLLMProvider(settings(), client)

    result = await provider.generate_structured("system", "user", Answer)

    assert result.status == "failed"
    assert result.value is None
    assert result.error_code == "nvidia_schema_invalid"
    assert result.warning is not None
    assert "schema" in result.warning


def test_missing_nvidia_key_does_not_construct_provider() -> None:
    assert build_llm_provider(Settings(llm_provider="nvidia")) is None
