from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.domain.run_snapshot import RunSnapshot
from app.orchestration.stages import StageOutput, collect_sources, extract_claims, verify_claims
from app.providers.offline import UnavailableSourceProvider
from app.providers.protocols import SourceProvider
from app.schemas import Claim, EvidenceRecord, SourceSnapshot

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

    def __init__(self, source_provider: SourceProvider | None = None) -> None:
        self.source_provider = source_provider or UnavailableSourceProvider()

    async def run(self, run: RunSnapshot) -> PipelineResult:
        result = PipelineResult(outcome="partial")
        source_ids: set[str] = set()

        for stage_name in ("market_statistics", "competitor_research"):
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
            claim_stage = extract_claims(run, result.sources)
            result.stage_results.append(claim_stage)
            result.claims.extend(claim_stage.claims)
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


class DemoPipeline(DeterministicPipeline):
    """Default local pipeline. It performs no network or model calls."""
