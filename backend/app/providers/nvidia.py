from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.providers.protocols import LLMProvider, ProviderResponse


STRUCTURED_MAX_TOKENS = 2048


class NvidiaProviderError(RuntimeError):
    """A safe, user-facing provider failure without secret request details."""

    def __init__(self, message: str, code: str = "nvidia_provider_failed") -> None:
        super().__init__(message)
        self.code = code


class NvidiaLLMProvider:
    """OpenAI-compatible NVIDIA hosted inference adapter."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if client is None and not settings.nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY is required when the NVIDIA provider is enabled.")
        self.settings = settings
        self.client = client

    async def generate_structured(
        self,
        system_prompt: str,
        user_content: str,
        output_model: type[BaseModel],
        *,
        max_attempts: int | None = None,
    ) -> ProviderResponse[BaseModel]:
        last_error: NvidiaProviderError | None = None
        attempt_limit = max(1, max_attempts or self.settings.nvidia_max_retries + 1)
        for attempt in range(attempt_limit):
            try:
                payload = await self._request(system_prompt, user_content, output_model, attempt > 0)
                parsed = self._parse_payload(payload, output_model)
                return ProviderResponse(
                    status="available",
                    provider="nvidia",
                    value=parsed,
                    attempts=attempt + 1,
                    usage=self._usage(payload),
                )
            except NvidiaProviderError as error:
                last_error = error
                if error.code not in {"nvidia_invalid_json", "nvidia_schema_invalid"}:
                    break

        assert last_error is not None
        return ProviderResponse(
            status="failed",
            provider="nvidia",
            value=None,
            warning=str(last_error),
            error_code=last_error.code,
            attempts=attempt_limit,
        )

    async def _request(
        self, system_prompt: str, user_content: str, output_model: type[BaseModel], retry: bool
    ) -> dict[str, Any]:
        instructions = (
            "\nReturn only valid JSON matching the following JSON Schema. "
            "Do not include Markdown fences, commentary, or any text outside the JSON.\n"
            + json.dumps(output_model.model_json_schema())
        )
        suffix = " Return only valid JSON matching the requested schema." if retry else ""
        request = {
            "model": self.settings.nvidia_model,
            "messages": [
                {"role": "system", "content": system_prompt + instructions + suffix},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0,
            "max_tokens": STRUCTURED_MAX_TOKENS,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.nvidia_api_key or ''}",
            "Content-Type": "application/json",
        }
        try:
            if self.client is not None:
                response = await self.client.post(
                    f"{self.settings.nvidia_base_url}/chat/completions",
                    headers=headers,
                    json=request,
                )
            else:
                async with httpx.AsyncClient(timeout=self.settings.nvidia_timeout_seconds) as client:
                    response = await client.post(
                        f"{self.settings.nvidia_base_url}/chat/completions",
                        headers=headers,
                        json=request,
                    )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as error:
            raise NvidiaProviderError("NVIDIA inference timed out.", "nvidia_timeout") from error
        except httpx.HTTPStatusError as error:
            code = "nvidia_auth_failed" if error.response.status_code in {401, 403} else "nvidia_http_error"
            raise NvidiaProviderError("NVIDIA inference request failed.", code) from error
        except (httpx.HTTPError, ValueError) as error:
            raise NvidiaProviderError("NVIDIA inference request failed.", "nvidia_request_failed") from error
        if not isinstance(data, dict):
            raise NvidiaProviderError("NVIDIA returned an invalid response.", "nvidia_invalid_response")
        return data

    @staticmethod
    def _parse_payload(payload: dict[str, Any], output_model: type[BaseModel]) -> BaseModel:
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise NvidiaProviderError("NVIDIA returned no model content.", "nvidia_invalid_response") from error
        if not isinstance(content, str):
            raise NvidiaProviderError("NVIDIA returned non-text model content.", "nvidia_invalid_response")
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError as error:
            raise NvidiaProviderError("NVIDIA returned invalid JSON.", "nvidia_invalid_json") from error
        try:
            return output_model.model_validate(decoded)
        except ValidationError as error:
            raise NvidiaProviderError("NVIDIA returned JSON that did not match the required schema.", "nvidia_schema_invalid") from error

    @staticmethod
    def _usage(payload: dict[str, Any]) -> dict[str, int | float] | None:
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            return None
        return {
            key: value
            for key, value in usage.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
