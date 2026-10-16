from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.schemas import (
    MarketDefinitionProposal,
    ProductIntake,
    RunEvent,
    RunStatus,
    RunWarning,
    Claim,
    EvidenceRecord,
    SourceSnapshot,
    StageSnapshot,
)


STAGE_NAMES = (
    "market_statistics",
    "competitor_research",
    "customer_voice",
    "claim_extraction",
    "evidence_verification",
    "assessment",
    "report_generation",
)


@dataclass
class RunSnapshot:
    id: str
    owner_id: str
    intake: ProductIntake
    created_at: datetime
    updated_at: datetime
    status: RunStatus
    market_definition: str
    proposed_market_definition: MarketDefinitionProposal | None = None
    confirmed_market_definition: MarketDefinitionProposal | None = None
    evidence_count: int = 0
    report_available: bool = False
    warnings: list[RunWarning] = field(default_factory=list)
    stages: list[StageSnapshot] = field(default_factory=list)
    events: list[RunEvent] = field(default_factory=list)
    sources: list[SourceSnapshot] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
