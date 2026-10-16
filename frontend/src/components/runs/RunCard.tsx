import type { RunSummary } from "../../features/runs/models";
import { StatusBadge } from "./StatusBadge";

export function RunCard({ run }: { run: RunSummary }) {
  const hasWarning = run.warnings.length > 0;

  return (
    <article className={`run-card ${hasWarning ? "run-card-warning" : ""}`}>
      <div className="run-number" aria-hidden="true">{run.id.replace("run-", "").padStart(3, "0")}</div>
      <div className="run-main">
        <div className="run-topline">
          <StatusBadge status={run.status} />
          <span className="run-date">Updated {formatDate(run.updatedAt)}</span>
        </div>
        <h3>{run.productName}</h3>
        <p className="run-definition">{run.marketDefinition}</p>
        <div className="run-meta">
          <span><strong>Region</strong> {run.region}</span>
          <span><strong>Evidence</strong> {run.evidenceCount ? `${run.evidenceCount} verified claims` : "Collecting"}</span>
        </div>
        {hasWarning && (
          <div className="run-warning" role="status">
            <span aria-hidden="true">△</span>
            <span>{run.warnings[0].message}</span>
          </div>
        )}
      </div>
      <a className="run-open" href={`#${run.id}`} aria-label={`Open ${run.productName} research run`}>
        <span>Open run</span><span aria-hidden="true">↗</span>
      </a>
    </article>
  );
}

function formatDate(date: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(date));
}
