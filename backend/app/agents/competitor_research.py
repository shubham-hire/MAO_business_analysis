from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.agents.contracts import AgentBudget, AgentBudgetLedger, AgentContext, AgentResult
from app.orchestration.stages import collect_sources
from app.providers.protocols import ProviderResponse
from app.providers.tavily import build_search_queries
from app.schemas import CompetitorObservation, CoverageSnapshot, RunWarning, SourceSnapshot, VerificationStatus


COMPETITOR_DIMENSIONS = (
    "identity",
    "target_customer",
    "features",
    "positioning",
    "published_pricing",
    "billing_period",
    "currency",
    "regional_availability",
)

_UNKNOWN_VALUES = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "not available",
    "not found",
    "not published",
    "unknown",
    "unavailable",
}


class SearchPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=4)


class CoverageDecision(BaseModel):
    action: Literal["search", "stop"]
    queries: list[str] = Field(default_factory=list, max_length=4)
    covered_dimensions: list[str] = Field(default_factory=list, max_length=12)
    missing_dimensions: list[str] = Field(default_factory=list, max_length=12)
    summary: str = Field(default="", max_length=500)
    observations: list[CompetitorObservation] = Field(default_factory=list, max_length=20)


# Descriptive aliases keep the competitor-specific contract discoverable while matching
# the market agent's public SearchPlan and CoverageDecision names.
CompetitorSearchPlan = SearchPlan
CompetitorCoverageDecision = CoverageDecision


class CompetitorResearchAgent:
    name = "competitor_research"

    async def run(self, context: AgentContext, budget: AgentBudget) -> AgentResult:
        started_at = datetime.now(timezone.utc)
        ledger = AgentBudgetLedger(budget)
        warnings: list[RunWarning] = []
        usage: dict[str, int | float] = {}
        sources_by_id: dict[str, SourceSnapshot] = {}
        observations_by_name = {
            self._name_key(name): self._empty_observation(name, "user_listed")
            for name in self._listed_competitors(context)
        }
        coverage: CoverageSnapshot | None = None
        next_queries: list[str] | None = None
        budget_exhausted = False
        iterations_completed = 0
        error_code: str | None = None
        max_iterations = max(1, budget.max_iterations)

        for iteration in range(1, max_iterations + 1):
            if ledger.expired:
                return self._result(
                    started_at,
                    ledger,
                    sources_by_id,
                    observations_by_name,
                    warnings,
                    coverage,
                    usage,
                    iteration - 1,
                    "competitor_research_timeout",
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
                try:
                    planned, plan_usage, plan_warning = await self._plan_queries(
                        context, fallback_queries, iteration, ledger
                    )
                except asyncio.TimeoutError:
                    return self._result(
                        started_at,
                        ledger,
                        sources_by_id,
                        observations_by_name,
                        warnings,
                        coverage,
                        usage,
                        iteration,
                        "competitor_research_timeout",
                        True,
                    )
                self._merge_usage(usage, plan_usage)
                queries = planned or fallback_queries
                if plan_warning:
                    warnings.append(plan_warning)

            queries = self._clean_queries(queries, ledger.remaining_queries)
            if not queries or ledger.remaining_sources <= 0:
                budget_exhausted = True
                break

            try:
                response = await self._collect(context, queries, ledger)
            except asyncio.TimeoutError:
                return self._result(
                    started_at,
                    ledger,
                    sources_by_id,
                    observations_by_name,
                    warnings,
                    coverage,
                    usage,
                    iteration,
                    "competitor_research_timeout",
                    True,
                )
            except Exception:
                warnings.append(RunWarning(
                    stage=self.name,
                    source="source",
                    message="Competitor source provider failed; successful artifacts were preserved.",
                ))
                error_code = error_code or "competitor_research_provider_failure"
                break

            actual_query_count = len(queries)
            if response.usage and isinstance(response.usage.get("query_count"), (int, float)):
                actual_query_count = max(0, int(response.usage["query_count"]))
            ledger.record_queries(min(actual_query_count, ledger.remaining_queries))
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

            if not sources_by_id:
                coverage = self._deterministic_coverage([], context)
                break

            if context.llm_provider is None:
                coverage = self._deterministic_coverage(list(sources_by_id.values()), context)
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
                return self._result(
                    started_at,
                    ledger,
                    sources_by_id,
                    observations_by_name,
                    warnings,
                    coverage,
                    usage,
                    iteration,
                    "competitor_research_timeout",
                    True,
                )
            self._merge_usage(usage, decision_usage)
            if decision_warning:
                warnings.append(decision_warning)
            if decision is None:
                coverage = self._deterministic_coverage(list(sources_by_id.values()), context)
                break

            coverage = CoverageSnapshot(
                summary=decision.summary,
                covered_dimensions=decision.covered_dimensions,
                missing_dimensions=decision.missing_dimensions,
            )
            observation_warnings = self._merge_observations(
                observations_by_name,
                decision.observations,
                sources_by_id,
                context,
            )
            warnings.extend(observation_warnings)
            if decision.action != "search" or iteration >= max_iterations:
                break

            next_queries = self._clean_queries(decision.queries, ledger.remaining_queries)
            if not next_queries or ledger.remaining_queries <= 0:
                budget_exhausted = True
                break

        if not sources_by_id and not warnings:
            warnings.append(RunWarning(stage=self.name, message="Competitor research returned no usable sources."))
        if coverage is None:
            coverage = self._deterministic_coverage(list(sources_by_id.values()), context)
        return self._result(
            started_at,
            ledger,
            sources_by_id,
            observations_by_name,
            warnings,
            coverage,
            usage,
            iterations_completed,
            error_code,
            budget_exhausted,
        )

    async def _plan_queries(
        self,
        context: AgentContext,
        fallback_queries: list[str],
        iteration: int,
        ledger: AgentBudgetLedger,
    ) -> tuple[list[str], dict[str, int | float], RunWarning | None]:
        prompt = (
            "Create a small, diverse search plan for competitor research. "
            "Cover named competitors and possible alternatives, with identity, target customer, features, "
            "positioning, published pricing, billing period, currency and regional availability. "
            "Queries must be concise, factual and under 400 characters. Do not include URLs, citations or answers."
        )
        user_content = (
            f"Market definition: {self._market_definition(context)}\n"
            f"Target customer: {context.run.intake.target_customer}\n"
            f"Region: {context.run.intake.region}\n"
            f"User-listed competitors: {self._listed_competitors(context)}\n"
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
                message="NVIDIA competitor query planning failed; deterministic queries were used.",
            )
        if response.status != "available" or not response.value:
            return fallback_queries, response.usage or {}, RunWarning(
                stage=self.name,
                source=response.provider,
                message=response.warning or "NVIDIA competitor query planning returned no usable plan.",
            )
        plan = self._coerce_search_plan(response.value)
        if plan is None:
            return fallback_queries, response.usage or {}, RunWarning(
                stage=self.name,
                source=response.provider,
                message="NVIDIA competitor query planning returned invalid output; deterministic queries were used.",
            )
        queries = self._clean_queries(plan.queries, 4)
        return queries or fallback_queries, response.usage or {}, None

    async def _decide_coverage(
        self,
        context: AgentContext,
        sources: list[SourceSnapshot],
        previous_queries: list[str],
        iteration: int,
        ledger: AgentBudgetLedger,
    ) -> tuple[CoverageDecision | None, dict[str, int | float], RunWarning | None]:
        prompt = (
            "Review the retained competitor source snapshots against every required dimension. "
            "Return observations only for facts supported by the supplied source text or permitted excerpts. "
            "Use exact source_ids. Mark an unreported price as unknown or not_found; never estimate or infer a price. "
            "Set source_type to discovered for alternatives not in the user-listed competitor set. "
            "Choose search only when a bounded follow-up query can fill a meaningful gap; otherwise choose stop."
        )
        source_text = "\n\n".join(
            f"SOURCE {source.id}\nTITLE: {source.title}\nTEXT: "
            f"{(source.stored_text or source.permitted_excerpt or '')[:3500]}"
            for source in sources
        )
        user_content = (
            f"Required dimensions: {list(COMPETITOR_DIMENSIONS)}\n"
            f"Market definition: {self._market_definition(context)}\n"
            f"Region: {context.run.intake.region}\n"
            f"User-listed competitors: {self._listed_competitors(context)}\n"
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
                message="NVIDIA competitor coverage review failed; collected artifacts were preserved.",
            )
        decision = self._coerce_coverage_decision(response.value)
        if response.status != "available" or decision is None:
            return decision, response.usage or {}, RunWarning(
                stage=self.name,
                source=response.provider,
                message=response.warning or "NVIDIA competitor coverage review returned no usable decision.",
            )
        return decision, response.usage or {}, None

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
        if ledger.expired:
            raise asyncio.TimeoutError
        try:
            response = await self._with_deadline(
                context.llm_provider.generate_structured(
                    system_prompt,
                    user_content,
                    output_model,
                    max_attempts=ledger.remaining_model_calls,
                ),
                ledger,
            )
        except Exception:
            ledger.record_model_calls(min(1, ledger.remaining_model_calls))
            raise
        ledger.record_model_calls(min(max(1, response.attempts), ledger.remaining_model_calls))
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

    def _merge_observations(
        self,
        target: dict[str, CompetitorObservation],
        raw_observations: list[Any],
        sources_by_id: dict[str, SourceSnapshot],
        context: AgentContext,
    ) -> list[RunWarning]:
        warnings: list[RunWarning] = []
        listed_names = {self._name_key(name) for name in self._listed_competitors(context)}
        for raw in raw_observations:
            observation = self._coerce_observation(raw)
            if observation is None:
                warnings.append(RunWarning(
                    stage=self.name,
                    source="nvidia",
                    message="A model competitor observation failed schema validation and was discarded.",
                ))
                continue
            key = self._name_key(observation.competitor_name)
            if not key:
                continue
            source_ids = [source_id for source_id in observation.source_ids if source_id in sources_by_id]
            observation = observation.model_copy(update={
                "competitor_name": " ".join(observation.competitor_name.split())[:240],
                "source_type": "user_listed" if key in listed_names else "discovered",
                "source_ids": source_ids,
                "verification_status": VerificationStatus.UNCHECKED,
            })
            observation, pricing_warning = self._normalize_pricing(observation, sources_by_id)
            if pricing_warning:
                warnings.append(RunWarning(stage=self.name, source="nvidia", message=pricing_warning))
            current = target.get(key)
            target[key] = self._merge_observation(current, observation) if current else observation
        return self._unique_warnings(warnings)

    def _normalize_pricing(
        self,
        observation: CompetitorObservation,
        sources_by_id: dict[str, SourceSnapshot],
    ) -> tuple[CompetitorObservation, str | None]:
        pricing = self._clean_value(observation.published_pricing, "unknown")
        if self._is_unknown(pricing):
            return observation.model_copy(update={
                "published_pricing": "not_found" if pricing == "not found" else pricing,
                "pricing_status": "not_found",
                "billing_period": self._missing_value(observation.billing_period),
                "currency": self._missing_value(observation.currency),
            }), None
        source_text = [
            source.stored_text or source.permitted_excerpt or ""
            for source_id, source in sources_by_id.items()
            if source_id in observation.source_ids
        ]
        if not source_text or not self._price_is_supported(pricing, source_text):
            return observation.model_copy(update={
                "published_pricing": "unknown",
                "pricing_status": "unknown",
                "billing_period": "unknown",
                "currency": "unknown",
            }), f"Unsupported pricing for {observation.competitor_name} was discarded; price remains unknown."
        return observation.model_copy(update={"published_pricing": pricing, "pricing_status": "published"}), None

    @staticmethod
    def _price_is_supported(pricing: str, source_text: list[str]) -> bool:
        candidate = " ".join(pricing.lower().split())
        for text in source_text:
            normalized = " ".join(text.lower().split())
            if candidate and candidate in normalized:
                return True
            numbers = re.findall(r"\d+(?:[,.]\d+)*", candidate)
            if numbers and all(number.replace(",", "") in normalized.replace(",", "") for number in numbers):
                return True
        return False

    @staticmethod
    def _merge_observation(
        current: CompetitorObservation,
        incoming: CompetitorObservation,
    ) -> CompetitorObservation:
        def choose_text(old: str, new: str) -> str:
            return new if not CompetitorResearchAgent._is_unknown(new) else old

        features = list(dict.fromkeys([*current.features, *incoming.features]))
        source_ids = list(dict.fromkeys([*current.source_ids, *incoming.source_ids]))
        if incoming.pricing_status == "published" or current.pricing_status != "published":
            pricing = incoming
        else:
            pricing = current
        return current.model_copy(update={
            "source_type": "user_listed" if current.source_type == "user_listed" else incoming.source_type,
            "identity": choose_text(current.identity, incoming.identity),
            "target_customer": choose_text(current.target_customer, incoming.target_customer),
            "features": features[:20],
            "positioning": choose_text(current.positioning, incoming.positioning),
            "published_pricing": pricing.published_pricing,
            "pricing_status": pricing.pricing_status,
            "billing_period": choose_text(current.billing_period, incoming.billing_period),
            "currency": choose_text(current.currency, incoming.currency),
            "regional_availability": choose_text(current.regional_availability, incoming.regional_availability),
            "source_ids": source_ids[:20],
            "verification_status": VerificationStatus.UNCHECKED,
        })

    def _result(
        self,
        started_at: datetime,
        ledger: AgentBudgetLedger,
        sources_by_id: dict[str, SourceSnapshot],
        observations_by_name: dict[str, CompetitorObservation],
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
                message="Competitor research budget exhausted; retained artifacts may be incomplete.",
            ))
        unique_warnings = self._unique_warnings(warnings)
        if coverage is None:
            coverage = self._deterministic_coverage(list(sources_by_id.values()), None)
        if coverage.missing_dimensions and sources_by_id and error_code is None:
            error_code = "competitor_research_incomplete"
        if not sources_by_id and error_code is None:
            error_code = "competitor_research_empty"
        status = "completed" if sources_by_id and not unique_warnings and not coverage.missing_dimensions else "partial"
        return AgentResult(
            status=status,
            sources=list(sources_by_id.values()),
            observations=list(observations_by_name.values()),
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
    def _deterministic_coverage(
        sources: list[SourceSnapshot],
        context: AgentContext | None,
    ) -> CoverageSnapshot:
        text = " ".join(
            f"{source.title} {source.stored_text or source.permitted_excerpt or ''}" for source in sources
        ).lower()
        region = context.run.intake.region.lower() if context is not None else ""
        keywords = {
            "identity": ("company", "platform", "marketplace", "founded", "profile"),
            "target_customer": ("customer", "retailer", "merchant", "business", "enterprise", "consumer"),
            "features": ("feature", "inventory", "delivery", "payment", "analytics", "integration", "api"),
            "positioning": ("position", "leading", "specializ", "for ", "platform", "marketplace"),
            "published_pricing": ("pricing", "price", "cost", "free", "inr", "usd", "$", "₹"),
            "billing_period": ("monthly", "month", "annual", "annually", "yearly", "year", "one-time"),
            "currency": ("inr", "usd", "eur", "gbp", "$", "₹", "€", "£"),
            "regional_availability": (region, "india", "regional", "available in", "country"),
        }
        covered = [
            dimension for dimension in COMPETITOR_DIMENSIONS
            if any(term and term in text for term in keywords[dimension])
        ]
        return CoverageSnapshot(
            summary="Coverage estimated from retained competitor source text.",
            covered_dimensions=covered,
            missing_dimensions=[dimension for dimension in COMPETITOR_DIMENSIONS if dimension not in covered],
        )

    @staticmethod
    def _empty_observation(name: str, source_type: Literal["user_listed", "discovered"]) -> CompetitorObservation:
        return CompetitorObservation(
            competitor_name=name,
            source_type=source_type,
            verification_status=VerificationStatus.UNCHECKED,
        )

    @staticmethod
    def _listed_competitors(context: AgentContext) -> list[str]:
        definition = context.run.confirmed_market_definition or context.run.proposed_market_definition
        names = [*(definition.competitors if definition else []), *context.run.intake.competitors]
        result: list[str] = []
        seen: set[str] = set()
        for name in names:
            clean = " ".join(name.split())[:240].strip()
            key = CompetitorResearchAgent._name_key(clean)
            if clean and key not in seen:
                result.append(clean)
                seen.add(key)
        return result

    @staticmethod
    def _market_definition(context: AgentContext) -> str:
        definition = context.run.confirmed_market_definition or context.run.proposed_market_definition
        if definition is None:
            return context.run.market_definition
        return (
            f"category={definition.category}; included={definition.included_boundaries}; "
            f"excluded={definition.excluded_boundaries}"
        )

    @staticmethod
    def _name_key(name: str) -> str:
        return " ".join(name.casefold().split())

    @staticmethod
    def _clean_queries(queries: list[str], limit: int) -> list[str]:
        if limit <= 0:
            return []
        clean: list[str] = []
        seen: set[str] = set()
        for query in queries:
            normalized = " ".join(str(query).split())[:399].strip()
            key = normalized.casefold()
            if normalized and key not in seen:
                clean.append(normalized)
                seen.add(key)
        return clean[:limit]

    @staticmethod
    def _clean_value(value: Any, default: str) -> str:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return str(value)
        clean = " ".join(str(value).split())[:1000].strip()
        return clean or default

    @staticmethod
    def _missing_value(value: str) -> str:
        return "not_found" if CompetitorResearchAgent._is_unknown(value) else value

    @staticmethod
    def _is_unknown(value: str) -> bool:
        return " ".join(value.casefold().replace("_", " ").split()) in _UNKNOWN_VALUES

    @staticmethod
    def _coerce_search_plan(value: Any) -> SearchPlan | None:
        data = CompetitorResearchAgent._object_data(value, ("queries",))
        try:
            return SearchPlan.model_validate(data)
        except ValidationError:
            return None

    @staticmethod
    def _coerce_coverage_decision(value: Any) -> CoverageDecision | None:
        if value is None:
            return None
        if isinstance(value, CoverageDecision):
            return value
        data = CompetitorResearchAgent._object_data(
            value,
            ("action", "queries", "covered_dimensions", "missing_dimensions", "summary", "observations"),
        )
        try:
            observations = [CompetitorResearchAgent._coerce_observation(item) for item in data.get("observations", [])]
            data["observations"] = [item for item in observations if item is not None]
            return CoverageDecision.model_validate(data)
        except (ValidationError, TypeError):
            return None

    @staticmethod
    def _coerce_observation(value: Any) -> CompetitorObservation | None:
        if isinstance(value, CompetitorObservation):
            return value
        raw = CompetitorResearchAgent._object_data(
            value,
            (
                "competitor_name",
                "competitor",
                "name",
                "source_type",
                "origin",
                "source",
                "identity",
                "target_customer",
                "features",
                "positioning",
                "published_pricing",
                "pricing",
                "price",
                "pricing_status",
                "billing_period",
                "currency",
                "regional_availability",
                "source_ids",
                "source_id",
            ),
        )
        data: dict[str, Any] = {}
        aliases = {
            "competitor_name": ("competitor_name", "competitor", "name"),
            "source_type": ("source_type", "origin", "source"),
            "identity": ("identity",),
            "target_customer": ("target_customer",),
            "features": ("features",),
            "positioning": ("positioning",),
            "published_pricing": ("published_pricing", "pricing", "price"),
            "pricing_status": ("pricing_status",),
            "billing_period": ("billing_period",),
            "currency": ("currency",),
            "regional_availability": ("regional_availability",),
            "source_ids": ("source_ids", "source_id"),
        }
        for field_name, field_aliases in aliases.items():
            for alias in field_aliases:
                if alias in raw and raw[alias] is not None:
                    data[field_name] = raw[alias]
                    break
        if isinstance(data.get("features"), str):
            data["features"] = [data["features"]]
        if isinstance(data.get("source_ids"), str):
            data["source_ids"] = [data["source_ids"]]
        if isinstance(data.get("published_pricing"), (int, float)):
            data["published_pricing"] = str(data["published_pricing"])
        source_type = data.get("source_type")
        if isinstance(source_type, str):
            normalized_source_type = " ".join(source_type.casefold().replace("-", " ").split())
            if normalized_source_type in {"user", "listed", "user listed"}:
                data["source_type"] = "user_listed"
            elif normalized_source_type in {"alternative", "discovered alternative"}:
                data["source_type"] = "discovered"
        pricing = data.get("published_pricing")
        if isinstance(pricing, Mapping):
            nested = pricing
            data["published_pricing"] = nested.get("value") or nested.get("display") or nested.get("amount")
            data.setdefault("pricing_status", nested.get("status"))
            data.setdefault("billing_period", nested.get("billing_period"))
            data.setdefault("currency", nested.get("currency"))
        if "competitor_name" not in data:
            return None
        data.pop("source_type", None) if data.get("source_type") is None else None
        try:
            return CompetitorObservation.model_validate(data)
        except (ValidationError, TypeError):
            return None

    @staticmethod
    def _object_data(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, Mapping):
            return dict(value)
        return {field: getattr(value, field) for field in fields if hasattr(value, field)}

    @staticmethod
    def _merge_usage(target: dict[str, int | float], values: Mapping[str, Any]) -> None:
        for key, value in values.items():
            if isinstance(value, (int, float)):
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
