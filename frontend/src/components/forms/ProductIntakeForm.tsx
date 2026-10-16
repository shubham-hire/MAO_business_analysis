import { cloneElement, isValidElement, useState, type FormEvent, type ReactElement, type ReactNode } from "react";
import type { ProductIntake, RunSummary } from "../../features/runs/models";
import type { RunCreationApi } from "../../features/runs/api";

type FormValues = {
  productName: string;
  productDescription: string;
  targetCustomer: string;
  region: string;
  minimumPrice: string;
  maximumPrice: string;
  currency: string;
  competitors: string;
  additionalContext: string;
};

type FormErrors = Partial<Record<keyof FormValues | "priceRange", string>>;

const initialValues: FormValues = {
  productName: "",
  productDescription: "",
  targetCustomer: "",
  region: "",
  minimumPrice: "",
  maximumPrice: "",
  currency: "INR",
  competitors: "",
  additionalContext: "",
};

type ProductIntakeFormProps = {
  api: RunCreationApi;
  onSuccess: (run: RunSummary, input: ProductIntake) => void;
};

export function ProductIntakeForm({ api, onSuccess }: ProductIntakeFormProps) {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateValue(field: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => {
      const next = { ...current };
      delete next[field];
      if (field === "minimumPrice" || field === "maximumPrice") delete next.priceRange;
      return next;
    });
    setSubmitError("");
  }

  function validate() {
    const nextErrors: FormErrors = {};
    const requiredText: Array<keyof FormValues> = ["productDescription", "targetCustomer", "region", "currency"];
    for (const field of requiredText) {
      if (!values[field].trim()) nextErrors[field] = "This field is required.";
    }

    const minimum = Number(values.minimumPrice);
    const maximum = Number(values.maximumPrice);
    if (!values.minimumPrice.trim() || !Number.isFinite(minimum) || minimum < 0) {
      nextErrors.minimumPrice = "Enter a non-negative minimum price.";
    }
    if (!values.maximumPrice.trim() || !Number.isFinite(maximum) || maximum < 0) {
      nextErrors.maximumPrice = "Enter a non-negative maximum price.";
    }
    if (!nextErrors.minimumPrice && !nextErrors.maximumPrice && minimum > maximum) {
      nextErrors.priceRange = "Minimum price cannot be greater than maximum price.";
    }
    return nextErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const input: ProductIntake = {
      productDescription: values.productDescription.trim(),
      targetCustomer: values.targetCustomer.trim(),
      region: values.region.trim(),
      priceRange: {
        minimum: Number(values.minimumPrice),
        maximum: Number(values.maximumPrice),
        currency: values.currency.trim(),
      },
    };
    const productName = values.productName.trim();
    const competitors = values.competitors.split("\n").map((item) => item.trim()).filter(Boolean);
    const additionalContext = values.additionalContext.trim();
    if (productName) input.productName = productName;
    if (competitors.length > 0) input.competitors = competitors;
    if (additionalContext) input.additionalContext = additionalContext;

    setIsSubmitting(true);
    setSubmitError("");
    try {
      const run = await api.createRun(input);
      onSuccess(run, input);
    } catch {
      setSubmitError("We could not save this draft. Your information is still here; try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="intake-form" onSubmit={handleSubmit} noValidate>
      <div className="form-grid">
        <Field label="Product name" hint="Optional" error={errors.productName}>
          <input id="productName" value={values.productName} onChange={(event) => updateValue("productName", event.target.value)} />
        </Field>
        <Field label="Target customer" required error={errors.targetCustomer}>
          <input id="targetCustomer" value={values.targetCustomer} onChange={(event) => updateValue("targetCustomer", event.target.value)} aria-invalid={Boolean(errors.targetCustomer)} />
        </Field>
      </div>

      <Field label="What are you researching?" required hint="Describe the product or idea in plain language." error={errors.productDescription}>
        <textarea id="productDescription" rows={5} value={values.productDescription} onChange={(event) => updateValue("productDescription", event.target.value)} aria-invalid={Boolean(errors.productDescription)} />
      </Field>

      <div className="form-grid">
        <Field label="Target region" required error={errors.region}>
          <input id="region" value={values.region} onChange={(event) => updateValue("region", event.target.value)} aria-invalid={Boolean(errors.region)} />
        </Field>
        <Field label="Known competitors" hint="Optional · one per line">
          <textarea id="competitors" rows={3} value={values.competitors} onChange={(event) => updateValue("competitors", event.target.value)} />
        </Field>
      </div>

      <fieldset className="price-fieldset">
        <legend>Expected price range <span>(required)</span></legend>
        <div className="price-fields">
          <Field label="Minimum price" error={errors.minimumPrice || errors.priceRange}>
            <input id="minimumPrice" inputMode="decimal" min="0" step="0.01" type="number" value={values.minimumPrice} onChange={(event) => updateValue("minimumPrice", event.target.value)} aria-invalid={Boolean(errors.minimumPrice || errors.priceRange)} />
          </Field>
          <Field label="Maximum price" error={errors.maximumPrice}>
            <input id="maximumPrice" inputMode="decimal" min="0" step="0.01" type="number" value={values.maximumPrice} onChange={(event) => updateValue("maximumPrice", event.target.value)} aria-invalid={Boolean(errors.maximumPrice)} />
          </Field>
          <Field label="Currency" error={errors.currency}>
            <select id="currency" value={values.currency} onChange={(event) => updateValue("currency", event.target.value)} aria-invalid={Boolean(errors.currency)}>
              <option value="INR">INR · ₹</option>
              <option value="USD">USD · $</option>
              <option value="GBP">GBP · £</option>
              <option value="EUR">EUR · €</option>
            </select>
          </Field>
        </div>
      </fieldset>

      <Field label="Additional context" hint="Optional">
        <textarea id="additionalContext" rows={4} value={values.additionalContext} onChange={(event) => updateValue("additionalContext", event.target.value)} />
      </Field>

      <div className="cost-cap-notice" role="note">
        <span aria-hidden="true">◎</span>
        <p><strong>Research budget notice</strong> Each run is subject to the configured cost cap. You will review and confirm the proposed market definition before research starts.</p>
      </div>

      {submitError && <div className="form-submit-error" role="alert">{submitError}</div>}
      <div className="form-actions">
        <button className="button button-dark" disabled={isSubmitting} type="submit">{isSubmitting ? "Saving draft…" : "Continue to market definition"}<span aria-hidden="true">↗</span></button>
        <span className="form-action-note">No research starts at this step.</span>
      </div>
    </form>
  );
}

function Field({ label, hint, required, error, children }: { label: string; hint?: string; required?: boolean; error?: string; children: ReactNode }) {
  const id = (children as ReactElement<{ id?: string }>)?.props?.id;
  return (
    <div className="form-field">
      <label className="form-label" htmlFor={id}>
        {label} {required && <span aria-hidden="true">*</span>} {hint && <small>{hint}</small>}
      </label>
      {isValidElement(children) && id
        ? cloneElement(children as ReactElement<Record<string, unknown>>, {
            "aria-describedby": error ? `${id}-error` : undefined,
          })
        : children}
      {error && <span className="field-error" id={id ? `${id}-error` : undefined} role="alert">{error}</span>}
    </div>
  );
}
