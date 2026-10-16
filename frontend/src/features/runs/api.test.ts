import { describe, expect, it } from "vitest";
import { fixtureRunCreationApi } from "./api";

describe("fixture run creation API", () => {
  it("keeps market confirmation separate from starting research", async () => {
    const run = await fixtureRunCreationApi.createRun({
      productName: "Local delivery marketplace",
      productDescription: "Delivery tools for independent stores.",
      targetCustomer: "Independent retailers",
      region: "India",
      priceRange: { minimum: 100, maximum: 500, currency: "INR" },
      competitors: ["Store A"],
    });

    expect(run.status).toBe("awaiting_market_confirmation");
    expect(run.evidenceCount).toBe(0);
    expect(run.proposedMarketDefinition?.competitors).toEqual(["Store A"]);

    const confirmed = await fixtureRunCreationApi.confirmMarketDefinition(run.id, {
      category: "Local delivery market",
      includedBoundaries: "Independent retailers in India",
      excludedBoundaries: "Enterprise-only offerings",
      competitors: ["Store A", "Store B"],
    });

    expect(confirmed.id).toBe(run.id);
    expect(confirmed.status).toBe("queued");
    expect(confirmed.evidenceCount).toBe(0);
    expect(confirmed.reportAvailable).toBe(false);
  });
});
