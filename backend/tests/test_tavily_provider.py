from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.config import Settings, build_source_provider
from app.domain.run_snapshot import RunSnapshot
from app.orchestration.stages import collect_sources
from app.providers.offline import UnavailableSourceProvider
from app.providers.tavily import TavilySourceProvider, build_search_queries
from app.schemas import MarketDefinitionProposal, ProductIntake, RunStatus


def make_run() -> RunSnapshot:
    intake = ProductIntake.model_validate({
        "productName": "Local delivery marketplace",
        "productDescription": "A delivery marketplace for independent local stores.",
        "targetCustomer": "Independent retailers",
        "region": "India",
        "priceRange": {"minimum": 100, "maximum": 500, "currency": "INR"},
        "competitors": ["Store A"],
    })
    definition = MarketDefinitionProposal(
        category="Local delivery market",
        included_boundaries="Independent retailers in India",
        excluded_boundaries="Enterprise-only offerings",
        competitors=["Store A"],
    )
    timestamp = datetime.now(timezone.utc)
    return RunSnapshot(
        id="run-tavily-test",
        owner_id="demo-user",
        intake=intake,
        created_at=timestamp,
        updated_at=timestamp,
        status=RunStatus.QUEUED,
        market_definition=definition.category,
        proposed_market_definition=definition,
        confirmed_market_definition=definition,
    )


class FakeTavilyClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def search(self, query: str, **kwargs: object) -> dict[str, object]:
        self.calls.append((query, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response  # type: ignore[return-value]


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "source_provider": "tavily",
        "tavily_api_key": "test-key",
        "tavily_max_results": 3,
        "tavily_max_queries_per_stage": 2,
        "tavily_timeout_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def result(url: str = "https://example.com/report", content: str = "Market demand grew.") -> dict[str, object]:
    return {"title": "Market report", "url": url, "content": content, "score": 0.91}


def test_queries_are_bounded_and_use_confirmed_market_context() -> None:
    queries = build_search_queries(make_run(), "competitor_research", limit=2)

    assert len(queries) == 2
    assert all(len(query) < 400 for query in queries)
    assert "Local delivery market" in queries[0]
    assert "India" in queries[0]
    assert "Store A" in queries[1]


@pytest.mark.asyncio
async def test_successful_results_map_to_deduplicated_source_snapshots() -> None:
    client = FakeTavilyClient([
        {"results": [result()]},
        {"results": [result()]},
    ])
    provider = TavilySourceProvider(settings(), client)

    response = await provider.collect(make_run(), "market_statistics")

    assert response.status == "available"
    assert response.error_code is None
    assert len(response.value) == 1
    source = response.value[0]
    assert source.provider == "tavily"
    assert source.origin == "tavily"
    assert source.publisher == "example.com"
    assert source.stored_text is None
    assert source.permitted_excerpt == "Market demand grew."
    assert client.calls[0][1]["include_answer"] is False
    assert client.calls[0][1]["max_results"] == 3


@pytest.mark.asyncio
async def test_raw_content_can_be_retained_when_explicitly_enabled() -> None:
    client = FakeTavilyClient([
        {"results": [{
            **result(content="Short excerpt."),
            "raw_content": "The complete retained source text.",
        }]},
        {"results": []},
    ])
    provider = TavilySourceProvider(settings(tavily_include_raw_content=True), client)

    response = await provider.collect(make_run(), "market_statistics")

    assert response.value[0].stored_text == "The complete retained source text."
    assert response.value[0].permitted_excerpt == "Short excerpt."


@pytest.mark.asyncio
async def test_one_failed_query_preserves_successful_results_as_partial() -> None:
    client = FakeTavilyClient([
        TimeoutError(),
        {"results": [result(url="https://example.com/other", content="A second source.")]},
    ])
    provider = TavilySourceProvider(settings(), client)

    response = await provider.collect(make_run(), "market_statistics")

    assert response.status == "partial"
    assert response.error_code == "tavily_timeout"
    assert len(response.value) == 1
    assert response.warning is not None
    assert "timed out" in response.warning


@pytest.mark.asyncio
async def test_malformed_results_are_discarded_without_raising() -> None:
    client = FakeTavilyClient([
        {"results": [{"title": "Missing URL", "content": "Not enough metadata."}]},
        {"results": []},
    ])
    provider = TavilySourceProvider(settings(), client)

    response = await provider.collect(make_run(), "market_statistics")

    assert response.status == "unavailable"
    assert response.error_code == "tavily_empty_results"
    assert response.value == []
    assert response.warning is not None
    assert "no usable" in response.warning


@pytest.mark.asyncio
async def test_empty_queries_return_structured_tavily_error() -> None:
    client = FakeTavilyClient([])
    provider = TavilySourceProvider(settings(), client)

    response = await provider.collect_queries(make_run(), "market_statistics", [])

    assert response.status == "unavailable"
    assert response.provider == "tavily"
    assert response.value == []
    assert response.warning == "Tavily could not build a query for the market_statistics stage."
    assert response.error_code == "tavily_empty_query"
    assert client.calls == []


@pytest.mark.asyncio
async def test_stage_maps_provider_error_code_and_warning() -> None:
    client = FakeTavilyClient([TimeoutError(), TimeoutError()])
    provider = TavilySourceProvider(settings(), client)

    stage = await collect_sources(make_run(), "market_statistics", provider)

    assert stage.state == "partial"
    assert stage.provider == "tavily"
    assert stage.error_code == "tavily_timeout"
    assert stage.warning is not None


@pytest.mark.asyncio
async def test_missing_tavily_key_uses_honest_offline_provider() -> None:
    provider = build_source_provider(Settings(source_provider="tavily"))

    assert isinstance(provider, UnavailableSourceProvider)
    response = await provider.collect(make_run(), "market_statistics")
    assert response.status == "unavailable"
    assert response.warning is not None
    assert "TAVILY_API_KEY" in response.warning
