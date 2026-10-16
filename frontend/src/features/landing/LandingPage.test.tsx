import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LandingPage } from "./LandingPage";

describe("LandingPage", () => {
  it("presents the evidence-first product and key sections", () => {
    render(<LandingPage onOpenApp={vi.fn()} />);

    expect(screen.getByRole("heading", { name: /Find out if your product idea has a market/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How it works" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sample report preview" })).toBeInTheDocument();
    expect(screen.getByText(/Research has not started yet|market feasibility only/i)).toBeInTheDocument();
  });

  it("opens the authenticated workspace from the primary CTA", async () => {
    const user = userEvent.setup();
    const onOpenApp = vi.fn();
    render(<LandingPage onOpenApp={onOpenApp} />);

    await user.click(screen.getByRole("button", { name: /start a research run/i }));
    expect(onOpenApp).toHaveBeenCalledTimes(1);
  });

  it("keeps the FAQ honest about product scope", () => {
    render(<LandingPage onOpenApp={vi.fn()} />);

    expect(screen.getByText(/This product covers market feasibility only/i)).toBeInTheDocument();
    expect(screen.getByText(/Every claim points back to its origin/i)).toBeInTheDocument();
  });
});
