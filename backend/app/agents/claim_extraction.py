from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from pydantic import BaseModel, Field, ValidationError

from app.agents.contracts import AgentBudget, AgentContext, AgentResult
from app.orchestration.stages import extract_claims
from app.schemas import Claim, ClaimType, RunWarning, VerificationStatus


class ClaimCandidate(BaseModel):
    source_id: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=2000)
    subject: str = Field(min_length=1, max_length=300)
    attribute: str = Field(min_length=1, max_length=160)
    claim_type: ClaimType = ClaimType.SOURCE_REPORTED_FACT
    region: str | None = None
    year: int | None = None
    period: str | None = None
    value: float | None = None
    unit: str | None = None
    currency: str | None = None


class ClaimBatch(BaseModel):
    claims: list[ClaimCandidate] = Field(default_factory=list, max_length=50)


class ClaimExtractionAgent:
    name = "claim_extraction"

    async def run(self, context: AgentContext, budget: AgentBudget) -> AgentResult:
        started_at = datetime.now(timezone.utc)
        if not context.sources:
            return AgentResult(
                status="partial",
                warnings=[RunWarning(stage=self.name, message="No source inputs were available.")],
                iterations=1,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        if context.llm_provider is None or budget.max_model_calls < 1:
            return self._deterministic_fallback(context, started_at, "NVIDIA is not configured; deterministic claim extraction was used.")

        prompt = (
            "Extract only source-reported claims from the supplied source snapshots. "
            "The claim text must be a verbatim excerpt from its source, not a paraphrase. "
            "Return JSON matching the schema and include source_id for every claim. "
            "Do not infer facts that are not explicitly present."
        )
        source_text = "\n\n".join(
            f"SOURCE {source.id}\nTITLE: {source.title}\nTEXT: {(source.stored_text or source.permitted_excerpt or '')[:4000]}"
            for source in context.sources
        )
        user_content = f"Market: {context.run.market_definition}\n{source_text}"
        try:
            response = await context.llm_provider.generate_structured(
                prompt,
                user_content,
                ClaimBatch,
                max_attempts=budget.max_model_calls,
            )
        except Exception:
            return self._deterministic_fallback(
                context,
                started_at,
                "NVIDIA claim extraction failed; deterministic claim extraction was used.",
            )

        if response.status != "available" or not response.value:
            return self._deterministic_fallback(
                context,
                started_at,
                response.warning or "NVIDIA claim extraction returned no usable output; deterministic extraction was used.",
                usage=response.usage or {},
            )

        claims, warnings = self._claims_from_batch(context, response.value)
        return AgentResult(
            status="completed" if claims and not warnings else "partial",
            claims=claims,
            warnings=warnings,
            usage=response.usage or {},
            error_code=response.error_code,
            iterations=1,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def _deterministic_fallback(
        self,
        context: AgentContext,
        started_at: datetime,
        warning: str,
        usage: dict[str, int | float] | None = None,
    ) -> AgentResult:
        output = extract_claims(context.run, context.sources)
        return AgentResult(
            status="completed" if output.claims else "partial",
            claims=output.claims,
            warnings=[RunWarning(stage=self.name, source="deterministic", message=warning)],
            usage=usage or {},
            iterations=1,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _claims_from_batch(context: AgentContext, batch: ClaimBatch) -> tuple[list[Claim], list[RunWarning]]:
        source_by_id = {source.id: source for source in context.sources}
        claims: list[Claim] = []
        warnings: list[RunWarning] = []
        for candidate in batch.claims:
            source = source_by_id.get(candidate.source_id)
            if source is None:
                warnings.append(RunWarning(stage="claim_extraction", message="A model claim referenced an unknown source."))
                continue
            claim_id = f"claim-{sha256((candidate.source_id + candidate.text).encode()).hexdigest()[:12]}"
            try:
                claims.append(Claim(
                    id=claim_id,
                    stable_key=f"source:{candidate.source_id}:{sha256(candidate.text.encode()).hexdigest()[:10]}",
                    text=candidate.text.strip(),
                    subject=candidate.subject.strip(),
                    attribute=candidate.attribute.strip(),
                    period=candidate.period,
                    year=candidate.year,
                    region=candidate.region or context.run.intake.region,
                    claim_type=candidate.claim_type,
                    source_ids=[candidate.source_id],
                    independence_group=source.publisher,
                    verification_status=VerificationStatus.UNCHECKED,
                    value=candidate.value,
                    unit=candidate.unit,
                    currency=candidate.currency,
                ))
            except ValidationError:
                warnings.append(RunWarning(stage="claim_extraction", message="A model claim failed schema validation."))
        return claims, ClaimExtractionAgent._unique_warnings(warnings)

    @staticmethod
    def _unique_warnings(warnings: list[RunWarning]) -> list[RunWarning]:
        unique: list[RunWarning] = []
        seen: set[str] = set()
        for warning in warnings:
            if warning.message not in seen:
                seen.add(warning.message)
                unique.append(warning)
        return unique
