import { useState, type FormEvent } from "react";
import type { MarketDefinitionProposal, ProductIntake, RunSummary } from "../../features/runs/models";
import { StatusBadge } from "../runs/StatusBadge";

type MarketDefinitionConfirmationProps = {
  run: RunSummary;
  intake: ProductIntake;
  onConfirm: (definition: MarketDefinitionProposal) => Promise<RunSummary>;
  onCancel: () => void;
  onConfirmed: (run: RunSummary) => void;
};

export function MarketDefinitionConfirmation({ run, intake, onConfirm, onCancel, onConfirmed }: MarketDefinitionConfirmationProps) {
  const [definition, setDefinition] = useState<MarketDefinitionProposal>(run.proposedMarketDefinition ?? {
    category: "",
    includedBoundaries: "",
    excludedBoundaries: "",
    competitors: [],
  });
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const hasRequiredDefinition = Boolean(definition.category.trim() && definition.includedBoundaries.trim());

  function updateDefinition(field: "category" | "includedBoundaries" | "excludedBoundaries", value: string) {
    setDefinition((current) => ({ ...current, [field]: value }));
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasRequiredDefinition || !confirmed) return;
    setIsSubmitting(true);
    setError("");
    try {
      const nextRun = await onConfirm({
        ...definition,
        category: definition.category.trim(),
        includedBoundaries: definition.includedBoundaries.trim(),
        excludedBoundaries: definition.excludedBoundaries.trim(),
        competitors: definition.competitors.map((competitor) => competitor.trim()).filter(Boolean),
      });
      onConfirmed(nextRun);
    } catch {
      setError("We could not confirm this market definition. Your edits are still here; try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="market-definition-page" aria-labelledby="market-definition-title">
      <div className="market-definition-intro">
        <div className="section-marker section-marker-dark">002 / CONFIRM THE MARKET</div>
        <h2 id="market-definition-title">Make the boundary explicit.</h2>
        <p>Statistics and competitor results depend on this definition. Review the proposal, edit anything that is too broad or narrow, then confirm the scope before research starts.</p>
        <div className="definition-status"><StatusBadge status={run.status} /><span>Confirmation is required before the pipeline can run.</span></div>
      </div>

      <div className="scope-summary" aria-label="Confirmed intake context">
        <div><span>Target customer</span><strong>{intake.targetCustomer}</strong></div>
        <div><span>Region</span><strong>{intake.region}</strong></div>
        <div><span>Expected price</span><strong>{intake.priceRange.currency} {intake.priceRange.minimum.toLocaleString()}–{intake.priceRange.maximum.toLocaleString()}</strong></div>
      </div>

      <form className="definition-form" onSubmit={handleSubmit} noValidate>
        <div className="definition-fields">
          <Field label="Proposed category" id="marketCategory" value={definition.category} onChange={(value) => updateDefinition("category", value)} required />
          <Field label="Included market boundaries" id="includedBoundaries" value={definition.includedBoundaries} onChange={(value) => updateDefinition("includedBoundaries", value)} required textarea />
          <Field label="Excluded market boundaries" id="excludedBoundaries" value={definition.excludedBoundaries} onChange={(value) => updateDefinition("excludedBoundaries", value)} textarea />
          <div className="competitor-editor">
            <label className="form-label" htmlFor="proposedCompetitors">Proposed competitors <small>One per line</small></label>
            <textarea id="proposedCompetitors" rows={4} value={definition.competitors.join("\n")} onChange={(event) => setDefinition((current) => ({ ...current, competitors: event.target.value.split("\n") }))} />
            <span className="field-help">Products are proposed with a reason during the research setup. Remove anything that does not belong.</span>
          </div>
        </div>

        <div className="definition-warning" role="note">
          <span aria-hidden="true">!</span>
          <p><strong>This is a research gate.</strong> Confirming saves the market definition and makes the run ready for research. It does not silently change the scope later.</p>
        </div>

        <label className="confirmation-check">
          <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
          <span>I confirm this is the market definition for this run.</span>
        </label>

        {error && <div className="form-submit-error" role="alert">{error}</div>}
        <div className="definition-actions">
          <button className="button button-dark" disabled={!hasRequiredDefinition || !confirmed || isSubmitting} type="submit">{isSubmitting ? "Saving definition…" : "Confirm market definition"}<span aria-hidden="true">↗</span></button>
          <button className="text-button" type="button" onClick={onCancel}>Cancel and return to runs</button>
        </div>
      </form>
    </section>
  );
}

function Field({ label, id, value, onChange, required, textarea }: { label: string; id: string; value: string; onChange: (value: string) => void; required?: boolean; textarea?: boolean }) {
  return (
    <div className="form-field">
      <label className="form-label" htmlFor={id}>{label} {required && <span aria-hidden="true">*</span>}</label>
      {textarea ? <textarea id={id} rows={4} value={value} onChange={(event) => onChange(event.target.value)} /> : <input id={id} value={value} onChange={(event) => onChange(event.target.value)} />}
    </div>
  );
}
