from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.agents.contracts import AgentBudget, AgentContext
from app.agents.market_research import MarketResearchAgent, SearchPlan
from app.providers.offline import fixture_source
from app.providers.protocols import ProviderResponse
from app.schemas import MarketDefinitionProposal, ProductIntake


def intake() -> ProductIntake:
    return ProductIntake.model_validate({
        "productName": "Local delivery marketplace",
        "productDescription": "A delivery marketplace for independent local stores.",
        "targetCustomer": "Independent retailers",
        "region": "India",
        "priceRange": {"minimum": 100, "maximum": 500, "currency": "INR"},
    })


def definition() -> MarketDefinitionProposal:
    return MarketDefinitionProposal(
        category="Local delivery market",
        included_boundaries="Independent retailers in India",
        excluded_boundaries="Enterprise-only offerings",
        competitors=[],
    )


class SequencedSourceProvider:
    def __init__(self, sources: list[object], delay: float = 0, reported_query_count: int | None = None) -> None:
        self.sources = sources
        self.delay = delay
        self.reported_query_count = reported_query_count
        self.calls: list[list[str]] = []
        self.options: list[dict[str, object]] = []

    async def collect_queries(self, _run, _stage, queries, **kwargs):
        self.calls.append(list(queries))
        self.options.append(kwargs)
        if self.delay:
            await asyncio.sleep(self.delay)
        value = self.sources[len(self.calls) - 1] if len(self.calls) <= len(self.sources) else []
        return ProviderResponse(
            status="available" if value else "partial",
            provider="fake-tavily",
            value=value,
            usage={"query_count": self.reported_query_count if self.reported_query_count is not None else len(queries)},
        )


class AdaptiveLLM:
    def __init__(self, initial_queries: list[str] | None = None) -> None:
        self.calls: list[str] = []
        self.options: list[dict[str, object]] = []
        self.initial_queries = initial_queries or ["initial market size India"]

    async def generate_structured(self, _system, _user, output_model, **kwargs):
        self.calls.append(output_model.__name__)
        self.options.append(kwargs)
        if output_model is SearchPlan:
            value = SearchPlan(queries=self.initial_queries)
        elif output_model.__name__ == "CoverageDecision":
            value = SimpleNamespace(
                action="search" if self.calls.count("CoverageDecision") == 1 else "stop",
                queries=["regional market growth India"],
                covered_dimensions=["market_size"],
                missing_dimensions=[] if self.calls.count("CoverageDecision") > 1 else ["market_growth"],
                summary="Coverage reviewed.",
            )
        else:
            raise AssertionError(f"Unexpected model: {output_model.__name__}")
        return ProviderResponse(status="available", provider="fake-nvidia", value=value)


def context(provider, llm) -> AgentContext:
    run = SimpleNamespace(
        market_definition=definition().category,
        proposed_market_definition=definition(),
        confirmed_market_definition=definition(),
        intake=intake(),
    )
    return AgentContext(run=run, source_provider=provider, llm_provider=llm)


@pytest.mark.asyncio
async def test_market_agent_uses_a_follow_up_search_when_coverage_is_incomplete() -> None:
    first = fixture_source("Initial market source", "India market size was reported.")
    second = fixture_source("Regional growth source", "India market growth was reported.")
    provider = SequencedSourceProvider([[first], [second]])
    llm = AdaptiveLLM()

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=4, max_model_calls=4, max_sources=10),
    )

    assert len(provider.calls) == 2
    assert llm.calls == ["SearchPlan", "CoverageDecision", "CoverageDecision"]
    assert result.iterations == 2
    assert result.query_count == 2
    assert result.model_call_count == 3
    assert result.source_count == 2
    assert result.coverage is not None
    assert result.coverage.covered_dimensions == ["market_size"]


@pytest.mark.asyncio
async def test_market_agent_enforces_cumulative_query_budget() -> None:
    source = fixture_source("Market source", "A market signal.")
    provider = SequencedSourceProvider([[source], [source]])
    llm = AdaptiveLLM()

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=1, max_model_calls=4, max_sources=10),
    )

    assert sum(len(call) for call in provider.calls) == 1
    assert result.query_count == 1
    assert result.budget_exhausted is True


@pytest.mark.asyncio
async def test_market_agent_enforces_retained_source_budget_before_persisting() -> None:
    sources = [fixture_source(f"Source {index}", f"Market source {index}.") for index in range(5)]
    provider = SequencedSourceProvider([sources])
    llm = AdaptiveLLM()

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=1, max_queries=1, max_model_calls=1, max_sources=2),
    )

    assert result.source_count == 2
    assert len(result.sources) == 2
    assert provider.options[0]["max_sources"] == 2


@pytest.mark.asyncio
async def test_market_agent_does_not_search_after_source_budget_is_exhausted() -> None:
    source = fixture_source("Market source", "A market signal.")
    provider = SequencedSourceProvider([[source], [source]])
    llm = AdaptiveLLM()

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=4, max_model_calls=4, max_sources=1),
    )

    assert len(provider.calls) == 1
    assert result.source_count == 1
    assert result.budget_exhausted is True


@pytest.mark.asyncio
async def test_market_agent_passes_remaining_model_attempt_budget_to_provider() -> None:
    source = fixture_source("Market source", "A market signal.")
    provider = SequencedSourceProvider([[source]])
    llm = AdaptiveLLM()

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=1, max_queries=1, max_model_calls=2, max_sources=10),
    )

    assert result.model_call_count == 2
    assert [option["max_attempts"] for option in llm.options] == [2, 1]


@pytest.mark.asyncio
async def test_market_agent_reports_actual_iterations_without_an_llm() -> None:
    source = fixture_source("Market source", "A market signal.")
    provider = SequencedSourceProvider([[source]])

    result = await MarketResearchAgent().run(
        context(provider, None),
        AgentBudget(max_iterations=2, max_queries=4, max_model_calls=4, max_sources=10),
    )

    assert result.iterations == 1


@pytest.mark.asyncio
async def test_market_agent_uses_provider_query_usage_for_actual_request_count() -> None:
    source = fixture_source("Market source", "A market signal.")
    provider = SequencedSourceProvider([[source]], reported_query_count=1)
    llm = AdaptiveLLM(initial_queries=["query one", "query two"])

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=1, max_queries=4, max_model_calls=1, max_sources=10),
    )

    assert result.query_count == 1


@pytest.mark.asyncio
async def test_market_agent_enforces_total_timeout() -> None:
    provider = SequencedSourceProvider([[]], delay=0.05)
    llm = AdaptiveLLM()

    result = await MarketResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=1, max_model_calls=1, max_sources=10, timeout_seconds=0.01),
    )

    assert result.status == "partial"
    assert result.error_code == "market_research_timeout"
    assert result.budget_exhausted is True
