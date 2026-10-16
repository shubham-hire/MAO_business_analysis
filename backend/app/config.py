from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from app.providers.offline import UnavailableSourceProvider
from app.providers.protocols import LLMProvider, SourceProvider


def _positive_int(value: str | None, default: int, maximum: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return default
    return min(max(parsed, 1), maximum)


def _positive_float(value: str | None, default: float, maximum: float) -> float:
    try:
        parsed = float(value or "")
    except ValueError:
        return default
    return min(max(parsed, 0.1), maximum)


def _flag(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings with an offline-safe default provider."""

    source_provider: str = "offline"
    llm_provider: str = "offline"
    tavily_api_key: str | None = None
    tavily_project_id: str | None = None
    tavily_search_depth: str = "advanced"
    tavily_max_results: int = 5
    tavily_max_queries_per_stage: int = 2
    tavily_timeout_seconds: float = 30.0
    tavily_include_raw_content: bool = True
    tavily_live_smoke: bool = False
    market_agent_max_iterations: int = 2
    market_agent_max_queries: int = 4
    market_agent_max_model_calls: int = 4
    market_agent_max_sources: int = 10
    market_agent_timeout_seconds: float = 120.0
    nvidia_api_key: str | None = None
    nvidia_model: str = "nvidia/nemotron-3-super-120b-a12b"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_timeout_seconds: float = 60.0
    nvidia_max_retries: int = 2

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if environ is None else environ
        depth = env.get("TAVILY_SEARCH_DEPTH", "advanced").strip().lower()
        if depth not in {"ultra-fast", "fast", "basic", "advanced"}:
            depth = "advanced"
        return cls(
            source_provider=env.get("SOURCE_PROVIDER", "offline").strip().lower() or "offline",
            llm_provider=env.get("LLM_PROVIDER", "offline").strip().lower() or "offline",
            tavily_api_key=env.get("TAVILY_API_KEY") or None,
            tavily_project_id=env.get("TAVILY_PROJECT_ID") or None,
            tavily_search_depth=depth,
            tavily_max_results=_positive_int(env.get("TAVILY_MAX_RESULTS"), 5, 20),
            tavily_max_queries_per_stage=_positive_int(env.get("TAVILY_MAX_QUERIES_PER_STAGE"), 2, 5),
            tavily_timeout_seconds=_positive_float(env.get("TAVILY_TIMEOUT_SECONDS"), 30.0, 120.0),
            tavily_include_raw_content=_flag(env.get("TAVILY_INCLUDE_RAW_CONTENT"), True),
            tavily_live_smoke=_flag(env.get("TAVILY_LIVE_SMOKE")),
            market_agent_max_iterations=_positive_int(env.get("MARKET_AGENT_MAX_ITERATIONS"), 2, 5),
            market_agent_max_queries=_positive_int(env.get("MARKET_AGENT_MAX_QUERIES"), 4, 20),
            market_agent_max_model_calls=_positive_int(env.get("MARKET_AGENT_MAX_MODEL_CALLS"), 4, 10),
            market_agent_max_sources=_positive_int(env.get("MARKET_AGENT_MAX_SOURCES"), 10, 50),
            market_agent_timeout_seconds=_positive_float(env.get("MARKET_AGENT_TIMEOUT_SECONDS"), 120.0, 300.0),
            nvidia_api_key=env.get("NVIDIA_API_KEY") or None,
            nvidia_model=env.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b").strip(),
            nvidia_base_url=env.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/"),
            nvidia_timeout_seconds=_positive_float(env.get("NVIDIA_TIMEOUT_SECONDS"), 60.0, 180.0),
            nvidia_max_retries=_positive_int(env.get("NVIDIA_MAX_RETRIES"), 2, 5),
        )


def build_source_provider(settings: Settings) -> SourceProvider:
    if settings.source_provider != "tavily":
        return UnavailableSourceProvider()

    if not settings.tavily_api_key:
        return UnavailableSourceProvider(
            warning="Tavily is enabled but TAVILY_API_KEY is missing; no external evidence was collected."
        )

    from app.providers.tavily import TavilySourceProvider

    return TavilySourceProvider(settings)


def build_llm_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_provider != "nvidia":
        return None
    if not settings.nvidia_api_key:
        return None

    from app.providers.nvidia import NvidiaLLMProvider

    return NvidiaLLMProvider(settings)
