from __future__ import annotations

import asyncio

import pytest

from app.domain.run_service import RunService
from app.infrastructure.memory_repository import MemoryRunRepository
from app.agents.claim_extraction import ClaimBatch, ClaimCandidate
from app.agents.market_research import CoverageDecision as MarketCoverageDecision, SearchPlan as MarketSearchPlan
from app.agents.competitor_research import CoverageDecision as CompetitorCoverageDecision, SearchPlan as CompetitorSearchPlan
from app.orchestration.pipeline import DeterministicPipeline, PipelineResult
from app.orchestration.runner import RunRunner
from app.orchestration.stages import verify_claims
from app.providers.offline import StaticFixtureSourceProvider, fixture_source
from app.providers.protocols import ProviderResponse
from app.schemas import Claim, ClaimType, CompetitorObservation, MarketDefinitionProposal, ProductIntake, VerificationStatus

SearchPlan = MarketSearchPlan
CoverageDecision = MarketCoverageDecision


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


@pytest.mark.asyncio
async def test_fixture_pipeline_persists_exact_evidence() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    source = fixture_source("Offline market note", "Independent retailers reported repeat delivery demand.")
    runner = RunRunner(service, DeterministicPipeline(StaticFixtureSourceProvider([source])))
    run = await service.create_run(intake(), "demo-user")
    await service.confirm_market_definition(run.id, "demo-user", definition())

    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert detail.sources[0].origin == "offline_fixture"
    assert detail.claims[0].verification_status == "verified"
    assert detail.evidence[0].excerpt_match == "exact"
    assert detail.evidence[0].excerpt in detail.sources[0].stored_text
    assert detail.verified_claim_count == 1
    assert detail.report_available is False
    assert [stage.name for stage in detail.stages] == [
        "market_statistics",
        "competitor_research",
        "customer_voice",
        "claim_extraction",
        "evidence_verification",
        "assessment",
        "report_generation",
    ]


@pytest.mark.asyncio
async def test_unavailable_provider_preserves_empty_artifacts_and_stage_warnings() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    runner = RunRunner(service)
    run = await service.create_run(intake(), "demo-user")
    await service.confirm_market_definition(run.id, "demo-user", definition())

    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert detail.sources == []
    assert detail.claims == []
    assert detail.evidence == []
    assert detail.status == "partial"
    assert any(stage.name == "market_statistics" and stage.state == "partial" for stage in detail.stages)
    assert any("providers are not configured" in warning.message for warning in detail.warnings)


@pytest.mark.asyncio
async def test_permitted_excerpt_can_support_exact_evidence() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    source = fixture_source("Excerpt-only note", "A fact retained in the permitted excerpt.").model_copy(
        update={"stored_text": None, "permitted_excerpt": "A fact retained in the permitted excerpt."}
    )
    runner = RunRunner(service, DeterministicPipeline(StaticFixtureSourceProvider([source])))
    run = await service.create_run(intake(), "demo-user")
    await service.confirm_market_definition(run.id, "demo-user", definition())

    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert detail.verified_claim_count == 1
    assert detail.evidence[0].start_offset == 0


def test_exact_evidence_uses_permitted_excerpt_when_stored_text_does_not_match() -> None:
    source = fixture_source("Excerpt-only note", "Stored source body without the claim.").model_copy(
        update={"permitted_excerpt": "Allowed excerpt: repeat delivery demand grew."}
    )
    claim_text = "repeat delivery demand grew."
    claim = Claim(
        id="claim-permitted-excerpt",
        stable_key="source:permitted-excerpt",
        text=claim_text,
        subject="Local delivery marketplace",
        attribute="market_signal",
        region="India",
        claim_type=ClaimType.SOURCE_REPORTED_FACT,
        source_ids=[source.id],
    )

    output = verify_claims([claim], [source])

    assert output.claims[0].verification_status == VerificationStatus.VERIFIED
    assert output.evidence[0].excerpt == claim_text
    assert output.evidence[0].start_offset == 17
    assert output.evidence[0].end_offset == 45


@pytest.mark.asyncio
async def test_same_title_fixtures_with_different_text_remain_distinct() -> None:
    first = fixture_source("Same title", "First source text.")
    second = fixture_source("Same title", "Second source text.")

    assert first.id != second.id

    repository = MemoryRunRepository()
    service = RunService(repository)
    runner = RunRunner(service, DeterministicPipeline(StaticFixtureSourceProvider([first, second])))
    run = await service.create_run(intake(), "demo-user")
    await service.confirm_market_definition(run.id, "demo-user", definition())

    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert len(detail.sources) == 2
    assert len(detail.evidence) == 2


class ExplodingPipeline:
    async def run(self, _run):
        raise RuntimeError("provider exploded")


class FailedResultPipeline:
    async def run(self, _run):
        return PipelineResult(outcome="failed", warnings=["A required provider failed."])


class PrematureCompletionPipeline:
    async def run(self, _run):
        return PipelineResult(outcome="completed", report_available=True)


async def queued_run(service: RunService):
    run = await service.create_run(intake(), "demo-user")
    await service.confirm_market_definition(run.id, "demo-user", definition())
    return run


@pytest.mark.asyncio
async def test_pipeline_exception_persists_failed_run_and_stage_event() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    run = await queued_run(service)

    await RunRunner(service, ExplodingPipeline()).run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")
    events = await repository.events(run.id, "demo-user")

    assert detail.status == "failed"
    assert detail.stages[0].state == "failed"
    assert events is not None
    assert any(event.type == "stage.failed" for event in events)
    assert any(event.type == "run.status_changed" and event.status == "failed" for event in events)


@pytest.mark.asyncio
async def test_failed_pipeline_result_is_not_downgraded_to_partial() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    run = await queued_run(service)

    await RunRunner(service, FailedResultPipeline()).run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert detail.status == "failed"
    assert detail.stages[0].state == "failed"


@pytest.mark.asyncio
async def test_incomplete_completed_result_is_marked_partial() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    run = await queued_run(service)

    await RunRunner(service, PrematureCompletionPipeline()).run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert detail.status == "partial"
    assert any("before all required stages" in warning.message for warning in detail.warnings)


class FakeStructuredLLM:
    def __init__(self, source_id: str, excerpt: str) -> None:
        self.source_id = source_id
        self.excerpt = excerpt
        self.calls: list[str] = []

    async def generate_structured(self, _system: str, _user: str, output_model, **_kwargs):
        self.calls.append(output_model.__name__)
        if output_model.__name__ == "SearchPlan":
            return ProviderResponse(
                status="available",
                provider="nvidia",
                value=output_model(queries=["local delivery market statistics India"]),
                usage={"total_tokens": 10},
            )
        if output_model.__name__ == "CoverageDecision":
            return ProviderResponse(
                status="available",
                provider="nvidia",
                value=output_model(
                    action="stop",
                    covered_dimensions=["regional_relevance", "demand_signal"],
                    missing_dimensions=["market_size", "market_growth"],
                    summary="Market size and growth remain open.",
                ),
                usage={"total_tokens": 8},
            )
        return ProviderResponse(
            status="available",
            provider="nvidia",
            value=ClaimBatch(claims=[ClaimCandidate(
                source_id=self.source_id,
                text=self.excerpt,
                subject="Local delivery marketplace",
                attribute="market_signal",
                region="India",
            )]),
            usage={"total_tokens": 20},
        )


@pytest.mark.asyncio
async def test_hosted_agent_path_uses_llm_for_planning_and_claim_extraction() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    source = fixture_source("Hosted market note", "Independent retailers reported repeat delivery demand.")
    llm = FakeStructuredLLM(source.id, "Independent retailers reported repeat delivery demand.")
    runner = RunRunner(service, DeterministicPipeline(StaticFixtureSourceProvider([source]), llm))
    run = await queued_run(service)

    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert llm.calls.count("SearchPlan") == 2
    assert llm.calls.count("CoverageDecision") == 2
    assert llm.calls.count("ClaimBatch") == 1
    assert detail.verified_claim_count == 1
    assert detail.stages[0].provider == "source"
    assert detail.stages[0].query_count == 1
    assert detail.stages[0].model_call_count == 2
    assert detail.stages[0].coverage is not None
    assert detail.stages[0].coverage.missing_dimensions == ["market_size", "market_growth"]
    assert detail.stages[3].provider == "nvidia"


class ParallelSourceProvider:
    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0
        self.calls: list[str] = []

    async def collect_queries(self, _run, stage, queries, **_kwargs):
        self.calls.append(stage)
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(0.01)
            source = fixture_source(f"{stage} source", f"{stage} source content for India.")
            return ProviderResponse(
                status="available",
                provider="fake-tavily",
                value=[source],
                usage={"query_count": len(queries)},
            )
        finally:
            self.active -= 1


class ParallelAgentLLM:
    async def generate_structured(self, _system, _user, output_model, **_kwargs):
        if output_model in {MarketSearchPlan, CompetitorSearchPlan}:
            return ProviderResponse(
                status="available",
                provider="fake-nvidia",
                value=output_model(queries=["bounded research query"]),
            )
        if output_model in {MarketCoverageDecision, CompetitorCoverageDecision}:
            if output_model is CompetitorCoverageDecision:
                value = output_model(
                    action="stop",
                    covered_dimensions=["identity"],
                    missing_dimensions=["published_pricing"],
                    observations=[CompetitorObservation(competitor_name="Discovered Co", source_ids=[])],
                )
            else:
                value = output_model(
                    action="stop",
                    covered_dimensions=["regional_relevance"],
                    missing_dimensions=["market_size"],
                )
            return ProviderResponse(status="available", provider="fake-nvidia", value=value)
        if output_model is ClaimBatch:
            return ProviderResponse(status="available", provider="fake-nvidia", value=ClaimBatch())
        raise AssertionError(f"Unexpected output model: {output_model.__name__}")


class MarketOnlyProvider(ParallelSourceProvider):
    async def collect_queries(self, run, stage, queries, **kwargs):
        if stage == "competitor_research":
            raise RuntimeError("competitor provider unavailable")
        return await super().collect_queries(run, stage, queries, **kwargs)


@pytest.mark.asyncio
async def test_market_and_competitor_agents_run_concurrently_and_merge_artifacts() -> None:
    provider = ParallelSourceProvider()
    llm = ParallelAgentLLM()
    repository = MemoryRunRepository()
    service = RunService(repository)
    run = await queued_run(service)

    runner = RunRunner(service, DeterministicPipeline(provider, llm))
    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert provider.max_active == 2
    assert set(provider.calls) == {"market_statistics", "competitor_research"}
    assert len(detail.sources) == 2
    assert detail.competitor_observations[0].competitor_name == "Discovered Co"
    competitor_stage = next(stage for stage in detail.stages if stage.name == "competitor_research")
    assert competitor_stage.observations[0].competitor_name == "Discovered Co"


@pytest.mark.asyncio
async def test_competitor_failure_preserves_market_artifacts() -> None:
    provider = MarketOnlyProvider()
    llm = ParallelAgentLLM()
    repository = MemoryRunRepository()
    service = RunService(repository)
    run = await queued_run(service)

    await RunRunner(service, DeterministicPipeline(provider, llm)).run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")

    assert detail.status == "partial"
    assert detail.sources
    assert any(source.origin == "offline_fixture" for source in detail.sources)
    competitor_stage = next(stage for stage in detail.stages if stage.name == "competitor_research")
    assert competitor_stage.state == "partial"
    assert any("provider" in warning.message.lower() for warning in detail.warnings)
