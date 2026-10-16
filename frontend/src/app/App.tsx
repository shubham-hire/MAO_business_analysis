import { useEffect, useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { RunsDashboard } from "../features/runs/dashboard";
import { NewRun } from "../features/runs/newRun";
import { RunDetailPage } from "../features/runs/RunDetailPage";
import type { RunSummary } from "../features/runs/models";
import { LandingPage } from "../features/landing/LandingPage";
import "../features/landing/landing.css";

export function App() {
  const [view, setView] = useState<"landing" | "runs" | "new-run" | "run-detail">(() => initialView());
  const [runId, setRunId] = useState<string | undefined>(() => initialRunId());

  useEffect(() => {
    const handlePopState = () => { setView(initialView()); setRunId(initialRunId()); };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigate(nextView: "landing" | "runs" | "new-run" | "run-detail", run?: RunSummary) {
    setRunId(run?.id || (nextView === "run-detail" ? runId : undefined));
    setView(nextView);
    const path = nextView === "landing" ? "/" : nextView === "new-run" ? "/runs/new" : nextView === "run-detail" && run ? `/runs/${run.id}` : "/runs";
    window.history.pushState({}, "", path);
  }

  if (view === "landing") return <LandingPage onOpenApp={() => navigate("runs")} />;

  return <AppShell currentView={view} onNavigateRuns={() => navigate("runs")} onNavigateNewRun={() => navigate("new-run")}>
    {view === "new-run" ? <NewRun onBackToRuns={() => navigate("runs")} /> : view === "run-detail" && runId ? <RunDetailPage runId={runId} onBack={() => navigate("runs")} /> : <RunsDashboard onStartNewRun={() => navigate("new-run")} onOpenRun={(run) => navigate("run-detail", run)} />}
  </AppShell>;
}

function initialView(): "landing" | "runs" | "new-run" | "run-detail" {
  if (window.location.pathname === "/runs" || window.location.pathname === "/runs/") return "runs";
  if (window.location.pathname === "/runs/new") return "new-run";
  if (window.location.pathname.startsWith("/runs/")) return "run-detail";
  return "landing";
}

function initialRunId(): string | undefined {
  const match = window.location.pathname.match(/^\/runs\/([^/]+)$/);
  return match?.[1];
}
