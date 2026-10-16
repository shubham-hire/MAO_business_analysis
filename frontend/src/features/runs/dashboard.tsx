import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/feedback/EmptyState";
import { ErrorState } from "../../components/feedback/ErrorState";
import { LoadingState } from "../../components/feedback/LoadingState";
import { RunCard } from "../../components/runs/RunCard";
import { fixtureRunsApi } from "./api";
import type { RunsApi } from "./api";
import type { RunSummary, RunsState } from "./models";

type DashboardProps = {
  api?: RunsApi;
  initialRuns?: RunSummary[];
  onStartNewRun?: () => void;
};

export function RunsDashboard({ api = fixtureRunsApi, initialRuns, onStartNewRun }: DashboardProps) {
  const [state, setState] = useState<RunsState>(() =>
    initialRuns ? { status: "ready", runs: initialRuns } : { status: "loading" },
  );

  const loadRuns = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const runs = await api.listRuns();
      setState({ status: "ready", runs });
    } catch {
      setState({
        status: "error",
        message: "We could not load your runs. Your saved research is safe; try again when you are ready.",
      });
    }
  }, [api]);

  useEffect(() => {
    if (!initialRuns) {
      void Promise.resolve().then(loadRuns);
    }
  }, [initialRuns, loadRuns]);

  const metrics = useMemo(() => {
    const runs = state.status === "ready" ? state.runs : [];
    return {
      active: runs.filter((run) => ["queued", "running"].includes(run.status)).length,
      completed: runs.filter((run) => run.status === "completed").length,
      evidence: runs.reduce((total, run) => total + run.evidenceCount, 0),
      latest: runs.length > 0 ? formatDate(runs[0].updatedAt) : "—",
    };
  }, [state]);

  return (
    <main className="dashboard-page">
      <section className="dashboard-hero" aria-labelledby="dashboard-title">
        <div className="section-marker">001 / RESEARCH RUNS</div>
        <div className="hero-row">
          <div className="hero-copy">
            <h1 id="dashboard-title">Your research runs</h1>
            <p>Trace the evidence behind your next market decision.</p>
          </div>
          <button className="button button-light" type="button" onClick={onStartNewRun}>
            <span aria-hidden="true">+</span> Start new run
          </button>
        </div>
        <div className="metric-strip" aria-label="Research summary">
          <Metric label="Active runs" value={metrics.active.toString().padStart(2, "0")} />
          <Metric label="Completed" value={metrics.completed.toString().padStart(2, "0")} />
          <Metric label="Verified evidence" value={metrics.evidence.toString().padStart(2, "0")} />
          <Metric label="Latest activity" value={metrics.latest} />
        </div>
      </section>

      <section className="runs-section" aria-labelledby="recent-runs-title">
        <div className="section-heading">
          <div>
            <div className="section-marker section-marker-dark">002 / SNAPSHOTS</div>
            <h2 id="recent-runs-title">Recent research</h2>
          </div>
          <span className="section-count">
            {state.status === "ready" ? `${state.runs.length.toString().padStart(2, "0")} runs` : "Loading"}
          </span>
        </div>

        {state.status === "loading" && <LoadingState />}
        {state.status === "error" && <ErrorState message={state.message} onRetry={() => void loadRuns()} />}
        {state.status === "ready" && state.runs.length === 0 && <EmptyState onStartNewRun={onStartNewRun} />}
        {state.status === "ready" && state.runs.length > 0 && (
          <div className="run-list">
            {state.runs.map((run) => (
              <RunCard key={run.id} run={run} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatDate(date: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(new Date(date));
}
