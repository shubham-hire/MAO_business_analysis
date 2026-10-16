from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.agents.competitor_research import CompetitorResearchAgent, CoverageDecision, SearchPlan
from app.agents.contracts import AgentBudget, AgentContext
from app.providers.offline import fixture_source
from app.providers.protocols import ProviderResponse
from app.schemas import CompetitorObservation, MarketDefinitionProposal, ProductIntake


def intake() -> ProductIntake:
    return ProductIntake.model_validate({
        "productName": "Local delivery marketplace",
        "productDescription": "A delivery marketplace for independent local stores.",
        "targetCustomer": "Independent retailers",
        "region": "India",
        "priceRange": {"minimum": 100, "maximum": 500, "currency": "INR"},
        "competitors": ["Known Co"],
    })


def definition() -> MarketDefinitionProposal:
    return MarketDefinitionProposal(
        category="Local delivery market",
        included_boundaries="Independent retailers in India",
        excluded_boundaries="Enterprise-only offerings",
        competitors=["Known Co"],
    )


def context(provider: object, llm: object | None) -> AgentContext:
    run = SimpleNamespace(
        market_definition=definition().category,
        proposed_market_definition=definition(),
        confirmed_market_definition=definition(),
        intake=intake(),
    )
    return AgentContext(run=run, source_provider=provider, llm_provider=llm)


class SequencedSourceProvider:
    def __init__(self, responses: list[object], delay: float = 0) -> None:
        self.responses = responses
        self.delay = delay
        self.calls: list[list[str]] = []
        self.options: list[dict[str, object]] = []

    async def collect_queries(self, _run, _stage, queries, **kwargs):
        self.calls.append(list(queries))
        self.options.append(kwargs)
        if self.delay:
            await asyncio.sleep(self.delay)
        response = self.responses[len(self.calls) - 1] if len(self.calls) <= len(self.responses) else []
        if isinstance(response, Exception):
            raise response
        if isinstance(response, ProviderResponse):
            return response
        return ProviderResponse(
            status="available" if response else "partial",
            provider="fake-tavily",
            value=response,
            usage={"query_count": len(queries)},
        )


class CompetitorLLM:
    def __init__(self, decisions: list[CoverageDecision]) -> None:
        self.decisions = decisions
        self.calls: list[str] = []
        self.options: list[dict[str, object]] = []

    async def generate_structured(self, _system, _user, output_model, **kwargs):
        self.calls.append(output_model.__name__)
        self.options.append(kwargs)
        if output_model is SearchPlan:
            return ProviderResponse(
                status="available",
                provider="fake-nvidia",
                value=SearchPlan(queries=["Known Co features pricing India", "India delivery alternatives"]),
            )
        if output_model is CoverageDecision:
            decision = self.decisions.pop(0)
            return ProviderResponse(status="available", provider="fake-nvidia", value=decision)
        raise AssertionError(f"Unexpected model: {output_model.__name__}")


def observation(
    name: str,
    source_id: str,
    *,
    source_type: str = "discovered",
    pricing: str = "not_found",
) -> CompetitorObservation:
    return CompetitorObservation(
        competitor_name=name,
        source_type=source_type,
        identity=f"{name} marketplace",
        target_customer="Independent retailers",
        features=["inventory", "delivery"],
        positioning=f"{name} for local retailers",
        published_pricing=pricing,
        billing_period="monthly" if pricing not in {"unknown", "not_found"} else "not_found",
        currency="INR" if pricing not in {"unknown", "not_found"} else "not_found",
        regional_availability="India",
        source_ids=[source_id],
    )


@pytest.mark.asyncio
async def test_competitor_agent_distinguishes_listed_and_discovered_competitors_and_keeps_missing_price_unknown() -> None:
    source = fixture_source(
        "Competitor comparison",
        "Known Co serves independent retailers in India. Rival Co offers inventory and delivery features. Pricing is not published.",
    )
    provider = SequencedSourceProvider([[source]])
    llm = CompetitorLLM([
        CoverageDecision(
            action="stop",
            covered_dimensions=["identity", "target_customer", "features", "positioning", "regional_availability"],
            missing_dimensions=["published_pricing", "billing_period", "currency"],
            summary="Identity and regional coverage are available; pricing is not published.",
            observations=[
                observation("Known Co", source.id, source_type="user_listed"),
                observation("Rival Co", source.id, pricing="$999/month"),
            ],
        ),
    ])

    result = await CompetitorResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=1, max_queries=2, max_model_calls=2, max_sources=10),
    )

    by_name = {item.competitor_name: item for item in result.observations}
    assert result.status == "partial"
    assert result.sources == [source]
    assert by_name["Known Co"].source_type == "user_listed"
    assert by_name["Rival Co"].source_type == "discovered"
    assert by_name["Known Co"].published_pricing == "not_found"
    assert by_name["Rival Co"].published_pricing in {"unknown", "not_found"}
    assert by_name["Rival Co"].verification_status == "unchecked"
    assert result.coverage is not None
    assert "published_pricing" in result.coverage.missing_dimensions


@pytest.mark.asyncio
async def test_competitor_agent_adapts_with_a_bounded_follow_up_and_merges_observations() -> None:
    first = fixture_source("Known Co profile", "Known Co serves independent retailers in India.")
    second = fixture_source("Alternative profile", "Rival Co offers inventory tools and is available in India.")
    provider = SequencedSourceProvider([[first], [second]])
    llm = CompetitorLLM([
        CoverageDecision(
            action="search",
            queries=["Rival Co features regional availability"],
            covered_dimensions=["identity", "target_customer"],
            missing_dimensions=["features", "positioning", "regional_availability"],
            summary="A follow-up is needed for alternative features and availability.",
            observations=[observation("Known Co", first.id, source_type="user_listed")],
        ),
        CoverageDecision(
            action="stop",
            covered_dimensions=["identity", "target_customer", "features", "regional_availability"],
            missing_dimensions=["positioning", "published_pricing", "billing_period", "currency"],
            summary="The follow-up added an alternative profile.",
            observations=[observation("Rival Co", second.id)],
        ),
    ])

    result = await CompetitorResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=3, max_model_calls=3, max_sources=10),
    )

    assert len(provider.calls) == 2
    assert llm.calls == ["SearchPlan", "CoverageDecision", "CoverageDecision"]
    assert result.iterations == 2
    assert result.query_count == 3
    assert result.model_call_count == 3
    assert {item.competitor_name for item in result.observations} == {"Known Co", "Rival Co"}


@pytest.mark.asyncio
async def test_competitor_agent_enforces_cumulative_query_budget() -> None:
    source = fixture_source("Known Co profile", "Known Co serves independent retailers in India.")
    provider = SequencedSourceProvider([[source], [source]])
    llm = CompetitorLLM([
        CoverageDecision(
            action="search",
            queries=["follow-up one", "follow-up two"],
            missing_dimensions=["features"],
            observations=[observation("Known Co", source.id, source_type="user_listed")],
        ),
    ])

    result = await CompetitorResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=1, max_model_calls=2, max_sources=10),
    )

    assert sum(len(call) for call in provider.calls) == 1
    assert result.query_count == 1
    assert result.budget_exhausted is True
    assert result.observations[0].competitor_name == "Known Co"


@pytest.mark.asyncio
async def test_competitor_agent_preserves_sources_and_observations_after_partial_provider_failure() -> None:
    source = fixture_source("Known Co profile", "Known Co serves independent retailers in India.")
    provider = SequencedSourceProvider([
        ProviderResponse(
            status="partial",
            provider="fake-tavily",
            value=[source],
            warning="One competitor query failed; successful source retained.",
            error_code="provider_partial",
            usage={"query_count": 1},
        ),
    ])
    llm = CompetitorLLM([
        CoverageDecision(
            action="stop",
            observations=[observation("Known Co", source.id, source_type="user_listed")],
            missing_dimensions=["published_pricing"],
        ),
    ])

    result = await CompetitorResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=1, max_queries=2, max_model_calls=2, max_sources=10),
    )

    assert result.sources == [source]
    assert [item.competitor_name for item in result.observations] == ["Known Co"]
    assert any("query failed" in warning.message for warning in result.warnings)
    assert result.status == "partial"


@pytest.mark.asyncio
async def test_competitor_agent_preserves_first_round_artifacts_when_follow_up_provider_raises() -> None:
    source = fixture_source("Known Co profile", "Known Co serves independent retailers in India.")
    provider = SequencedSourceProvider([[source], RuntimeError("second query failed")])
    llm = CompetitorLLM([
        CoverageDecision(
            action="search",
            queries=["follow-up profile"],
            observations=[observation("Known Co", source.id, source_type="user_listed")],
        ),
    ])

    result = await CompetitorResearchAgent().run(
        context(provider, llm),
        AgentBudget(max_iterations=2, max_queries=3, max_model_calls=2, max_sources=10),
    )

    assert result.sources == [source]
    assert result.observations[0].competitor_name == "Known Co"
    assert any("provider" in warning.message.lower() for warning in result.warnings)


@pytest.mark.asyncio
async def test_competitor_agent_returns_partial_timeout_without_losing_budget_accounting() -> None:
    provider = SequencedSourceProvider([[]], delay=0.05)

    result = await CompetitorResearchAgent().run(
        context(provider, None),
        AgentBudget(max_iterations=2, max_queries=1, max_model_calls=1, max_sources=10, timeout_seconds=0.01),
    )

    assert result.status == "partial"
    assert result.error_code == "competitor_research_timeout"
    assert result.budget_exhausted is True
    assert result.query_count == 0
