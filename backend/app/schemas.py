from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class RunStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_MARKET_CONFIRMATION = "awaiting_market_confirmation"
    QUEUED = "queued"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class ClaimType(StrEnum):
    SOURCE_REPORTED_FACT = "source_reported_fact"
    CALCULATION = "calculation"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNSUPPORTED = "unsupported"
    UNCHECKED = "unchecked"


class EvidenceGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class PriceRange(ApiModel):
    minimum: float = Field(ge=0)
    maximum: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def validate_order(self) -> "PriceRange":
        if self.minimum > self.maximum:
            raise ValueError("minimum price cannot exceed maximum price")
        return self


class ProductIntake(ApiModel):
    product_name: str | None = Field(default=None, max_length=160)
    product_description: str = Field(min_length=10, max_length=5000)
    target_customer: str = Field(min_length=2, max_length=500)
    region: str = Field(min_length=2, max_length=160)
    price_range: PriceRange
    competitors: list[str] = Field(default_factory=list, max_length=20)
    additional_context: str | None = Field(default=None, max_length=3000)

    @field_validator("product_description", "target_customer", "region", mode="before")
    @classmethod
    def trim_required_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("competitors", mode="before")
    @classmethod
    def normalize_competitors(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("competitors must be a list")
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]


class MarketDefinitionProposal(ApiModel):
    category: str = Field(min_length=2, max_length=300)
    included_boundaries: str = Field(min_length=2, max_length=2000)
    excluded_boundaries: str = Field(default="", max_length=2000)
    competitors: list[str] = Field(default_factory=list, max_length=20)
    competitor_reasons: dict[str, str] = Field(default_factory=dict)

    @field_validator("category", "included_boundaries", "excluded_boundaries", mode="before")
    @classmethod
    def trim_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("competitors", mode="before")
    @classmethod
    def normalize_names(cls, value: Any) -> Any:
        if value is None:
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]


class RunWarning(ApiModel):
    stage: str | None = None
    source: str | None = None
    message: str


class SourceSnapshot(ApiModel):
    id: str
    title: str
    url: str
    publisher: str
    publication_date: datetime | None = None
    retrieval_date: datetime
    content_hash: str
    stored_text: str | None = None
    permitted_excerpt: str | None = None
    origin: str = "provider"
    provider: str


class EvidenceRecord(ApiModel):
    id: str
    claim_id: str
    source_id: str
    excerpt: str = Field(min_length=1)
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    relation: str = Field(pattern=r"^(supports|contradicts)$")
    excerpt_match: str = Field(pattern=r"^(exact|fuzzy|missing)$")


class Claim(ApiModel):
    id: str
    stable_key: str
    text: str
    subject: str
    attribute: str
    period: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2200)
    region: str | None = None
    claim_type: ClaimType
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    independence_group: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNCHECKED
    evidence_grade: EvidenceGrade | None = None
    value: float | None = None
    unit: str | None = None
    currency: str | None = None

    @model_validator(mode="after")
    def validate_numeric_context(self) -> "Claim":
        if self.value is not None and (not self.unit or (self.year is None and not self.period) or not self.region):
            raise ValueError("numeric claims require unit, year or period, and region")
        return self


class StageResult(ApiModel):
    name: str
    state: StageState
    attempt: int = Field(default=1, ge=1)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    provider: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    source_count: int = Field(default=0, ge=0)
    claim_count: int = Field(default=0, ge=0)
    evidence_count: int = Field(default=0, ge=0)
    warning: str | None = None
    error_code: str | None = None


# Backwards-compatible name for the first control-plane implementation.
StageSnapshot = StageResult


class RunEvent(ApiModel):
    id: str
    run_id: str
    type: str
    timestamp: datetime
    message: str
    status: str
    actor: str = "system"
    stage: str | None = None


class RunSummary(ApiModel):
    id: str
    product_name: str
    region: str
    market_definition: str
    created_at: datetime
    updated_at: datetime
    status: RunStatus
    evidence_count: int = Field(ge=0)
    source_count: int = Field(default=0, ge=0)
    claim_count: int = Field(default=0, ge=0)
    verified_claim_count: int = Field(default=0, ge=0)
    report_available: bool
    warnings: list[RunWarning] = Field(default_factory=list)
    proposed_market_definition: MarketDefinitionProposal | None = None
    confirmed_market_definition: MarketDefinitionProposal | None = None


class RunDetail(RunSummary):
    stages: list[StageResult]
    intake: ProductIntake
    sources: list[SourceSnapshot] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)


class EventPage(ApiModel):
    events: list[RunEvent]


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(ApiModel):
    error: ErrorBody
