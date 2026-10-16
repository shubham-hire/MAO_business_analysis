from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from app.domain.run_snapshot import RunSnapshot
from app.schemas import SourceSnapshot


T = TypeVar("T")


@dataclass
class ProviderResponse(Generic[T]):
    status: str
    provider: str
    value: T
    warning: str | None = None
    usage: dict[str, int | float] | None = None


class SourceProvider(Protocol):
    async def collect(self, run: RunSnapshot, stage: str) -> ProviderResponse[list[SourceSnapshot]]:
        ...


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        system_prompt: str,
        user_content: str,
        output_model: type[BaseModel],
    ) -> ProviderResponse[BaseModel]:
        ...
