import type { ReactNode } from "react";

type LandingPageProps = {
  onOpenApp: () => void;
};

const deliverables = [
  ["DELIVERABLE 01", "[BASELINES]", "Market size and growth", "Explicit market sizing with documented base year, regional scope and source-backed figures."],
  ["DELIVERABLE 02", "[PRICING]", "Competitors and prices", "Direct and indirect players organized side by side with sourced pricing and features."],
  ["DELIVERABLE 03", "[FRAMEWORK]", "Seven-area rating", "A structured feasibility view across demand, pricing, competition, pain, distribution and regulation."],
  ["DELIVERABLE 04", "[SAFETY]", "Honest gaps instead of guesses", "When evidence is unavailable, the system says so instead of inventing a plausible number."],
  ["DELIVERABLE 05", "[DELTA AUDIT]", "Re-run later to see what changed", "Immutable snapshots highlight changed figures, claims, sources and ratings over time."],
];

const audiences: Array<[string, string, string, string[]]> = [
  ["SEGMENT 01", "FOUNDERS", "Validate assumptions before writing code or spending capital.", ["Avoid phantom market segments", "Verify genuine price signals"]],
  ["SEGMENT 02", "ACADEMIA", "Back thesis work and venture competitions with verifiable market evidence.", ["Defensible research references", "Repeatable evaluation"]],
  ["SEGMENT 03", "PRODUCT TEAMS", "Stress-test new feature bets and adjacent market expansions with structured evidence.", ["Feature roadmap risk", "Side-by-side positioning"]],
];

export function LandingPage({ onOpenApp }: LandingPageProps) {
  return (
    <div className="landing-page">
      <aside className="landing-ticker" aria-label="System notice">
        <span><i /> SYSTEM SPEC 0.9.4 // ALPHA BUILD</span>
        <span className="ticker-detail">AUDITING LOGIC STRICT MODE: ZERO SPECULATION THRESHOLD</span>
        <span className="ticker-badge">EARLY PROJECT · IN DEVELOPMENT</span>
      </aside>

      <header className="landing-nav">
        <a className="landing-brand" href="#top" aria-label="Tracer home">TRACER <small>v0.9.dossier</small></a>
        <span className="landing-validator"><i /> PRIMARY-SOURCE VALIDATOR</span>
        <nav>
          <a href="#sample-dossier">Inspect sample</a>
          <button type="button" onClick={onOpenApp}>Open application <span aria-hidden="true">↗</span></button>
        </nav>
      </header>

      <main id="top">
        <section className="landing-hero landing-grid-lines">
          <div className="landing-container">
            <div className="landing-coordinate"><span>LAT: 20.5937° N, LON: 78.9629° E // ARCHITECTURAL FRAMEWORK</span><span>[ SECTION: 00 / CORE THESIS ]</span></div>
            <div className="landing-hero-grid">
              <div className="landing-hero-copy">
                <span className="landing-kicker">■ EARLY PROJECT · IN DEVELOPMENT</span>
                <h1>Find out if your product idea has a market, <u>with proof.</u></h1>
                <p>Describe your product. AI agents research the market, check every source, and give you a report you can verify.</p>
                <div className="landing-hero-actions"><button className="landing-button landing-button-dark" type="button" onClick={onOpenApp}>Start a research run <span>↗</span></button><span className="landing-audit-tag">◉ AUDIT v0.9 // NO SPECULATION</span></div>
                <div className="landing-principles"><span><b>NO HALLUCINATION</b>Explicit data floor enforced</span><span><b>SOURCE PARSED</b>Public evidence first</span><span><b>REPRODUCIBLE</b>Deterministic audit traces</span></div>
              </div>
              <VerificationWidget />
            </div>
          </div>
        </section>

        <LandingSection number="01" label="PROCESS ARCHITECTURE" title="How it works" description="Three sequential phases. Every operation prioritizes verifiable evidence over predictive narrative.">
          <div className="landing-process-grid">
            <ProcessCard number="01" label="INIT" title="Describe your product" text="Enter your product idea, target customer, geography and expected price tier." code={["[PARAM] domain: B2B / GovTech", "[PARAM] geography: IN / EU", "[PARAM] tier: Enterprise"]} />
            <ProcessCard number="02" label="SYNTH" title="Agents do the research" text="Specialized agents examine market statistics, competitor offerings, pricing and permitted public feedback." code={["FETCH public_sources ... OK", "PARSING competitor_pricing ... OK", "AUDITING evidence ... OK"]} />
            <ProcessCard number="03" label="AUDIT" title="Get a report with proof" text="Each finding cites a source, carries an evidence grade and stays inside the market-feasibility scope." code={["CITATIONS: Verified", "GAPS: Explicit", "EXPORT: PDF / JSON"]} />
          </div>
        </LandingSection>

        <section className="landing-section landing-section-muted">
          <div className="landing-container"><LandingSectionHeader number="02" label="DELIVERABLES SPEC" title="What you get" description="A decision-support dossier designed for evidence review, not confident fiction." />
            <div className="landing-deliverables">{deliverables.map(([label, tag, title, text], index) => <article className={`landing-deliverable ${index === 4 ? "landing-deliverable-wide" : ""}`} key={title}><div className="landing-card-meta"><b>{label}</b><span>{tag}</span></div><h3>{title}</h3><p>{text}</p><footer>TRACEABLE OUTPUT <span aria-hidden="true">↗</span></footer></article>)}</div>
          </div>
        </section>

        <LandingSection number="03" label="METHODOLOGY & INTEGRITY" title="Why it’s different" description="A fundamental departure from chat interfaces that generate speculative summaries without proof.">
          <div className="landing-pillar-grid">{[["PILLAR // 01", "Checked sources", "Every material claim leads to a source excerpt, publication date, retrieval date and evidence grade."], ["PILLAR // 02", "No made-up numbers", "When data is unavailable or conflicting, the system shows the gap instead of estimating silently."], ["PILLAR // 03", "Always comparable", "Stable claim keys and immutable run snapshots make later runs comparable." ]].map(([label, title, text]) => <article className="landing-pillar" key={title}><span>{label}</span><h3>{title}</h3><p>{text}</p><footer>// CONTROLLED RESEARCH POLICY</footer></article>)}</div>
        </LandingSection>

        <section className="landing-section landing-section-dossier" id="sample-dossier"><div className="landing-container"><LandingSectionHeader number="04" label="AUDIT DOSSIER SPECIMEN" title="Sample report preview" description="An illustrative view of the evidence-first report experience." /><div className="landing-dossier"><div className="dossier-header"><div><span className="landing-kicker">DOSSIER #TR-9042 · TARGET HYPOTHESIS</span><h3>B2B fleet telematics for regional couriers</h3></div><div className="dossier-tags"><span>GEOGRAPHY: US-MIDWEST</span><span>ACV TIER: $12K/YR</span><strong>ILLUSTRATIVE</strong></div></div><div className="dossier-metrics">{[["01. Demand urgency", "Favourable"], ["02. Willingness to pay", "Mixed"], ["03. Market size", "Favourable"], ["04. Competitor saturation", "Mixed"], ["05. Customer pain", "Favourable"], ["06. Distribution ease", "Insufficient"], ["07. Regulatory", "Mixed"]].map(([label, value]) => <div key={label}><span>{label}</span><b>{value}</b><i><em /></i></div>)}</div><div className="dossier-claim"><div className="landing-card-meta"><b>■ VERIFIED CLAIM #42-B</b><span>STATUS: VERIFIED WITH PRIMARY CITATION</span></div><blockquote>“Every material finding should lead to its source in two clicks or fewer.”</blockquote><a href="#evidence">↗ View source excerpt and evidence metadata</a></div><div className="dossier-footer"><span>HASH: 8f9b402e1c9447... SHA-256</span><span>SPECIMEN DOSSIER · ILLUSTRATIVE PREVIEW ONLY</span></div></div></div></section>

        <LandingSection number="05" label="AUDIENCE MATRICES" title="Who it’s for" description="Designed for people who need defensible evidence before committing resources.">
          <div className="landing-audience-grid">{audiences.map(([segment, title, text, bullets]) => <article key={title}><div className="landing-card-meta"><span>{segment}</span><b>{title}</b></div><h3>{title[0] + title.slice(1).toLowerCase()}</h3><p>{text}</p><ul>{bullets.map((bullet) => <li key={bullet}>■ {bullet}</li>)}</ul></article>)}</div>
        </LandingSection>

        <section className="landing-section landing-section-muted" id="faq"><div className="landing-container"><LandingSectionHeader number="06" label="VERIFICATION & LIMITATIONS" title="Frequently asked questions" description="Direct, honest answers about what the system can and cannot do." /><div className="landing-faq">{[["Does it guarantee success?", "No. It evaluates market conditions and public evidence. Execution, product quality and timing remain up to you."], ["Where does the data come from?", "Public market data, government statistics, company pages and permitted public sources. Every claim points back to its origin."], ["Does it judge whether I can build it?", "No. This product covers market feasibility only, not technical or financial feasibility." ]].map(([question, answer], index) => <details key={question} open={index === 0}><summary><span>QUERY // 0{index + 1}</span><b>{question}</b><i>+</i></summary><p>{answer}</p></details>)}</div></div></section>

        <section className="landing-cta" id="early-access"><div className="landing-cta-card"><span className="landing-kicker">■ 07 / ACCESS INVITATION</span><h2>Ready to test your idea with real data?</h2><p>Open the product workspace and define your first research mission.</p><button className="landing-button landing-button-dark" type="button" onClick={onOpenApp}>Open the research workspace <span>↗</span></button><div className="landing-cta-meta"><span>CITATIONS GUARANTEED</span><span>ZERO ESTIMATIONS</span><span>EARLY PROJECT · NOT YET RELEASED</span></div></div></section>
      </main>
      <footer className="landing-footer"><b>TRACER</b><span>SYSTEM REF // TR-ALPHA</span><span>MARKET FEASIBILITY INTELLIGENCE · 2026</span></footer>
    </div>
  );
}

function LandingSection({ number, label, title, description, children }: { number: string; label: string; title: string; description: string; children: ReactNode }) {
  return <section className="landing-section"><div className="landing-container"><LandingSectionHeader number={number} label={label} title={title} description={description} />{children}</div></section>;
}

function LandingSectionHeader({ number, label, title, description }: { number: string; label: string; title: string; description: string }) {
  return <div className="landing-section-header"><div><span>{number} / {label}</span><h2>{title}</h2></div><p>{description}</p></div>;
}

function ProcessCard({ number, label, title, text, code }: { number: string; label: string; title: string; text: string; code: string[] }) {
  return <article className="landing-process-card"><div className="landing-card-meta"><b>// {number}.{label}</b><span>STAGE {number}</span></div><h3>{title}</h3><p>{text}</p><pre>{code.join("\n")}</pre></article>;
}

function VerificationWidget() {
  return <div className="verification-widget"><header><b>■ VERIFICATION SPEC // PROTOCOL</b><span>SYSTEM READY</span></header><div className="verification-body"><div><span>Primary registry indexes</span><strong>148,920</strong></div><div><span>Registry coverage target</span><b>100% EXPLICIT</b><i><em /></i></div><div><span>Primary citation floor</span><b>100% EXPLICIT</b></div><div><span>Speculative filler logic</span><strong className="danger">DISALLOWED</strong></div><blockquote>“Findings without traceable records are flagged as non-verifiable data gaps.”</blockquote></div><footer>PARSER: V3_AUDIT_INDEX <span>STATUS: OPERATIONAL</span></footer></div>;
}
