import { useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { RunsDashboard } from "../features/runs/dashboard";
import { NewRun } from "../features/runs/newRun";
import { LandingPage } from "../features/landing/LandingPage";
import "../features/landing/landing.css";

export function App() {
  const [view, setView] = useState<"landing" | "runs" | "new-run">("landing");

  if (view === "landing") return <LandingPage onOpenApp={() => setView("runs")} />;

  return <AppShell onNavigateNewRun={() => setView("new-run")}>
    {view === "new-run" ? <NewRun onBackToRuns={() => setView("runs")} /> : <RunsDashboard onStartNewRun={() => setView("new-run")} />}
  </AppShell>;
}
