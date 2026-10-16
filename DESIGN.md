# Frontend Design Document

**Product:** AI-Powered Multi-Agent System for Cross-Market Competitor Intelligence  
**Working name:** Product Market-Feasibility Platform  
**Document status:** Draft for implementation  
**Reference:** [Turion Space](https://www.turionspace.com)  
**Product requirements:** [`PRD.md`](./PRD.md)

## 1. Purpose

This document defines the frontend experience for the product market-feasibility platform. It translates the product requirements into a visual system, information architecture, screen behavior, component model and implementation sequence.

The frontend is a responsive, authenticated research application. It is not a generic AI chat interface and it is not a marketing landing page. Its core job is to help a founder or analyst understand whether a product idea has a viable market, while showing the evidence and uncertainty behind every important finding.

## 2. Product design direction

### 2.1 Design concept: evidence mission control

The product should feel like a mission-control interface for market research:

- A user defines a research mission.
- The system shows which research stages are running.
- Results are presented as structured signals rather than an opaque answer.
- Every important signal leads to a source, excerpt and verification status.
- A later run can be compared with the original snapshot.

The visual tone should be confident, precise and editorial. It should communicate that the system is useful for making a decision, while never implying certainty that the evidence does not support.

### 2.2 Turion Space reference

The Turion Space website is used as a visual reference for:

- Dark, cinematic primary surfaces.
- Large editorial headings with short, direct language.
- Minimal navigation and strong visual focus.
- Numbered section markers such as `001`, `002` and `003`.
- Generous spacing between major sections.
- Large statistics and status values.
- Modular cards and horizontal content groups.
- High contrast between headings, metadata and body content.

The product must not copy Turion Space's logo, brand, text, images, layout, animations or proprietary assets. The reference is limited to visual qualities and information hierarchy. Research tables, evidence excerpts and forms should remain more functional and readable than a public-facing brand site.

### 2.3 What the interface must communicate

The interface should make these statements obvious:

1. This is a market-feasibility assessment, not a prediction or guarantee.
2. Findings are backed by sources, excerpts and verification states.
3. Figures may differ because their years, regions or market definitions differ.
4. Missing, stale, conflicting and failed evidence is intentionally visible.
5. The current report is a snapshot that can be revisited and compared.

## 3. Design principles

### Evidence first

Any material finding should lead to its supporting evidence in two interactions or fewer. Claims, recommendations and assessment dimensions must expose claim identifiers or an obvious evidence action.

### Honest uncertainty

Use explicit states for:

- Insufficient evidence.
- Stale figures.
- Conflicting figures.
- Unsupported or unchecked claims.
- Failed sources.
- Partial research results.
- Small customer-feedback samples.

Never replace a missing figure with an unlabelled estimate.

### Progressive disclosure

The report should follow this sequence:

1. Overall picture.
2. Assessment dimension.
3. Finding or claim.
4. Evidence excerpt and source metadata.

Dense source metadata should be available without overwhelming the first view.

### Plain language

Use language that a founder or product manager can understand without specialist research training. Prefer “Two sources report different market sizes” over “conflicting estimates detected.” Technical terms may appear in metadata, but the main explanation should remain plain.

### Accessible status communication

Ratings and verification states must use text, icons and colour together. The target is WCAG 2.1 AA, including keyboard navigation, labelled form fields, visible focus states and sufficient contrast.

### Responsive by default

The product must work on phone and desktop browsers. Wide data tables may scroll inside their own containers, but the page itself must not create accidental horizontal scrolling.

## 4. Primary users and jobs

### Early-stage founder

Needs to decide whether an idea is worth pursuing and share evidence with partners or mentors.

Primary job: create a run, understand the assessment and inspect the evidence behind key findings.

### Product manager or analyst

Needs a structured competitor view and repeatable research over time.

Primary job: compare competitors, revisit a product and identify changed figures, claims and ratings.

### Administrator

Needs to control access and understand usage and cost.

Primary job: approve users and monitor runs, failures and cost.

## 5. Information architecture

### 5.1 Global navigation

Desktop navigation:

```text
Product logo | Runs | New run | Admin* | Account
```

`Admin` is visible only to users with the administrator role.

The account menu contains:

- User email or display name.
- Account status.
- Sign out.

On mobile, the navigation becomes a menu drawer. The current page and current run status remain visible in the header.

### 5.2 Run navigation

Inside a run, use the following tabs:

```text
Summary | Market | Competitors | Customer feedback | Evidence | History
```

The selected tab must be visually clear and keyboard accessible. On narrow screens, tabs may horizontally scroll within the tab bar or become a labelled select control.

### 5.3 Routes

Recommended route structure:

```text
/login
/register
/runs
/runs/new
/runs/:runId/market-definition
/runs/:runId/progress
/runs/:runId/summary
/runs/:runId/market
/runs/:runId/competitors
/runs/:runId/customer-feedback
/runs/:runId/evidence
/runs/:runId/history
/admin/users
/admin/usage
```

## 6. Visual design system

### 6.1 Colour tokens

The exact values should be tested for contrast during implementation. These names are the stable design tokens:

| Token | Purpose | Direction |
| --- | --- | --- |
| `ink-950` | Main dark shell and report hero | Deep black/navy |
| `ink-900` | Dark panels and navigation | Near-black navy |
| `ink-700` | Primary dark text on light surfaces | Charcoal |
| `ink-500` | Secondary metadata | Muted grey |
| `paper-50` | Main application background | Warm off-white |
| `paper-0` | Cards and elevated content | White |
| `accent-500` | Primary links and actions | Electric blue |
| `success-600` | Verified and favourable states | Green |
| `warning-600` | Stale, mixed and conflicting states | Amber |
| `danger-600` | Failed, unfavourable and unsupported states | Red |
| `info-600` | Informational process state | Cyan or violet |

Dark surfaces should use light text with adequate contrast. Coloured status badges should use both a readable label and an icon or shape cue.

### 6.2 Typography

Use one strong display sans-serif and one highly readable interface sans-serif, or a single variable sans-serif with distinct display and text styles.

| Style | Desktop | Mobile | Use |
| --- | ---: | ---: | --- |
| Display | 56–72px | 36–44px | Report and page hero headings |
| H2 | 32–44px | 28–34px | Major content sections |
| H3 | 22–30px | 20–24px | Cards and dimensions |
| Body | 15–17px | 15–16px | Explanations and findings |
| Metadata | 11–13px | 11–12px | Dates, labels and source details |
| Metric | 48–80px | 36–56px | Counts and summary values |

Section markers use uppercase text, small size and increased letter spacing:

```text
003 / ASSESSMENT
```

### 6.3 Shape, borders and spacing

- Use moderate corner radii, not highly rounded consumer-app styling.
- Prefer thin borders and restrained shadows.
- Use large vertical spacing between major sections.
- Keep table rows compact but not cramped.
- Use a consistent spacing scale based on 4px or 8px increments.
- Keep content width constrained for reading, while allowing evidence tables to use the available width.

### 6.4 Imagery and motion

The authenticated product does not require decorative hero imagery. If imagery is used, it should explain a product category or support a report, not distract from the evidence.

Motion should be functional:

- Progress transitions when a stage changes.
- Drawer transitions for evidence details.
- Subtle expand/collapse for assessment dimensions.

Do not hide content behind scroll-triggered animations. Respect `prefers-reduced-motion`.

## 7. Screen specifications

### 7.1 Login

#### Purpose

Provide a focused entry point for approved users.

#### Layout

Use a dark split layout on desktop:

- Left: product statement and a small section marker, for example `001 / ACCESS`.
- Right: login form on a light or dark card with clear labels.

Fields:

- Email.
- Password.

Actions:

- Sign in.
- Create an account.
- Recover password, if supported by the backend.

States:

- Invalid credentials.
- Network error.
- Account awaiting approval.
- Account rejected.
- Submitting.

### 7.2 Registration

Fields:

- Name.
- Email.
- Password.
- Confirm password.

After registration, show a dedicated approval message rather than implying immediate access:

> Your account is awaiting administrator approval.

The message should explain what the user can do next and provide a sign-in link.

### 7.3 Runs dashboard

#### Purpose

Show the user's research history and make starting a new run the dominant action.

#### Header

```text
YOUR RESEARCH RUNS
Review what changed across your market research.
[START NEW RUN]
```

Use a dark header section with a large editorial heading and a compact summary strip.

Suggested summary metrics:

- Active runs.
- Completed runs.
- Verified claims.
- Last run date.

#### Run list

Each run row or card includes:

- Product name.
- Region.
- Confirmed market definition.
- Created and updated date.
- Status.
- Evidence count.
- Report availability.
- Open action.

Use numbered rows where appropriate:

```text
001  Sustainable packaging subscription
     India · Completed · 42 verified claims
```

Statuses:

- Draft.
- Awaiting market confirmation.
- Researching.
- Partial results.
- Completed.
- Failed.

#### Empty state

The first-run empty state includes:

1. A short explanation of the product.
2. A three-step workflow: define, confirm, review.
3. A sample report preview or evidence illustration.
4. A `START YOUR FIRST RUN` action.

### 7.4 New run intake

#### Purpose

Collect the required fields for US-1 and prevent underspecified research.

Required fields:

- Product description.
- Target customer.
- Region.
- Price range.

Optional fields:

- Product name.
- Known competitors.
- Additional context.

Recommended layout:

```text
001 / DEFINE THE PRODUCT

What are you researching?
[Large product description field]

Who is it for?
[Target customer]

Where will it compete?
[Region]

What price range?
[Minimum] [Maximum] [Currency]
```

Behavior:

- Validate fields before submission.
- Show inline errors next to the relevant field.
- Preserve entered values after validation errors.
- Explain how the information affects the market definition.
- Display a run-limit or cost-cap notice before submission.
- Do not start research until the proposed market definition is confirmed.

### 7.5 Market definition confirmation

#### Purpose

Make the research boundary explicit and editable before the system collects evidence.

Header:

```text
002 / CONFIRM THE MARKET
```

Content:

- Proposed product category.
- Included market boundaries.
- Excluded market boundaries.
- Region.
- Target customer.
- Price range.
- Proposed competitors.

Each proposed competitor includes:

- Name.
- Reason for inclusion.
- Edit action.
- Remove action.

Actions:

- `CONFIRM AND START RESEARCH`.
- `EDIT DEFINITION`.

Use a high-visibility warning:

> Statistics and competitor results depend on this market definition. Confirming it starts the research pipeline.

### 7.6 Live research progress

#### Purpose

Make the research pipeline transparent and useful when a source fails or only partial results are available.

Pipeline stages:

```text
01  Market statistics
02  Competitor research
03  Customer feedback
04  Claim extraction
05  Evidence verification
06  Feasibility assessment
07  Report generation
```

Each stage shows:

- Status.
- Start or completion time.
- Source count, when available.
- Warning or failure reason.
- Retry action, if supported.

Use these status labels:

- Queued.
- Running.
- Complete.
- Partial.
- Failed.
- Retrying.

Do not display a made-up percentage. If the backend cannot calculate meaningful progress, show stage progress and a truthful status message instead.

Partial-result message example:

> Two sources could not be reached. Results from the remaining sources are available.

### 7.7 Assessment report summary

#### Purpose

Give the user a useful summary without hiding the supporting evidence.

Report header:

- Product name.
- Confirmed market definition.
- Region.
- Run date.
- `MARKET FEASIBILITY ONLY` label.
- Export PDF action.
- Compare run action.

Hero treatment:

```text
003 / ASSESSMENT

Evidence points to a mixed feasibility picture.
```

The statement must be generated from the assessment result and must not overstate certainty.

Summary indicators:

- Verified claim count.
- Source count.
- Data gaps.
- Stale figures.
- Conflicting figures.
- Failed sources.

Do not use a single unexplained score. The PRD defines seven dimension ratings, so the primary report structure should be those dimensions.

### 7.8 Feasibility dimension cards

Each of the seven dimensions is shown as a reusable card containing:

- Dimension name.
- Rating: favourable, mixed, unfavourable or insufficient evidence.
- Plain-language explanation.
- Evidence grade or grade range.
- Supporting claim count.
- Data-gap indicator.
- `VIEW EVIDENCE` action.

The card must visually distinguish:

- Strong evidence.
- Mixed evidence.
- Stale evidence.
- Missing evidence.

### 7.9 Assessment dimension detail

The expanded dimension view contains:

- Dimension title and rating.
- Assessment explanation.
- Assessment rule or confidence note, when available.
- Supporting claims.
- Contradicting claims.
- Data gaps.
- Recommendation.
- Evidence links.

Recommendations must link to verified claim IDs. Claims that fail verification must be excluded or clearly flagged.

### 7.10 Market statistics

Market figures are structured records, not only narrative text.

Required visible fields:

- Value.
- Unit.
- Currency.
- Year or period.
- Region.
- Market definition.
- Publisher.
- Source link.
- Evidence grade.
- Stale status.

#### Conflicting figures

Show every source-backed value and explain the conflict:

```text
CONFLICTING FIGURES

Source A: ₹X · 2025
Source B: ₹Z · 2025

These sources report different values or definitions. Review both before using the range.
```

#### Missing figures

Use:

> Insufficient evidence found for this metric.

Never display an estimated number as if it were source-backed.

### 7.11 Competitor comparison

#### Desktop

Use a horizontally scrollable table with columns for:

- Competitor.
- Positioning.
- Key features.
- Price.
- Recent launches.
- Verification status.
- Sources.

#### Mobile

Convert each competitor into a stacked card. Do not compress a full desktop table until its content is unreadable.

Separate:

- Verified competitors.
- Partially verified competitors.
- Suggested but unverified competitors.

Every feature and price needs a source indicator or an explicit unavailable state.

### 7.12 Customer feedback

If the Customer Voice Agent is included, show:

- Source or platform.
- Collection period.
- Sample size.
- Positive themes.
- Pain points.
- Representative evidence.
- Reliability warning for small samples.

When the sample is below the configured minimum, use:

> Customer feedback could not be reported because the available sample was below the minimum threshold.

### 7.13 Evidence explorer

#### Purpose

Make evidence the central differentiator of the product.

Desktop layout:

```text
┌──────────────────────┬──────────────────────────────────────┐
│ Filters and claims   │ Selected claim and evidence detail   │
└──────────────────────┴──────────────────────────────────────┘
```

Each claim item shows:

- Claim text.
- Claim type: source-reported fact, calculation, inference or hypothesis.
- Verification status.
- Evidence grade A–D.
- Source publisher.
- Publication date.
- Stale or conflict warning.

Filters:

- Verification status.
- Evidence grade.
- Claim type.
- Source.
- Supports or contradicts.
- Stale figures.
- Conflicting figures.

Evidence detail shows:

- Full claim.
- Exact excerpt.
- Highlighted matching passage, when available.
- Source title.
- Publisher.
- Publication date.
- Retrieval date.
- Evidence grade.
- Verification explanation.
- `OPEN SOURCE` action.
- Related assessment dimensions.
- Related claims.

On mobile, the detail panel becomes a full-screen detail route or bottom sheet. The back action must return to the same list and filter state.

### 7.14 Run comparison

#### Purpose

Show how a product's research changed between two immutable snapshots.

Controls:

- Run A selector.
- Run B selector.
- Date and market-definition labels.

Change categories:

- Changed market figures.
- Added claims.
- Removed claims.
- Changed verification status.
- Changed evidence grades.
- Changed assessment ratings.
- New data gaps.
- Newly stale sources.

Use explicit change labels:

- Added.
- Removed.
- Improved.
- Declined.
- Unchanged.
- Newly conflicting.

Each changed item shows the old value, new value, reason if available and evidence links.

### 7.15 Admin console

The administrator-only area contains:

#### User approval

- Pending users.
- Approved users.
- Rejected users.
- Approve and reject actions.

#### Usage and cost

- Runs by user.
- Cost per run.
- Runtime per stage.
- Failed source count.
- Search/model usage.
- Quota warnings.

The admin interface can be delivered after the core report experience, but role checks and route structure should exist from the beginning.

## 8. Interaction specifications

### 8.1 Form behavior

- Use visible labels, not placeholder-only labels.
- Validate required fields before submission.
- Show errors beside the relevant field.
- Keep entered values after an error.
- Describe the expected input with examples.
- Disable duplicate submissions while a request is pending.
- Preserve a clear recovery path after API failures.

### 8.2 Evidence behavior

- Clicking a finding opens its evidence detail.
- Evidence detail includes the exact excerpt, not only a source title.
- The source opens in a new tab with an accessible label.
- The user can return to the same report section and filters.
- Unsupported claims are never presented as verified.

### 8.3 Partial failure behavior

When a source or agent fails:

1. Keep successful results available.
2. Name the failed source or stage.
3. Explain whether the failure affects completeness.
4. Offer retry when supported.
5. Mark the report as partial rather than completed without qualification.

### 8.4 Loading behavior

Use skeletons for stable layouts such as cards and tables. Use explicit progress stages for research jobs. Avoid an indefinite spinner without a message or recovery option.

### 8.5 Empty states

Every data view should define an empty state for:

- No runs.
- No market figures.
- No verified claims.
- No competitors.
- No customer feedback.
- No comparison changes.
- No admin users awaiting approval.

Empty states should explain why the view is empty and what action, if any, can resolve it.

## 9. Component architecture

The frontend should be built from typed, reusable components rather than page-specific markup.

```text
components/
  layout/
    AppShell
    TopNav
    MobileNav
    RunContextHeader
    AccountMenu

  feedback/
    AlertBanner
    ErrorState
    EmptyState
    LoadingSkeleton
    Toast

  forms/
    FormField
    ProductIntakeForm
    MarketDefinitionForm
    CompetitorEditor
    ValidationMessage

  runs/
    RunCard
    RunStatusBadge
    RunFilters
    ProgressTimeline
    ResearchStage

  report/
    ReportHeader
    SummaryMetrics
    AssessmentGrid
    AssessmentCard
    AssessmentDetail
    RatingBadge
    DataGapNotice

  evidence/
    EvidenceExplorer
    EvidenceFilters
    EvidenceList
    EvidenceListItem
    EvidenceDetailDrawer
    SourceMetadata
    ExcerptViewer

  market/
    MarketStatCard
    MarketStatsTable
    ConflictNotice
    MissingEvidenceNotice

  competitors/
    CompetitorTable
    CompetitorCard
    VerificationStatus
    SourceLink

  comparison/
    RunSelector
    ChangeSummary
    ChangeTable
    ChangeBadge

  admin/
    UserApprovalTable
    UsageTable
    CostSummary
```

All report components should receive typed API models. Hardcoded demo content belongs only in fixtures or story/demo data.

## 10. Data and API boundaries

The frontend should consume the API shapes proposed in the PRD:

| Frontend need | API boundary |
| --- | --- |
| Authentication | `POST /auth/register`, `POST /auth/login` |
| Create run | `POST /runs` |
| Confirm market | `POST /runs/{id}/market-definition` |
| Run status | `GET /runs/{id}` |
| Live progress | `WebSocket /runs/{id}/events` |
| Report | `GET /runs/{id}/report` |
| Claims | `GET /runs/{id}/claims` |
| Evidence detail | `GET /claims/{id}/evidence` |
| PDF export | `GET /runs/{id}/export` |
| Comparison | `GET /runs/{id}/compare/{other_id}` |
| Admin users | `GET /admin/users` and approval endpoints |
| Admin usage | `GET /admin/usage` |

Frontend error handling should consume the API's consistent error object containing a code and message. The UI should display a helpful message while retaining a technical code for support or logs.

## 11. Responsive behavior

### Desktop

- Persistent top navigation.
- Two-column evidence explorer.
- Wide assessment grid.
- Scroll-contained comparison tables.
- Summary metrics displayed as a horizontal strip.

### Tablet

- Reduced navigation spacing.
- Assessment cards may use two columns.
- Evidence explorer may reduce the detail pane width.
- Tables remain horizontally scrollable within their containers.

### Mobile

- Collapsible navigation drawer.
- Single-column report layout.
- Summary metrics become a two-column grid or vertical list.
- Assessment cards become stacked sections.
- Evidence detail becomes a full-screen view.
- Competitor rows become cards.
- Run comparison uses stacked old/new values.
- Long tab lists scroll within the tab bar.

Never allow the main document to scroll horizontally because of a table or chart.

## 12. Accessibility requirements

The implementation target is WCAG 2.1 AA.

- Every form control has a visible or programmatically associated label.
- Keyboard users can reach every action in logical order.
- Focus states are visible against both light and dark surfaces.
- Dialogs and evidence drawers trap focus appropriately and close predictably.
- Status uses text in addition to colour.
- Tables have useful captions or accessible names.
- Source links identify that they open an external page.
- Heading hierarchy follows the page structure.
- Errors are announced or associated with the relevant input.
- Motion is reduced when the user requests reduced motion.
- Contrast is checked for body text, metadata, borders and status badges.

## 13. Stitch workflow

### 13.1 Initial Stitch project prompt

```text
Design a responsive authenticated web application called “Market Feasibility Intelligence”.

Use https://www.turionspace.com only as a visual reference for cinematic dark surfaces, oversized editorial typography, strong numbered sections, minimal navigation, generous spacing, bold statistics and modular content blocks. Do not copy Turion Space branding, logo, content, imagery or layout.

This product helps startup founders and analysts evaluate a product idea against public market evidence. Every important finding must connect to a verified source. The interface must clearly show stale figures, conflicting sources, missing evidence, partial research failures and evidence grades.

Create screens for login, registration, runs dashboard, new-run intake, market-definition confirmation, live research progress, assessment summary, market statistics, competitor comparison, evidence explorer, run comparison and an administrator console.

The interface should feel like evidence mission control, not a generic AI chat application and not a marketing landing page. Use deep black/navy for primary surfaces, warm off-white for dense content, white bordered cards, electric blue actions and explicit text labels for favourable, mixed, unfavourable, insufficient evidence, stale and conflicting states.

Prioritize evidence visibility, source traceability, progressive disclosure, plain language, keyboard accessibility, responsive tables, partial results and error recovery.
```

### 13.2 Generation order

Generate and approve these screens in order:

1. Dashboard.
2. Assessment report.
3. Evidence explorer.
4. New run intake.
5. Market definition.
6. Research progress.
7. Market statistics.
8. Competitor comparison.
9. Run comparison.
10. Login, registration and admin console.

The first three screens establish the visual system. Do not generate every screen independently before approving shared typography, spacing, colours and status patterns.

### 13.3 Responsive Stitch pass

After the desktop views are approved, generate responsive variants at approximately:

- 1440px desktop.
- 1024px tablet.
- 390px mobile.

Ask Stitch specifically to preserve evidence access, labels and table usability rather than simply shrinking the desktop layout.

## 14. Frontend delivery sequence

### Phase 1: Design foundation

- Confirm Stitch direction.
- Define colour, typography and spacing tokens.
- Select one component library.
- Build the app shell and responsive navigation.
- Build status badges, buttons, cards and feedback states.

### Phase 2: Intake workflow

- Build dashboard.
- Build new-run form.
- Add validation and cost-cap notice.
- Build market-definition confirmation.
- Connect run creation and confirmation endpoints.

### Phase 3: Research process

- Build live progress timeline.
- Connect WebSocket events.
- Add partial result and failure states.
- Add retry actions where supported.

### Phase 4: Report experience

- Build report header and summary metrics.
- Build seven assessment cards.
- Build dimension detail.
- Build market statistics.
- Build competitor comparison.

### Phase 5: Evidence and history

- Build evidence explorer and filters.
- Build evidence detail drawer.
- Build source excerpt viewer.
- Build PDF export action.
- Build run comparison.

### Phase 6: Access and quality

- Build login and registration.
- Build account approval states.
- Build admin console.
- Run accessibility, responsive, performance and end-to-end checks.

## 15. Acceptance criteria

The frontend design is complete when:

- A user can create a run from the dashboard.
- Required intake fields are validated.
- The proposed market definition is visible, editable and confirmed before research starts.
- Run progress shows stages and named warnings.
- Partial results remain available after a source failure.
- The report clearly states that it covers market feasibility only.
- Seven feasibility dimensions show text ratings and evidence context.
- Every assessment item and recommendation links to verified claim IDs.
- A finding leads to its evidence in two interactions or fewer.
- Evidence detail shows excerpt, source, publication date, retrieval date and grade.
- Stale, conflicting, unsupported and insufficient-evidence states are visible.
- Market figures show value, unit, currency, year, region and market definition.
- Competitor features and prices show their sources or unavailable state.
- Two runs can be compared using changed figures, claims and ratings.
- PDF export is available from the report.
- The layout works on phone and desktop without page-level horizontal scrolling.
- Admin-only screens are protected by role and permission checks.
- Keyboard navigation and text-based status communication meet the accessibility target.

## 16. Open design decisions

These decisions should be resolved before implementation is considered final:

1. Product name and final logo treatment.
2. Exact font choices and licensing.
3. Component library selection.
4. Exact rating rules for the seven dimensions.
5. Whether the overall report uses a roll-up label or only dimension ratings.
6. Minimum customer-feedback sample size.
7. Supported region and currency for the first release.
8. Whether evidence detail is a drawer, route or both.
9. PDF export loading and failure behavior.
10. Final mobile navigation pattern.

## 17. Orchestration and AI boundary

The frontend represents a deterministic research workflow. The orchestrator is application code, not an AI model. It controls stage order, human confirmation, parallel work, timeouts, retries, budgets and partial-result states.

Language models operate only inside bounded agent tasks such as market-definition proposal, structured extraction, claim extraction, evidence support judgment and assessment drafting. The frontend must never imply that an autonomous model controls the entire research process.

The UI should expose the controlled stages:

```text
Market definition
→ Research agents
→ Normalization
→ Claim extraction
→ Evidence verification
→ Assessment
→ Report
```

Progress events should be rendered as explicit stage states such as `Queued`, `Running`, `Complete`, `Partial`, `Failed` and `Retrying`. A partial report must show which agent or source failed and how that affects completeness.

The selected model provider is an implementation detail behind a backend adapter. The browser must not call a model provider directly or receive provider credentials. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for agent contracts, provider abstraction, budgets and orchestration rules.
