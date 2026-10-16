export type RunStatus =
  | "draft"
  | "awaiting_market_confirmation"
  | "awaiting_research"
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
};

export type RunsState =
  | { status: "loading" }
  | { status: "ready"; runs: RunSummary[] }
  | { status: "error"; message: string };
