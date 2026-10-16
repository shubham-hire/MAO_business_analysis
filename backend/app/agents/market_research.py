from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agents.contracts import AgentBudget, AgentBudgetLedger, AgentContext, AgentResult
from app.orchestration.stages import collect_sources
from app.providers.protocols import ProviderResponse
from app.providers.tavily import build_search_queries
from app.schemas import CoverageSnapshot, RunWarning, SourceSnapshot


MARKET_DIMENSIONS = ("market_size", "market_growth", "regional_relevance", "demand_signal")


class SearchPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=4)


class CoverageDecision(BaseModel):
    action: Literal["search", "stop"]
    queries: list[str] = Field(default_factory=list, max_length=4)
    covered_dimensions: list[str] = Field(default_factory=list, max_length=8)
    missing_dimensions: list[str] = Field(default_factory=list, max_length=8)
    summary: str = Field(default="", max_length=500)


class MarketResearchAgent:
    name = "market_statistics"

    async def run(self, context: AgentContext, budget: AgentBudget) -> AgentResult:
        started_at = datetime.now(timezone.utc)
        ledger = AgentBudgetLedger(budget)
        warnings: list[RunWarning] = []
        usage: dict[str, int | float] = {}
        max_iterations = max(1, budget.max_iterations)
        sources_by_id: dict[str, SourceSnapshot] = {}
        coverage: CoverageSnapshot | None = None
        next_queries: list[str] | None = None
        budget_exhausted = False
        iterations_completed = 0

        for iteration in range(1, max_iterations + 1):
            if ledger.expired:
                budget_exhausted = True
                return self._result(
                    started_at,
                    ledger,
                    sources_by_id,
                    warnings,
                    coverage,
                    usage,
                    iteration - 1,
                    "market_research_timeout",
                    True,
                )
            iterations_completed = iteration

            fallback_queries = build_search_queries(
                context.run,
                self.name,
                limit=min(budget.max_queries, ledger.remaining_queries),
            )
            queries = next_queries or fallback_queries
            if iteration == 1 and context.llm_provider is not None and ledger.remaining_model_calls:
                planned, plan_usage, plan_warning = await self._plan_queries(
                    context, fallback_queries, iteration, ledger
                )
                self._merge_usage(usage, plan_usage)
                queries = planned or fallback_queries
                if plan_warning:
                    warnings.append(plan_warning)

            queries = queries[: ledger.remaining_queries]
            if not queries or ledger.remaining_sources <= 0:
                budget_exhausted = True
                break

            try:
                response = await self._collect(context, queries, ledger)
            except asyncio.TimeoutError:
                budget_exhausted = True
                return self._result(
                    started_at,
                    ledger,
                    sources_by_id,
                    warnings,
                    coverage,
                    usage,
                    iteration,
                    "market_research_timeout",
                    True,
                )

            actual_query_count = len(queries)
            if response.usage and isinstance(response.usage.get("query_count"), (int, float)):
                actual_query_count = max(0, int(response.usage["query_count"]))
            ledger.record_queries(actual_query_count)
            if response.usage:
                self._merge_usage(usage, response.usage)
            if response.warning:
                warnings.append(RunWarning(stage=self.name, source=response.provider, message=response.warning))

            for source in response.value or []:
                if source.id in sources_by_id:
                    continue
                if ledger.remaining_sources <= 0:
                    budget_exhausted = True
                    break
                sources_by_id[source.id] = source
                ledger.record_sources(1)

            if context.llm_provider is None or not sources_by_id:
                break

            if ledger.remaining_model_calls <= 0:
                budget_exhausted = True
                break

            try:
                decision, decision_usage, decision_warning = await self._decide_coverage(
                    context,
                    list(sources_by_id.values()),
                    queries,
                    iteration,
                    ledger,
                )
            except asyncio.TimeoutError:
                budget_exhausted = True
                return self._result(
                    started_at,
                    ledger,
                    sources_by_id,
                    warnings,
                    coverage,
                    usage,
                    iteration,
                    "market_research_timeout",
                    True,
                )
            self._merge_usage(usage, decision_usage)
            if decision_warning:
                warnings.append(decision_warning)
            if decision is None:
                break

            coverage = CoverageSnapshot(
                summary=decision.summary,
                covered_dimensions=decision.covered_dimensions,
                missing_dimensions=decision.missing_dimensions,
            )
            if decision.action != "search" or iteration >= max_iterations:
                break
            next_queries = [" ".join(query.split())[:399].strip() for query in decision.queries if query.strip()]
            if not next_queries or ledger.remaining_queries <= 0:
                budget_exhausted = True
                break

        if not sources_by_id and not warnings:
            warnings.append(RunWarning(stage=self.name, message="Market research returned no usable sources."))
        if coverage is None:
            coverage = self._deterministic_coverage(list(sources_by_id.values()))
        return self._result(
            started_at,
            ledger,
            sources_by_id,
            warnings,
            coverage,
            usage,
            iterations_completed,
            "market_research_empty" if not sources_by_id else None,
            budget_exhausted,
        )

    async def _plan_queries(
        self,
        context: AgentContext,
        fallback_queries: list[str],
        iteration: int,
        ledger: AgentBudgetLedger,
    ) -> tuple[list[str], dict[str, int | float], RunWarning | None]:
        assert context.llm_provider is not None
        prompt = (
            "Create a small, diverse search plan for market statistics. "
            "Queries must be concise, factual and under 400 characters. "
            "Do not include URLs, citations or answers."
        )
        user_content = (
            f"Market definition: {context.run.market_definition}\n"
            f"Region: {context.run.intake.region}\n"
            f"Target customer: {context.run.intake.target_customer}\n"
            f"Fallback queries: {fallback_queries}\n"
            f"This is bounded search iteration {iteration}."
        )
        try:
            response = await self._call_llm(context, prompt, user_content, SearchPlan, ledger)
        except asyncio.TimeoutError:
            raise
        except Exception:
            return fallback_queries, {}, RunWarning(
                stage=self.name,
                source="nvidia",
                message="NVIDIA query planning failed; deterministic queries were used.",
            )
        if response.status != "available" or not response.value:
            return fallback_queries, response.usage or {}, RunWarning(
                stage=self.name,
                source=response.provider,
                message=response.warning or "NVIDIA query planning returned no usable plan.",
            )
        plan = response.value
        queries = [" ".join(query.split())[:399].strip() for query in plan.queries if query.strip()]
        return queries or fallback_queries, response.usage or {}, None

    async def _decide_coverage(
        self,
        context: AgentContext,
        sources: list[SourceSnapshot],
        previous_queries: list[str],
        iteration: int,
        ledger: AgentBudgetLedger,
    ) -> tuple[CoverageDecision | None, dict[str, int | float], RunWarning | None]:
        assert context.llm_provider is not None
        prompt = (
            "Review the collected market sources against the required dimensions. "
            "Choose search only when a bounded follow-up query can fill a meaningful gap; "
            "otherwise choose stop. Never invent facts or URLs."
        )
        source_text = "\n\n".join(
            f"SOURCE {source.id}\nTITLE: {source.title}\nTEXT: {(source.stored_text or source.permitted_excerpt or '')[:1800]}"
            for source in sources
        )
        user_content = (
            f"Required dimensions: {list(MARKET_DIMENSIONS)}\n"
            f"Previous queries: {previous_queries}\n"
            f"Iteration: {iteration}\n{source_text}"
        )
        try:
            response = await self._call_llm(context, prompt, user_content, CoverageDecision, ledger)
        except asyncio.TimeoutError:
            raise
        except Exception:
            return None, {}, RunWarning(
                stage=self.name,
                source="nvidia",
                message="NVIDIA coverage review failed; collected sources were preserved.",
            )
        if response.status != "available" or not response.value:
            return None, response.usage or {}, RunWarning(
                stage=self.name,
                source=response.provider,
                message=response.warning or "NVIDIA coverage review returned no usable decision.",
            )
        return response.value, response.usage or {}, None

    async def _call_llm(
        self,
        context: AgentContext,
        system_prompt: str,
        user_content: str,
        output_model: type[BaseModel],
        ledger: AgentBudgetLedger,
    ) -> ProviderResponse[Any]:
        if context.llm_provider is None or ledger.remaining_model_calls <= 0:
            raise RuntimeError("model call budget exhausted")
        response = await self._with_deadline(
            context.llm_provider.generate_structured(
                system_prompt,
                user_content,
                output_model,
                max_attempts=ledger.remaining_model_calls,
            ),
            ledger,
        )
        ledger.record_model_calls(response.attempts)
        return response

    async def _collect(
        self,
        context: AgentContext,
        queries: list[str],
        ledger: AgentBudgetLedger,
    ) -> ProviderResponse[list[SourceSnapshot]]:
        provider: Any = context.source_provider
        collect_queries = getattr(provider, "collect_queries", None)
        if collect_queries is not None:
            return await self._with_deadline(
                collect_queries(
                    context.run,
                    self.name,
                    queries,
                    max_queries=ledger.remaining_queries,
                    max_sources=ledger.remaining_sources,
                    deadline=ledger.deadline,
                ),
                ledger,
            )
        stage = await self._with_deadline(collect_sources(context.run, self.name, provider), ledger)
        return ProviderResponse(
            status="available" if stage.state == "completed" else "partial",
            provider=stage.provider or "source",
            value=stage.sources,
            warning=stage.warning,
            error_code=stage.error_code,
        )

    @staticmethod
    async def _with_deadline(awaitable: Any, ledger: AgentBudgetLedger) -> Any:
        remaining = ledger.remaining_seconds
        if remaining <= 0:
            raise asyncio.TimeoutError
        return await asyncio.wait_for(awaitable, timeout=remaining)

    @staticmethod
    def _deterministic_coverage(sources: list[SourceSnapshot]) -> CoverageSnapshot:
        text = " ".join(
            f"{source.title} {source.stored_text or source.permitted_excerpt or ''}" for source in sources
        ).lower()
        keywords = {
            "market_size": ("size", "billion", "million", "market value"),
            "market_growth": ("growth", "cagr", "forecast", "increase"),
            "regional_relevance": ("india", "regional", "local", "country"),
            "demand_signal": ("demand", "adoption", "customer", "retailer"),
        }
        covered = [dimension for dimension in MARKET_DIMENSIONS if any(term in text for term in keywords[dimension])]
        return CoverageSnapshot(
            summary="Coverage estimated from retained source text.",
            covered_dimensions=covered,
            missing_dimensions=[dimension for dimension in MARKET_DIMENSIONS if dimension not in covered],
        )

    def _result(
        self,
        started_at: datetime,
        ledger: AgentBudgetLedger,
        sources_by_id: dict[str, SourceSnapshot],
        warnings: list[RunWarning],
        coverage: CoverageSnapshot | None,
        usage: dict[str, int | float],
        iterations: int,
        error_code: str | None,
        budget_exhausted: bool,
    ) -> AgentResult:
        if budget_exhausted:
            warnings.append(RunWarning(
                stage=self.name,
                message="Market research budget exhausted; retained artifacts may be incomplete.",
            ))
        unique_warnings = self._unique_warnings(warnings)
        if coverage is None:
            coverage = self._deterministic_coverage(list(sources_by_id.values()))
        if coverage.missing_dimensions and sources_by_id and error_code is None:
            error_code = "market_research_incomplete"
        status = "completed" if sources_by_id and not unique_warnings and not coverage.missing_dimensions else "partial"
        if not sources_by_id and error_code is None:
            error_code = "market_research_empty"
        return AgentResult(
            status=status,
            sources=list(sources_by_id.values()),
            warnings=unique_warnings,
            usage=usage,
            error_code=error_code,
            iterations=max(0, iterations),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            query_count=ledger.query_count,
            model_call_count=ledger.model_call_count,
            source_count=len(sources_by_id),
            coverage=coverage,
            budget_exhausted=budget_exhausted,
        )

    @staticmethod
    def _merge_usage(target: dict[str, int | float], values: dict[str, int | float]) -> None:
        for key, value in values.items():
            target[key] = target.get(key, 0) + value

    @staticmethod
    def _unique_warnings(warnings: list[RunWarning]) -> list[RunWarning]:
        unique: list[RunWarning] = []
        seen: set[tuple[str | None, str | None, str]] = set()
        for warning in warnings:
            key = (warning.stage, warning.source, warning.message)
            if key not in seen:
                seen.add(key)
                unique.append(warning)
        return unique
