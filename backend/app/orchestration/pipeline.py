from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.agents.claim_extraction import ClaimExtractionAgent
from app.agents.context import make_context
from app.agents.contracts import AgentBudget, AgentResult
from app.agents.market_research import MarketResearchAgent
from app.domain.run_snapshot import RunSnapshot
from app.orchestration.stages import StageOutput, collect_sources, verify_claims
from app.providers.offline import UnavailableSourceProvider
from app.providers.protocols import LLMProvider, SourceProvider
from app.schemas import Claim, EvidenceRecord, RunWarning, SourceSnapshot

PipelineOutcome = Literal["completed", "partial", "failed"]


@dataclass
class PipelineResult:
    outcome: PipelineOutcome
    stage_results: list[StageOutput] = field(default_factory=list)
    sources: list[SourceSnapshot] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    report_available: bool = False

    @property
    def completed(self) -> bool:
        return self.outcome == "completed"

    @property
    def warning(self) -> str | None:
        return self.warnings[0] if self.warnings else None


class DeterministicPipeline:
    """Runs bounded stages in a fixed order; it never chooses the next stage with a model."""

    def __init__(
        self,
        source_provider: SourceProvider | None = None,
        llm_provider: LLMProvider | None = None,
        market_budget: AgentBudget | None = None,
    ) -> None:
        self.source_provider = source_provider or UnavailableSourceProvider()
        self.llm_provider = llm_provider
        self.market_budget = market_budget or AgentBudget()

    async def run(self, run: RunSnapshot) -> PipelineResult:
        result = PipelineResult(outcome="partial")
        source_ids: set[str] = set()

        market_result = await MarketResearchAgent().run(
            make_context(run, self.source_provider, self.llm_provider),
            self.market_budget,
        )
        market_stage = self._agent_stage_output(market_result, "market_statistics", self._provider_name())
        result.stage_results.append(market_stage)
        for source in market_result.sources:
            if source.id not in source_ids:
                result.sources.append(source)
                source_ids.add(source.id)
        self._add_agent_warnings(result, market_result)

        for stage_name in ("competitor_research",):
            stage = await collect_sources(run, stage_name, self.source_provider)
            result.stage_results.append(stage)
            for source in stage.sources:
                if source.id not in source_ids:
                    result.sources.append(source)
                    source_ids.add(source.id)
            if stage.warning and stage.warning not in result.warnings:
                result.warnings.append(stage.warning)

        result.stage_results.append(StageOutput(
            name="customer_voice",
            state="skipped",
            warning="Optional customer voice stage is disabled in the offline slice.",
        ))

        if result.sources:
            claim_result = await ClaimExtractionAgent().run(
                make_context(run, self.source_provider, self.llm_provider, sources=result.sources),
                AgentBudget(max_model_calls=1),
            )
            claim_stage = self._agent_stage_output(claim_result, "claim_extraction", self._llm_name())
            result.stage_results.append(claim_stage)
            result.claims.extend(claim_result.claims)
            self._add_agent_warnings(result, claim_result)
        else:
            result.stage_results.append(StageOutput(name="claim_extraction", state="skipped", warning="No source inputs were available."))

        if result.claims:
            evidence_stage = verify_claims(result.claims, result.sources)
            result.stage_results.append(evidence_stage)
            result.claims = evidence_stage.claims
            result.evidence.extend(evidence_stage.evidence)
            if evidence_stage.warning and evidence_stage.warning not in result.warnings:
                result.warnings.append(evidence_stage.warning)
        else:
            result.stage_results.append(StageOutput(name="evidence_verification", state="skipped", warning="No claims were available."))

        result.stage_results.append(StageOutput(name="assessment", state="skipped", warning="Assessment rules are not implemented in this slice."))
        result.stage_results.append(StageOutput(name="report_generation", state="skipped", warning="No report artifact exists yet."))
        result.warnings.extend(
            stage.warning for stage in result.stage_results
            if stage.warning and stage.warning not in result.warnings
        )
        return result

    def _provider_name(self) -> str:
        return "tavily" if self.source_provider.__class__.__name__ == "TavilySourceProvider" else "source"

    def _llm_name(self) -> str:
        return "nvidia" if self.llm_provider is not None else "deterministic"

    @staticmethod
    def _agent_stage_output(agent: AgentResult, name: str, provider: str) -> StageOutput:
        warning = " ".join(item.message for item in agent.warnings) or None
        state = "completed" if agent.status == "completed" else "failed" if agent.status == "failed" else "partial"
        return StageOutput(
            name=name,
            state=state,
            started_at=agent.started_at,
            completed_at=agent.completed_at,
            provider=provider,
            sources=agent.sources,
            claims=agent.claims,
            warning=warning,
            error_code=agent.error_code,
            iterations=agent.iterations,
            query_count=agent.query_count,
            model_call_count=agent.model_call_count,
            usage=agent.usage,
            coverage=agent.coverage,
            budget_exhausted=agent.budget_exhausted,
        )

    @staticmethod
    def _add_agent_warnings(result: PipelineResult, agent: AgentResult) -> None:
        for warning in agent.warnings:
            if warning.message not in result.warnings:
                result.warnings.append(warning.message)


class DemoPipeline(DeterministicPipeline):
    """Default local pipeline. It performs no network or model calls."""
