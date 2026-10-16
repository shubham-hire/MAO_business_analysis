from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from hashlib import sha256
from time import monotonic
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

from tavily import AsyncTavilyClient

from app.config import Settings
from app.domain.run_snapshot import RunSnapshot
from app.providers.protocols import ProviderResponse
from app.schemas import SourceSnapshot


class TavilySearchClient(Protocol):
    async def search(self, query: str, **kwargs: Any) -> Mapping[str, Any]:
        ...


def _compact(value: str, limit: int) -> str:
    return " ".join(value.split())[:limit].strip()


def _bounded_query(parts: list[str]) -> str:
    query = _compact(" ".join(part for part in parts if part), 399)
    return query


def build_search_queries(run: RunSnapshot, stage: str, limit: int = 2) -> list[str]:
    definition = run.confirmed_market_definition or run.proposed_market_definition
    product = _compact(run.intake.product_name or run.intake.product_description, 100)
    category = _compact(definition.category if definition else "market", 100)
    region = _compact(run.intake.region, 80)
    customer = _compact(run.intake.target_customer, 80)

    if stage == "competitor_research":
        competitors = _compact(", ".join(definition.competitors if definition else run.intake.competitors), 100)
        queries = [
            _bounded_query([product, category, "competitors features pricing", region]),
            _bounded_query([competitors or product, "features pricing alternatives", region, customer]),
        ]
    else:
        queries = [
            _bounded_query([product, category, "market size statistics", region]),
            _bounded_query([product, category, "market growth adoption report", region, customer]),
        ]

    if limit <= 0:
        return []
    return [query for query in queries[:limit] if query]


def canonical_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def _publisher(url: str) -> str:
    hostname = urlsplit(url).hostname or "unknown publisher"
    return hostname.removeprefix("www.")


def _source_from_result(result: Mapping[str, Any], include_raw_content: bool) -> SourceSnapshot | None:
    url = str(result.get("url") or "").strip()
    if not url or urlsplit(url).scheme.lower() not in {"http", "https"}:
        return None

    normalized_url = canonical_url(url)
    content = str(result.get("content") or "").strip()
    raw_content = str(result.get("raw_content") or "").strip()
    permitted_excerpt = content or raw_content[:2000]
    if not permitted_excerpt:
        return None

    source_id = f"source-tavily-{sha256(normalized_url.encode()).hexdigest()[:16]}"
    return SourceSnapshot(
        id=source_id,
        title=_compact(str(result.get("title") or normalized_url), 300),
        url=normalized_url,
        publisher=_publisher(normalized_url),
        retrieval_date=datetime.now(timezone.utc),
        content_hash=sha256(
            (raw_content if include_raw_content and raw_content else permitted_excerpt).encode()
        ).hexdigest(),
        stored_text=raw_content if include_raw_content and raw_content else None,
        permitted_excerpt=permitted_excerpt,
        origin="tavily",
        provider="tavily",
    )


class TavilySourceProvider:
    """Collect source-level search results without asking Tavily for a synthesis."""

    def __init__(self, settings: Settings, client: TavilySearchClient | None = None) -> None:
        if client is None and not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required when the Tavily provider is enabled.")
        if client is not None:
            self.client = client
        else:
            kwargs: dict[str, str] = {"api_key": settings.tavily_api_key or ""}
            if settings.tavily_project_id:
                kwargs["project_id"] = settings.tavily_project_id
            self.client = AsyncTavilyClient(**kwargs)
        self.settings = settings

    async def collect(self, run: RunSnapshot, stage: str) -> ProviderResponse[list[SourceSnapshot]]:
        queries = build_search_queries(run, stage, self.settings.tavily_max_queries_per_stage)
        return await self.collect_queries(run, stage, queries)

    async def collect_queries(
        self,
        _run: RunSnapshot,
        _stage: str,
        queries: list[str],
        *,
        max_queries: int | None = None,
        max_sources: int | None = None,
        deadline: float | None = None,
    ) -> ProviderResponse[list[SourceSnapshot]]:
        if not queries:
            return ProviderResponse(
                status="unavailable",
                provider="tavily",
                value=[],
                warning=f"Tavily could not build a query for the {_stage} stage.",
                error_code="tavily_empty_query",
            )

        selected_queries = queries[: min(
            self.settings.tavily_max_queries_per_stage,
            max_queries if max_queries is not None else self.settings.tavily_max_queries_per_stage,
        )]
        if deadline is not None and monotonic() >= deadline:
            return ProviderResponse(
                status="partial",
                provider="tavily",
                value=[],
                warning="Tavily search budget timed out before a query could start.",
                error_code="tavily_timeout",
                usage={"query_count": 0, "source_count": 0},
            )

        responses = await asyncio.gather(
            *(
                self._search(
                    query,
                    max_results=max_sources,
                    deadline=deadline,
                )
                for query in selected_queries
            ),
            return_exceptions=True,
        )
        sources: list[SourceSnapshot] = []
        source_ids: set[str] = set()
        warnings: list[str] = []
        discarded = 0

        for response in responses:
            if isinstance(response, Exception):
                self._add_warning(warnings, self._warning_for_exception(response))
                continue
            if not isinstance(response, Mapping):
                self._add_warning(warnings, "Tavily returned an invalid response payload.")
                continue
            results = response.get("results", [])
            if not isinstance(results, list):
                self._add_warning(warnings, "Tavily returned an invalid results payload.")
                continue
            for result in results:
                if not isinstance(result, Mapping):
                    discarded += 1
                    continue
                source = _source_from_result(result, self.settings.tavily_include_raw_content)
                if source is None:
                    discarded += 1
                    continue
                if source.id not in source_ids:
                    source_ids.add(source.id)
                    sources.append(source)

        if discarded:
            self._add_warning(warnings, f"Tavily discarded {discarded} unusable search result(s).")
        if not sources:
            self._add_warning(warnings, "Tavily returned no usable source snapshots.")

        warning = " ".join(warnings) if warnings else None
        return ProviderResponse(
            status="available" if sources and not warnings else "partial" if sources else "unavailable",
            provider="tavily",
            value=sources,
            warning=warning,
            error_code=self._error_code(warnings),
            usage={"query_count": len(selected_queries), "source_count": len(sources)},
        )

    async def _search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        deadline: float | None = None,
    ) -> Mapping[str, Any]:
        timeout = self.settings.tavily_timeout_seconds
        if deadline is not None:
            timeout = min(timeout, max(0.001, deadline - monotonic()))
        return await asyncio.wait_for(
            self.client.search(
                query=query,
                search_depth=self.settings.tavily_search_depth,
                topic="general",
                max_results=min(self.settings.tavily_max_results, max_results or self.settings.tavily_max_results),
                include_answer=False,
                include_images=False,
                include_raw_content=self.settings.tavily_include_raw_content,
            ),
            timeout=timeout,
        )

    @staticmethod
    def _add_warning(warnings: list[str], warning: str) -> None:
        if warning not in warnings:
            warnings.append(warning)

    @staticmethod
    def _warning_for_exception(error: Exception) -> str:
        if isinstance(error, asyncio.TimeoutError):
            return "A Tavily search timed out; remaining results were preserved."
        name = type(error).__name__.lower()
        if "auth" in name or "permission" in name:
            return "Tavily authentication failed; remaining results were preserved."
        if "rate" in name or "limit" in name:
            return "Tavily rate limit reached; remaining results were preserved."
        return "A Tavily search failed; remaining results were preserved."

    @staticmethod
    def _error_code(warnings: list[str]) -> str | None:
        if any("timed out" in warning for warning in warnings):
            return "tavily_timeout"
        if any("authentication" in warning for warning in warnings):
            return "tavily_auth_failed"
        if any("rate limit" in warning for warning in warnings):
            return "tavily_rate_limited"
        if any("no usable" in warning for warning in warnings):
            return "tavily_empty_results"
        return "tavily_partial" if warnings else None
