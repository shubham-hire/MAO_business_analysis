import { useCallback, useEffect, useState } from "react";
import { ErrorState } from "../../components/feedback/ErrorState";
import { LoadingState } from "../../components/feedback/LoadingState";
import { RunDetail } from "./RunDetail";
import { runDetailApi } from "./api";
import type { RunDetail as RunDetailModel } from "./models";

export function RunDetailPage({ runId, onBack }: { runId: string; onBack: () => void }) {
  const [detail, setDetail] = useState<RunDetailModel>();
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const next = await runDetailApi.getRun(runId);
      setDetail(next);
      setError("");
    } catch {
      setError("We could not load this run. The run may have been removed or the API is unavailable.");
    }
  }, [runId]);

  useEffect(() => {
    let active = true;
    runDetailApi.getRun(runId).then((next) => {
      if (!active) return;
      setDetail(next);
      setError("");
    }).catch(() => {
      if (!active) return;
      setError("We could not load this run. The run may have been removed or the API is unavailable.");
    });
    return () => { active = false; };
  }, [runId]);

  useEffect(() => {
    if (!detail || !["queued", "running"].includes(detail.status)) return;
    const timer = window.setInterval(() => { void load(); }, 3000);
    return () => window.clearInterval(timer);
  }, [detail, load]);

  if (error && !detail) return <main className="run-detail-page"><ErrorState message={error} onRetry={() => void load()} /></main>;
  if (!detail) return <main className="run-detail-page"><LoadingState /></main>;
  return <RunDetail run={detail} onBack={onBack} />;
}
