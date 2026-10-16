from __future__ import annotations

from app.agents.contracts import AgentContext
from app.domain.run_snapshot import RunSnapshot
from app.providers.protocols import LLMProvider, SourceProvider
from app.schemas import Claim, SourceSnapshot


def make_context(
    run: RunSnapshot,
    source_provider: SourceProvider,
    llm_provider: LLMProvider | None = None,
    sources: list[SourceSnapshot] | None = None,
    claims: list[Claim] | None = None,
) -> AgentContext:
    return AgentContext(
        run=run,
        source_provider=source_provider,
        llm_provider=llm_provider,
        sources=sources or [],
        claims=claims or [],
    )
