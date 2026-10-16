export type RunStatus =
  | "draft"
  | "awaiting_market_confirmation"
  | "queued"
  | "running"
  | "partial"
  | "completed"
  | "failed"
  | "cancelled";

export type RunWarning = {
  stage?: string;
  source?: string;
  message: string;
};

export type ProductIntake = {
  productName?: string;
  productDescription: string;
  targetCustomer: string;
  region: string;
  priceRange: {
    minimum: number;
    maximum: number;
    currency: string;
  };
  competitors?: string[];
  additionalContext?: string;
};

export type MarketDefinitionProposal = {
  category: string;
  includedBoundaries: string;
  excludedBoundaries: string;
  competitors: string[];
};

export type RunSummary = {
  id: string;
  productName: string;
  region: string;
  marketDefinition: string;
  createdAt: string;
  updatedAt: string;
  status: RunStatus;
  evidenceCount: number;
  reportAvailable: boolean;
  warnings: RunWarning[];
  proposedMarketDefinition?: MarketDefinitionProposal;
  sourceCount?: number;
  claimCount?: number;
  verifiedClaimCount?: number;
};

export type StageState = "pending" | "running" | "completed" | "partial" | "failed" | "skipped";

export type StageResult = {
  name: string;
  state: StageState;
  attempt: number;
  startedAt?: string;
  completedAt?: string;
  provider?: string;
  sourceIds: string[];
  claimIds: string[];
  evidenceIds: string[];
  sourceCount: number;
  claimCount: number;
  evidenceCount: number;
  warning?: string;
  errorCode?: string;
  iterations?: number;
  queryCount?: number;
  modelCallCount?: number;
  usage?: Record<string, number>;
  coverage?: CoverageSnapshot;
  budgetExhausted?: boolean;
  observations?: CompetitorObservation[];
};

export type CoverageSnapshot = {
  summary: string;
  coveredDimensions: string[];
  missingDimensions: string[];
};

export type CompetitorObservation = {
  competitorName: string;
  sourceType: "user_listed" | "discovered";
  identity: string;
  targetCustomer: string;
  features: string[];
  positioning: string;
  publishedPricing: string;
  pricingStatus: "published" | "unknown" | "not_found";
  billingPeriod: string;
  currency: string;
  regionalAvailability: string;
  sourceIds: string[];
  verificationStatus: "verified" | "unsupported" | "unchecked";
};

export type SourceSnapshot = {
  id: string;
  title: string;
  url: string;
  publisher: string;
  publicationDate?: string;
  retrievalDate: string;
  contentHash: string;
  storedText?: string;
  permittedExcerpt?: string;
  origin: string;
  provider: string;
};

export type Claim = {
  id: string;
  stableKey: string;
  text: string;
  subject: string;
  attribute: string;
  period?: string;
  year?: number;
  region?: string;
  claimType: string;
  sourceIds: string[];
  evidenceIds: string[];
  independenceGroup?: string;
  verificationStatus: "verified" | "unsupported" | "unchecked";
  evidenceGrade?: "A" | "B" | "C" | "D";
  value?: number;
  unit?: string;
  currency?: string;
};

export type EvidenceRecord = {
  id: string;
  claimId: string;
  sourceId: string;
  excerpt: string;
  startOffset?: number;
  endOffset?: number;
  relation: "supports" | "contradicts";
  excerptMatch: "exact" | "fuzzy" | "missing";
};

export type RunEvent = {
  id: string;
  runId: string;
  type: string;
  timestamp: string;
  message: string;
  status: string;
  actor: string;
  stage?: string;
};

export type RunDetail = RunSummary & {
  stages: StageResult[];
  intake: ProductIntake;
  sources: SourceSnapshot[];
  claims: Claim[];
  evidence: EvidenceRecord[];
  competitorObservations?: CompetitorObservation[];
};

export type RunsState =
  | { status: "loading" }
  | { status: "ready"; runs: RunSummary[] }
  | { status: "error"; message: string };
