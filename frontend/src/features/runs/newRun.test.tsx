import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NewRun } from "./newRun";
import type { MarketDefinitionProposal, ProductIntake, RunSummary } from "./models";

const draft: RunSummary = {
  id: "draft-001",
  productName: "Local delivery marketplace",
  region: "India",
  marketDefinition: "Market definition proposed; confirmation required",
  createdAt: "2026-10-16T08:00:00Z",
  updatedAt: "2026-10-16T08:00:00Z",
  status: "awaiting_market_confirmation",
  evidenceCount: 0,
  reportAvailable: false,
  warnings: [],
  proposedMarketDefinition: {
    category: "Local delivery marketplace",
    includedBoundaries: "Independent retailers in India",
    excludedBoundaries: "Enterprise-only offerings",
    competitors: ["Store A", "Store B"],
  },
};

function fillRequiredFields() {
  return async (user: ReturnType<typeof userEvent.setup>) => {
    await user.type(screen.getByLabelText(/Product name/), "Local delivery marketplace");
    await user.type(screen.getByLabelText(/What are you researching/), "A delivery marketplace for independent local stores.");
    await user.type(screen.getByLabelText(/Target customer/), "Independent retailers");
    await user.type(screen.getByLabelText(/Target region/), "India");
    await user.type(screen.getByLabelText(/Minimum price/), "100");
    await user.type(screen.getByLabelText(/Maximum price/), "500");
  };
}

describe("NewRun", () => {
  it("renders the intake fields and budget notice", () => {
    render(<NewRun onBackToRuns={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "Start a research run" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Product name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/What are you researching/)).toBeInTheDocument();
    expect(screen.getByText("Research budget notice")).toBeInTheDocument();
  });

  it("validates required fields and preserves entered values", async () => {
    const user = userEvent.setup();
    render(<NewRun onBackToRuns={vi.fn()} />);
    const description = screen.getByLabelText(/What are you researching/);
    await user.type(description, "A product idea");
    await user.click(screen.getByRole("button", { name: /continue to market definition/i }));

    expect(screen.getAllByText("This field is required.").length).toBeGreaterThan(0);
    expect(description).toHaveValue("A product idea");
    expect(screen.getByLabelText(/Target customer/)).toHaveAttribute("aria-invalid", "true");
  });

  it("rejects an inverted price range", async () => {
    const user = userEvent.setup();
    render(<NewRun onBackToRuns={vi.fn()} />);
    await user.type(screen.getByLabelText(/What are you researching/), "A product idea");
    await user.type(screen.getByLabelText(/Target customer/), "Founders");
    await user.type(screen.getByLabelText(/Target region/), "India");
    await user.type(screen.getByLabelText(/Minimum price/), "500");
    await user.type(screen.getByLabelText(/Maximum price/), "100");
    await user.click(screen.getByRole("button", { name: /continue to market definition/i }));

    expect(screen.getByText("Minimum price cannot be greater than maximum price.")).toBeInTheDocument();
  });

  it("submits normalized intake data and opens the market confirmation gate", async () => {
    const user = userEvent.setup();
    const createRun = vi.fn<(input: ProductIntake) => Promise<RunSummary>>().mockResolvedValue(draft);
    const confirmMarketDefinition = vi.fn<(id: string, definition: MarketDefinitionProposal) => Promise<RunSummary>>();
    render(<NewRun api={{ createRun, confirmMarketDefinition }} onBackToRuns={vi.fn()} />);
    await fillRequiredFields()(user);
    await user.type(screen.getByLabelText(/Known competitors/), "Store A\n Store B ");
    await user.click(screen.getByRole("button", { name: /continue to market definition/i }));

    await waitFor(() => expect(createRun).toHaveBeenCalledTimes(1));
    expect(createRun).toHaveBeenCalledWith({
      productName: "Local delivery marketplace",
      productDescription: "A delivery marketplace for independent local stores.",
      targetCustomer: "Independent retailers",
      region: "India",
      priceRange: { minimum: 100, maximum: 500, currency: "INR" },
      competitors: ["Store A", "Store B"],
    });
    expect(await screen.findByRole("heading", { name: "Make the boundary explicit." })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Local delivery marketplace")).toBeInTheDocument();
    expect(screen.getByText("Awaiting market confirmation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm market definition/i })).toBeDisabled();
    expect(confirmMarketDefinition).not.toHaveBeenCalled();
  });

  it("requires explicit confirmation, submits edited boundaries and does not start research", async () => {
    const user = userEvent.setup();
    const createRun = vi.fn<(input: ProductIntake) => Promise<RunSummary>>().mockResolvedValue(draft);
    const readyRun: RunSummary = { ...draft, status: "awaiting_research", marketDefinition: "Edited delivery market" };
    const confirmMarketDefinition = vi.fn<(id: string, definition: MarketDefinitionProposal) => Promise<RunSummary>>().mockResolvedValue(readyRun);
    render(<NewRun api={{ createRun, confirmMarketDefinition }} onBackToRuns={vi.fn()} />);
    await fillRequiredFields()(user);
    await user.click(screen.getByRole("button", { name: /continue to market definition/i }));
    await screen.findByRole("heading", { name: "Make the boundary explicit." });

    const category = screen.getByLabelText(/Proposed category/);
    await user.clear(category);
    await user.type(category, "Edited delivery market");
    await user.click(screen.getByLabelText(/I confirm this is the market definition/));
    expect(screen.getByRole("button", { name: /confirm market definition/i })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: /confirm market definition/i }));

    await waitFor(() => expect(confirmMarketDefinition).toHaveBeenCalledWith("draft-001", {
      category: "Edited delivery market",
      includedBoundaries: "Independent retailers in India",
      excludedBoundaries: "Enterprise-only offerings",
      competitors: ["Store A", "Store B"],
    }));
    expect(await screen.findByRole("heading", { name: "The research boundary is set." })).toBeInTheDocument();
    expect(screen.getByText("Awaiting research")).toBeInTheDocument();
    expect(screen.getByText(/Research has not started yet/)).toBeInTheDocument();
  });

  it("shows API errors while keeping the form available", async () => {
    const user = userEvent.setup();
    const createRun = vi.fn<(input: ProductIntake) => Promise<RunSummary>>().mockRejectedValue(new Error("offline"));
    const confirmMarketDefinition = vi.fn<(id: string, definition: MarketDefinitionProposal) => Promise<RunSummary>>();
    render(<NewRun api={{ createRun, confirmMarketDefinition }} onBackToRuns={vi.fn()} />);
    await fillRequiredFields()(user);
    await user.click(screen.getByRole("button", { name: /continue to market definition/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("We could not save this draft");
    expect(screen.getByDisplayValue("Local delivery marketplace")).toBeInTheDocument();
  });
});
