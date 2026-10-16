import { sampleRuns } from "./fixtures";
import type { MarketDefinitionProposal, ProductIntake, RunSummary } from "./models";

export interface RunsApi {
  listRuns(): Promise<RunSummary[]>;
}

export interface RunCreationApi {
  createRun(input: ProductIntake): Promise<RunSummary>;
  confirmMarketDefinition(runId: string, definition: MarketDefinitionProposal): Promise<RunSummary>;
}

/** Fixture-backed adapter until GET /runs is available from the API. */
export const fixtureRunsApi: RunsApi = {
  async listRuns() {
    await new Promise((resolve) => window.setTimeout(resolve, 350));
    return sampleRuns;
  },
};

const createdRuns = new Map<string, RunSummary>();

export const fixtureRunCreationApi: RunCreationApi = {
  async createRun(input) {
    await new Promise((resolve) => window.setTimeout(resolve, 350));
    const id = `draft-${Date.now()}`;
    const proposedMarketDefinition: MarketDefinitionProposal = {
      category: `${input.productName || "Product"} market`,
      includedBoundaries: `Products serving ${input.targetCustomer} in ${input.region}, priced between ${input.priceRange.currency} ${input.priceRange.minimum} and ${input.priceRange.maximum}.`,
      excludedBoundaries: "Enterprise-only offerings, unrelated categories and markets outside the selected region.",
      competitors: input.competitors?.length ? input.competitors : ["Market leader candidate", "Emerging alternative"],
    };
    const run = {
      id,
      productName: input.productName || "Untitled product idea",
      region: input.region,
      marketDefinition: "Market definition proposed; confirmation required",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: "awaiting_market_confirmation" as const,
      evidenceCount: 0,
      reportAvailable: false,
      warnings: [],
      proposedMarketDefinition,
    };
    createdRuns.set(id, run);
    return run;
  },
  async confirmMarketDefinition(runId, definition) {
    await new Promise((resolve) => window.setTimeout(resolve, 350));
    const existing = createdRuns.get(runId);
    if (!existing) throw new Error("This research draft could not be found.");
    const confirmed = {
      ...existing,
      status: "awaiting_research" as const,
      marketDefinition: definition.category,
      proposedMarketDefinition: definition,
      updatedAt: new Date().toISOString(),
    };
    createdRuns.set(runId, confirmed);
    return confirmed;
  },
};
