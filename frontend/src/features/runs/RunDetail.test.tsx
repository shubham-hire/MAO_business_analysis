import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RunDetail } from "./RunDetail";
import type { RunDetail as RunDetailModel } from "./models";

const run: RunDetailModel = {
  id: "run-001",
  productName: "Sustainable packaging subscription",
  region: "India",
  marketDefinition: "B2B recurring packaging for small food businesses",
  createdAt: "2026-10-12T09:30:00Z",
  updatedAt: "2026-10-15T15:45:00Z",
  status: "completed",
  evidenceCount: 1,
  reportAvailable: true,
  warnings: [],
  sourceCount: 2,
  claimCount: 3,
  verifiedClaimCount: 2,
  stages: [
    { name: "market_statistics", state: "completed" as const, attempt: 1, sourceIds: ["source-1"], claimIds: [], evidenceIds: [], sourceCount: 1, claimCount: 0, evidenceCount: 0, iterations: 2, queryCount: 2, modelCallCount: 2, coverage: { summary: "Coverage reviewed.", coveredDimensions: ["market_size"], missingDimensions: ["market_growth"] } },
    { name: "competitor_research", state: "completed" as const, attempt: 1, sourceIds: ["source-2"], claimIds: [], evidenceIds: [], sourceCount: 1, claimCount: 0, evidenceCount: 0 },
    { name: "customer_voice", state: "skipped" as const, attempt: 1, sourceIds: [], claimIds: [], evidenceIds: [], sourceCount: 0, claimCount: 0, evidenceCount: 0 },
    { name: "claim_extraction", state: "completed" as const, attempt: 1, sourceIds: [], claimIds: ["claim-1"], evidenceIds: [], sourceCount: 0, claimCount: 1, evidenceCount: 0 },
    { name: "evidence_verification", state: "completed" as const, attempt: 1, sourceIds: [], claimIds: [], evidenceIds: ["evidence-1"], sourceCount: 0, claimCount: 0, evidenceCount: 1 },
    { name: "assessment", state: "pending" as const, attempt: 1, sourceIds: [], claimIds: [], evidenceIds: [], sourceCount: 0, claimCount: 0, evidenceCount: 0 },
    { name: "report_generation", state: "pending" as const, attempt: 1, sourceIds: [], claimIds: [], evidenceIds: [], sourceCount: 0, claimCount: 0, evidenceCount: 0 },
  ],
  intake: { productDescription: "Sustainable packaging", targetCustomer: "Food businesses", region: "India", priceRange: { minimum: 10, maximum: 20, currency: "INR" } },
  sources: [],
  claims: [],
  evidence: [],
  competitorObservations: [{ competitorName: "Known Co", sourceType: "user_listed", identity: "Known Co marketplace", targetCustomer: "Independent retailers", features: ["delivery"], positioning: "For local retailers", publishedPricing: "INR 999/month", pricingStatus: "published", billingPeriod: "monthly", currency: "INR", regionalAvailability: "India", sourceIds: ["source-1"], verificationStatus: "unchecked" }],
};

describe("RunDetail", () => {
  it("shows concrete run state and verified claim count", () => {
    render(<RunDetail run={run} onBack={vi.fn()} />);

    expect(screen.getByRole("heading", { name: run.productName })).toBeInTheDocument();
    expect(screen.getByText("Verified claims")).toBeInTheDocument();
    expect(screen.getByText(/Report available/)).toBeInTheDocument();
    expect(screen.getByTestId("market_statistics-progress")).toHaveTextContent("2 queries · 2 model calls");
    expect(screen.getByTestId("market_statistics-coverage-gap")).toHaveTextContent("Missing: market growth");
    expect(screen.getByText("Known Co")).toBeInTheDocument();
    expect(screen.getByText("INR 999/month")).toBeInTheDocument();
  });
});
