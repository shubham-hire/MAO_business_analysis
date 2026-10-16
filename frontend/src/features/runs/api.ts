import { sampleRuns } from "./fixtures";
import type { MarketDefinitionProposal, ProductIntake, RunDetail, RunEvent, RunSummary, StageResult } from "./models";

export interface RunsApi {
  listRuns(): Promise<RunSummary[]>;
}

export interface RunCreationApi {
  createRun(input: ProductIntake): Promise<RunSummary>;
  confirmMarketDefinition(runId: string, definition: MarketDefinitionProposal): Promise<RunSummary>;
}

export interface RunDetailApi {
  getRun(runId: string): Promise<RunDetail>;
  getEvents(runId: string, after?: string): Promise<RunEvent[]>;
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
      competitors: input.competitors || [],
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
      status: "queued" as const,
      marketDefinition: definition.category,
      proposedMarketDefinition: definition,
      updatedAt: new Date().toISOString(),
    };
    createdRuns.set(runId, confirmed);
    return confirmed;
  },
};

const fixtureStages = (run: RunSummary): StageResult[] => {
  const names = ["market_statistics", "competitor_research", "customer_voice", "claim_extraction", "evidence_verification", "assessment", "report_generation"];
  return names.map((name, index) => ({
    name,
    state: name === "customer_voice" ? "skipped" : run.status === "completed" ? "completed" : index === 0 && run.status === "running" ? "running" : run.status === "partial" && index < 2 ? "partial" : "pending",
    attempt: 1,
    sourceIds: [],
    claimIds: [],
    evidenceIds: [],
    sourceCount: 0,
    claimCount: 0,
    evidenceCount: 0,
  }));
};

export const fixtureRunDetailApi: RunDetailApi = {
  async getRun(runId) {
    await new Promise((resolve) => window.setTimeout(resolve, 180));
    const run = createdRuns.get(runId) || sampleRuns.find((item) => item.id === runId);
    if (!run) throw new Error("Run not found");
    return { ...run, stages: fixtureStages(run), intake: { productDescription: "Fixture run", targetCustomer: "Unknown", region: run.region, priceRange: { minimum: 0, maximum: 0, currency: "INR" } }, sources: [], claims: [], evidence: [] };
  },
  async getEvents() {
    return [];
  },
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const httpRunsApi: RunsApi = {
  listRuns: () => request<RunSummary[]>("/runs"),
};

export const httpRunCreationApi: RunCreationApi = {
  createRun: (input) => request<RunSummary>("/runs", { method: "POST", body: JSON.stringify(input) }),
  confirmMarketDefinition: (runId, definition) => request<RunSummary>(`/runs/${runId}/market-definition`, { method: "POST", body: JSON.stringify(definition) }),
};

export const httpRunDetailApi: RunDetailApi = {
  getRun: (runId) => request<RunDetail>(`/runs/${runId}`),
  getEvents: (runId, after) => request<{ events: RunEvent[] }>(`/runs/${runId}/events${after ? `?after=${encodeURIComponent(after)}` : ""}`).then((result) => result.events),
};

export const runsApi: RunsApi = apiBaseUrl ? httpRunsApi : fixtureRunsApi;
export const runCreationApi: RunCreationApi = apiBaseUrl ? httpRunCreationApi : fixtureRunCreationApi;
export const runDetailApi: RunDetailApi = apiBaseUrl ? httpRunDetailApi : fixtureRunDetailApi;
