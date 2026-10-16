from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from time import monotonic
from typing import Literal, Protocol

from app.domain.run_snapshot import RunSnapshot
from app.providers.protocols import LLMProvider, SourceProvider
from app.schemas import Claim, CompetitorObservation, CoverageSnapshot, RunWarning, SourceSnapshot


AgentStatus = Literal["completed", "partial", "failed"]


@dataclass(frozen=True)
class AgentBudget:
    max_iterations: int = 2
    max_queries: int = 4
    max_model_calls: int = 4
    max_sources: int = 10
    timeout_seconds: float = 60.0


@dataclass
class AgentBudgetLedger:
    budget: AgentBudget
    started_monotonic: float = field(default_factory=monotonic)
    query_count: int = 0
    model_call_count: int = 0
    source_count: int = 0

    @property
    def remaining_queries(self) -> int:
        return max(0, self.budget.max_queries - self.query_count)

    @property
    def remaining_model_calls(self) -> int:
        return max(0, self.budget.max_model_calls - self.model_call_count)

    @property
    def remaining_sources(self) -> int:
        return max(0, self.budget.max_sources - self.source_count)

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self.budget.timeout_seconds - (monotonic() - self.started_monotonic))

    @property
    def deadline(self) -> float:
        return self.started_monotonic + self.budget.timeout_seconds

    @property
    def expired(self) -> bool:
        return self.remaining_seconds <= 0

    def record_queries(self, count: int) -> None:
        self.query_count += max(0, count)

    def record_model_calls(self, count: int) -> None:
        self.model_call_count += max(0, count)

    def record_sources(self, count: int) -> None:
        self.source_count += max(0, count)


@dataclass
class AgentContext:
    run: RunSnapshot
    source_provider: SourceProvider
    llm_provider: LLMProvider | None = None
    sources: list[SourceSnapshot] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)


@dataclass
class AgentResult:
    status: AgentStatus
    sources: list[SourceSnapshot] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    observations: list[CompetitorObservation] = field(default_factory=list)
    warnings: list[RunWarning] = field(default_factory=list)
    usage: dict[str, int | float] = field(default_factory=dict)
    error_code: str | None = None
    iterations: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    query_count: int = 0
    model_call_count: int = 0
    source_count: int = 0
    coverage: CoverageSnapshot | None = None
    budget_exhausted: bool = False

    @property
    def competitor_observations(self) -> list[CompetitorObservation]:
        return self.observations


class AgentTask(Protocol):
    name: str

    async def run(self, context: AgentContext, budget: AgentBudget) -> AgentResult:
        ...
