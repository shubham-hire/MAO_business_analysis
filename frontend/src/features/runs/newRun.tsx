import { useState } from "react";
import { ProductIntakeForm } from "../../components/forms/ProductIntakeForm";
import { MarketDefinitionConfirmation } from "../../components/forms/MarketDefinitionConfirmation";
import { StatusBadge } from "../../components/runs/StatusBadge";
import { fixtureRunCreationApi } from "./api";
import type { ProductIntake, RunSummary } from "./models";
import type { RunCreationApi } from "./api";

type NewRunProps = {
  api?: RunCreationApi;
  onBackToRuns: () => void;
};

export function NewRun({ api = fixtureRunCreationApi, onBackToRuns }: NewRunProps) {
  const [saved, setSaved] = useState<{ run: RunSummary; input: ProductIntake }>();
  const [confirmedRun, setConfirmedRun] = useState<RunSummary>();

  return (
    <main className="new-run-page">
      <section className="new-run-intro">
        <div className="section-marker section-marker-dark">001 / DEFINE THE PRODUCT</div>
        <h1>Start a research run</h1>
        <p>Give the system enough context to find the right market, competitors and sources. You will confirm the proposed market before research begins.</p>
      </section>
      {confirmedRun ? <ResearchReady run={confirmedRun} onBackToRuns={onBackToRuns} /> : saved ? (
        <MarketDefinitionConfirmation
          run={saved.run}
          onConfirm={(definition) => api.confirmMarketDefinition(saved.run.id, definition)}
          onCancel={onBackToRuns}
          onConfirmed={setConfirmedRun}
        />
      ) : (
        <section className="intake-surface" aria-labelledby="intake-title">
          <div className="intake-heading">
            <div>
              <div className="section-marker section-marker-dark">RESEARCH INTAKE</div>
              <h2 id="intake-title">Define the product</h2>
            </div>
            <span className="required-note">* Required fields</span>
          </div>
          <ProductIntakeForm api={api} onSuccess={(run, input) => setSaved({ run, input })} />
        </section>
      )}
    </main>
  );
}

function ResearchReady({ run, onBackToRuns }: { run: RunSummary; onBackToRuns: () => void }) {
  return (
    <section className="draft-saved" aria-labelledby="research-ready-title">
      <div className="saved-mark" aria-hidden="true">✓</div>
      <div>
        <div className="section-marker section-marker-dark">MARKET DEFINITION CONFIRMED</div>
        <h2 id="research-ready-title">The research boundary is set.</h2>
        <p>The market definition for <strong>{run.productName}</strong> is saved. Research has not started yet.</p>
        <div className="saved-summary">
          <span><strong>Status</strong><StatusBadge status={run.status} /></span>
          <span><strong>Evidence</strong>0 verified claims</span>
          <span><strong>Next step</strong>Research can be started by the pipeline</span>
        </div>
        <button className="button button-dark" type="button" onClick={onBackToRuns}>Back to runs <span aria-hidden="true">↗</span></button>
      </div>
    </section>
  );
}
