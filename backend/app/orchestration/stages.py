from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256

from app.domain.run_snapshot import RunSnapshot
from app.providers.protocols import SourceProvider
from app.schemas import Claim, ClaimType, CompetitorObservation, CoverageSnapshot, EvidenceRecord, EvidenceGrade, SourceSnapshot, VerificationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StageOutput:
    name: str
    state: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    provider: str | None = None
    sources: list[SourceSnapshot] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    warning: str | None = None
    error_code: str | None = None
    iterations: int = 0
    query_count: int = 0
    model_call_count: int = 0
    usage: dict[str, int | float] = field(default_factory=dict)
    coverage: CoverageSnapshot | None = None
    budget_exhausted: bool = False
    observations: list[CompetitorObservation] = field(default_factory=list)


async def collect_sources(run: RunSnapshot, stage: str, provider: SourceProvider) -> StageOutput:
    started_at = utc_now()
    response = await provider.collect(run, stage)
    return StageOutput(
        name=stage,
        state="completed" if response.status == "available" else "partial",
        started_at=started_at,
        completed_at=utc_now(),
        provider=response.provider,
        sources=response.value or [],
        warning=response.warning,
        error_code=response.error_code,
    )


def extract_claims(run: RunSnapshot, sources: list[SourceSnapshot]) -> StageOutput:
    started_at = utc_now()
    claims: list[Claim] = []
    for source in sources:
        text = (source.stored_text or source.permitted_excerpt or "").strip()
        if not text:
            continue
        excerpt = text.split("\n", 1)[0].strip()
        claim_id = f"claim-{sha256(source.id.encode()).hexdigest()[:10]}"
        claims.append(
            Claim(
                id=claim_id,
                stable_key=f"source:{source.id}:summary",
                text=excerpt,
                subject=run.intake.product_name or "product",
                attribute="source_summary",
                region=run.intake.region,
                claim_type=ClaimType.SOURCE_REPORTED_FACT,
                source_ids=[source.id],
                independence_group=source.publisher,
            )
        )
    return StageOutput(
        name="claim_extraction",
        state="completed" if claims else "partial",
        started_at=started_at,
        completed_at=utc_now(),
        claims=claims,
    )


def verify_claims(claims: list[Claim], sources: list[SourceSnapshot]) -> StageOutput:
    started_at = utc_now()
    source_by_id = {source.id: source for source in sources}
    evidence: list[EvidenceRecord] = []
    verified_claims: list[Claim] = []
    for claim in claims:
        source = next((source_by_id.get(source_id) for source_id in claim.source_ids), None)
        matching_text = None
        if source:
            for source_text in (source.stored_text, source.permitted_excerpt):
                if source_text and claim.text in source_text:
                    matching_text = source_text
                    break
        if source and matching_text:
            evidence_id = f"evidence-{sha256((claim.id + source.id).encode()).hexdigest()[:10]}"
            start_offset = matching_text.index(claim.text)
            evidence.append(EvidenceRecord(
                id=evidence_id,
                claim_id=claim.id,
                source_id=source.id,
                excerpt=claim.text,
                start_offset=start_offset,
                end_offset=start_offset + len(claim.text),
                relation="supports",
                excerpt_match="exact",
            ))
            verified_claims.append(claim.model_copy(update={
                "evidence_ids": [evidence_id],
                "verification_status": VerificationStatus.VERIFIED,
                "evidence_grade": EvidenceGrade.C,
            }))
        else:
            verified_claims.append(claim.model_copy(update={"verification_status": VerificationStatus.UNSUPPORTED}))
    return StageOutput(
        name="evidence_verification",
        state="completed" if evidence else "partial",
        started_at=started_at,
        completed_at=utc_now(),
        claims=verified_claims,
        evidence=evidence,
        warning=None if evidence else "No claim excerpts matched stored source text.",
    )
