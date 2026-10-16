import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RunsDashboard } from "./dashboard";
import type { RunSummary } from "./models";

const partialRun: RunSummary = {
  id: "run-007",
  productName: "Evidence-led coffee marketplace",
  region: "India",
  marketDefinition: "Specialty coffee subscription for urban professionals",
  createdAt: "2026-10-16T08:00:00Z",
  updatedAt: "2026-10-16T09:00:00Z",
  status: "partial",
  evidenceCount: 12,
  reportAvailable: true,
  warnings: [{ message: "One permitted source was unavailable." }],
};

describe("RunsDashboard", () => {
  it("renders the run status as readable text and exposes partial warnings", () => {
    render(<RunsDashboard initialRuns={[partialRun]} />);

    expect(screen.getByText("Partial results")).toBeInTheDocument();
    expect(screen.getByText("One permitted source was unavailable.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open evidence-led coffee marketplace/i })).toBeInTheDocument();
  });

  it("shows an empty state with a first-run action", () => {
    render(<RunsDashboard initialRuns={[]} />);

    expect(screen.getByText("Start with a product question.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start your first run/i })).toBeInTheDocument();
  });

  it("shows an error and retries the API request", async () => {
    const api = {
      listRuns: vi
        .fn<() => Promise<RunSummary[]>>()
        .mockRejectedValueOnce(new Error("network"))
        .mockResolvedValueOnce([partialRun]),
    };
    const user = userEvent.setup();
    render(<RunsDashboard api={api} />);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /try again/i }));

    await waitFor(() => expect(screen.getByText(partialRun.productName)).toBeInTheDocument());
    expect(api.listRuns).toHaveBeenCalledTimes(2);
  });

  it("renders loading skeletons before the API resolves", async () => {
    let resolveRequest!: (runs: RunSummary[]) => void;
    const api = {
      listRuns: vi.fn(() => new Promise<RunSummary[]>((resolve) => { resolveRequest = resolve; })),
    };
    render(<RunsDashboard api={api} />);

    expect(screen.getByLabelText("Loading research runs")).toBeInTheDocument();
    await waitFor(() => expect(api.listRuns).toHaveBeenCalledTimes(1));
    resolveRequest([]);
    expect(await screen.findByText("Start with a product question.")).toBeInTheDocument();
  });
});
