import type { RunDetail as RunDetailModel, StageResult } from "./models";
import { StatusBadge } from "../../components/runs/StatusBadge";

type RunDetailProps = {
  run: RunDetailModel;
  onBack: () => void;
};

export function RunDetail({ run, onBack }: RunDetailProps) {
  return (
    <main className="run-detail-page">
      <button className="back-link" type="button" onClick={onBack}>← Back to runs</button>
      <section className="run-detail-header">
        <div><div className="section-marker section-marker-dark">003 / RUN OVERVIEW</div><h1>{run.productName}</h1><p>{run.marketDefinition}</p></div>
        <div className="run-detail-status"><StatusBadge status={run.status} /><span>{run.region}</span></div>
      </section>

      <div className="run-detail-tabs" role="tablist" aria-label="Run sections">
        <button className="run-tab run-tab-active" type="button" role="tab" aria-selected="true">Summary</button>
        <button className="run-tab" type="button" role="tab" aria-selected="false" disabled>Market</button>
        <button className="run-tab" type="button" role="tab" aria-selected="false" disabled>Competitors</button>
        <button className="run-tab" type="button" role="tab" aria-selected="false" disabled>Evidence</button>
        <span className="run-tab-note">Sections unlock as data is collected.</span>
      </div>

      <div className="run-detail-grid">
        <section className="detail-panel detail-progress" aria-labelledby="run-progress-title">
          <div className="detail-panel-heading"><div><div className="section-marker section-marker-dark">PROCESS</div><h2 id="run-progress-title">Research stages</h2></div><span className="detail-count">{stageCountLabel(run.stages)}</span></div>
          <div className="stage-list">{run.stages.map((stage) => <StageRow key={stage.name} stage={stage} />)}</div>
        </section>

        <section className="detail-panel detail-evidence" aria-labelledby="evidence-title">
          <div className="detail-panel-heading"><div><div className="section-marker section-marker-dark">ARTIFACTS</div><h2 id="evidence-title">What exists</h2></div><span className="evidence-total">{run.verifiedClaimCount ?? 0}</span></div>
          <div className="artifact-counts"><ArtifactCount label="Sources" value={run.sourceCount ?? run.sources.length} /><ArtifactCount label="Claims" value={run.claimCount ?? run.claims.length} /><ArtifactCount label="Evidence records" value={run.evidenceCount ?? run.evidence.length} /><ArtifactCount label="Verified claims" value={run.verifiedClaimCount ?? run.claims.filter((claim) => claim.verificationStatus === "verified").length} /></div>
          {run.warnings.length > 0 ? <div className="detail-empty detail-provider-warning"><span aria-hidden="true">!</span><p>{run.warnings[0].message}</p></div> : run.sources.length === 0 ? <div className="detail-empty"><span aria-hidden="true">—</span><p>No external evidence has been collected for this run yet.</p></div> : <div className="evidence-summary"><strong>{run.sources.length} source snapshots retained</strong><p>Source material is stored with the run so later verification can be replayed.</p></div>}
        </section>
      </div>

      <footer className="run-detail-footer"><span>Created {formatDate(run.createdAt)}</span><span>Updated {formatDate(run.updatedAt)}</span><span>{run.reportAvailable ? "Report available · snapshot ready" : "Report not available"}</span></footer>
    </main>
  );
}

function StageRow({ stage }: { stage: StageResult }) {
  const labels: Record<string, string> = { market_statistics: "Market statistics", competitor_research: "Competitor research", customer_voice: "Customer voice", claim_extraction: "Claim extraction", evidence_verification: "Evidence verification", assessment: "Feasibility assessment", report_generation: "Report generation" };
  const descriptions: Record<string, string> = { market_statistics: "Figures with year, region and market definition.", competitor_research: "Products, features and published pricing.", customer_voice: "Optional permitted public feedback.", claim_extraction: "Source material turned into stable claims.", evidence_verification: "Excerpts checked against stored source text.", assessment: "Seven dimensions using verified claims.", report_generation: "Decision-support report artifact." };
  return <div className="detail-stage"><span className={`stage-marker stage-${stage.state}`}>{stage.state === "completed" ? "✓" : stage.state === "skipped" ? "—" : stage.name.slice(0, 2).toUpperCase()}</span><div><strong>{labels[stage.name] || stage.name}</strong><p>{stage.warning || descriptions[stage.name] || "Stage status from the orchestration service."}</p></div><span className="stage-state">{stage.state}</span></div>;
}

function ArtifactCount({ label, value }: { label: string; value: number }) {
  return <div><span>{label}</span><strong>{value.toString().padStart(2, "0")}</strong></div>;
}

function stageCountLabel(stages: StageResult[]) {
  const terminal = stages.filter((stage) => ["completed", "partial", "failed", "skipped"].includes(stage.state)).length;
  return `${terminal} / ${stages.length}`;
}

function formatDate(date: string) {
  return new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric" }).format(new Date(date));
}
