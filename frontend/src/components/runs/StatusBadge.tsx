import type { RunStatus } from "../../features/runs/models";

const labels: Record<RunStatus, string> = {
  draft: "Draft",
  awaiting_market_confirmation: "Awaiting market confirmation",
  queued: "Queued",
  running: "Researching",
  partial: "Partial results",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span className={`status-badge status-${status}`}>
      <span className="status-dot" aria-hidden="true" />
      {labels[status]}
    </span>
  );
}
