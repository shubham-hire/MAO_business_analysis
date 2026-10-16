# Product Requirements Document

**Product:** AI-Powered Multi-Agent System for Cross-Market Competitor Intelligence (working name: Product Market-Feasibility Platform)

**Version:** 0.2 (draft) · **Date:** October 15, 2026 · **Status:** Draft for team review

**Owner:** Project team, Dept. of Computer Engineering, MVPS's Karmaveer Adv. Baburao Ganpatrao Thakare College of Engineering, Nashik

## 1. Executive Summary

**Product type:** web application (a responsive web client with a server and background research jobs). A mobile client is a later option.

### Product Vision

- **Description:** a web platform that checks a product idea against current public market evidence and returns an assessment in which every finding links to a verified source.
- **Target user and use case:** startup founders, entrepreneurs, product managers and analysts who must decide early, and with little budget, whether a product idea has a viable market.
- **Key differentiator:** four hypotheses, to be tested in the evaluation: verified-excerpt citations, numbers that carry their year, region and market definition, explicit handling of stale and conflicting figures, and run-to-run comparison.
- **Success definition:** a user can run an assessment, open the source behind any finding, and see what changed when they run it again. The primary measure is the share of material claims whose cited excerpt supports them (proposed target in section 8).

### Strategic Alignment

| Area | Statement |
| --- | --- |
| Business objectives | This is a final-year academic project. No revenue, growth or retention goal has been set, so none is claimed. The objective is a working, evaluated system built within budget. If the project is commercialised later, business goals will be added here. |
| User problems solved | Market research is scattered across sources, hard to repeat, and hard to audit. See section 2. |
| Market opportunity and timing | Not yet sized. The PRD makes no market-size claim for this tool, and sizing it is an open item. |
| Competitive advantage | Auditable and repeatable output compared with a general assistant with web search. This is an unproven hypothesis until the blind comparison in section 8 is done. |

### Resource Requirements

| Item | Current position |
| --- | --- |
| Development effort estimate | Not yet estimated. It will be estimated after Phase 0 (schemas and source-feasibility spike), when the real data constraints are known. |
| Timeline and milestones | Timeline not set. Milestones are defined in section 9 without dates. |
| Team and skills | A team of six authors. Skills needed: Python backend and asynchronous programming, React or Next.js frontend, prompt design and language-model integration, data labelling and evaluation, testing, and documentation. Role assignment is open. |
| Budget | Total target of ₹0 to ₹2,000, preferably under ₹1,000. The main costs are language-model tokens and search API calls. Hosting uses free tiers where possible. |

## 2. Problem Statement & Opportunity

### Problem Definition

Checking whether a product has a market is slow, hard to repeat and hard to audit. The main pain points are:

- Market statistics come from several publishers and use different years, regions and market definitions, so figures cannot be compared directly.
- It is often unclear which claims in a market report are backed by a source, and how old the supporting figures are.
- Competitor features, prices and customer feedback must be gathered and reconciled by hand.
- There is rarely a record of what changed since the last check, so research is repeated from scratch.

**Quantified impact:** not yet quantified. The pilot trials will measure the time a user needs to produce a feasibility brief manually and with the tool.

**Evidence for the problem:** at this stage the problem rests on the team's own observation and general practice, not on user research. Phase 1 stakeholder discussions will collect real evidence from prospective users.

### Opportunity Analysis

- **Market size and growth:** not sized, and no figure is claimed.
- **User segment:** early-stage founders, entrepreneurs and analysts who cannot easily pay for market-research reports. This is an assumption to validate.
- **Revenue and business impact:** none. The project is academic and no monetisation is planned.
- **Competitive gap:** the table compares the alternatives by category. These categories are described from general knowledge and were not benchmarked in this project.

| Alternative | Typical strength | Gap this product targets |
| --- | --- | --- |
| Manual research | Full control and flexible judgement | Slow, inconsistent, no audit trail, no comparison over time |
| Paid market-research and competitive-intelligence platforms | Curated data | Cost, and not examined in this project |
| General AI assistants with web search | Fast, readable reports | Output is hard to audit and cannot be compared across runs |
| This product | Verified citations, figures with year and region, flagged stale or conflicting data, run history | Unproven until the evaluation is done |

### Success Criteria

Targets below are proposals, to be validated after a pilot, and no result has been measured yet.

- **Primary:** share of sampled material claims whose cited excerpt supports them (proposed target: at least 90%); accuracy of numeric figures against their sources (proposed target: at least 90%); share of assessment items that cite verified claims (target: 100%, enforced by a rule).
- **Secondary:** unsupported-claim rate, share of stale or conflicting figures flagged, coverage of known important facts, cost per run, run time, and blind usefulness rating against a general assistant.
- **Expected user behaviour changes:** users open the evidence before trusting a finding, re-run the same product to see what changed, and spend less time searching by hand.
- **Anticipated outcomes:** a working, evaluated system with documented results. No commercial outcome is claimed.

## 3. User Requirements & Stories

### Primary User Personas

These personas are working assumptions and will be validated in Phase 1.

| Persona | Goals and motivation | Current workflow and pain points | Success criteria |
| --- | --- | --- | --- |
| **Early-stage founder** (primary) | Decide quickly whether a product idea is worth pursuing, and show evidence to partners or mentors | Searches many sites by hand, cannot compare figures that use different years or definitions, cannot tell which claims are sourced | Gets an assessment in one session and can open the source behind every key finding |
| **Product manager or analyst** (secondary) | Understand competitors, pricing and customer pain points before a launch | Gathers competitor features and prices manually, repeats the work each quarter | Gets a comparable structured view and sees what changed since the last run |
| **Administrator** | Keep the platform controlled and within cost | Has no view of usage or cost | Approves users and sees usage and cost per run |

### User Journey

| Stage | Current state | Proposed state | Opportunity |
| --- | --- | --- | --- |
| Define the product and market | Informal, and the market boundary is unclear | The user describes the product and confirms a proposed market definition | Statistics depend on the definition, so making it explicit prevents mismatched figures |
| Find market data | Manual search across publishers | Market Statistics Agent returns figures with unit, year, region and source | Saves search time and makes figures comparable |
| Study competitors and pricing | Manual comparison of product pages | Competitor Product Agent returns a structured comparison | Consistent fields across competitors |
| Read customer feedback | Reading reviews and forums by hand | Customer Voice Agent returns themes with sample sizes | Shows how reliable the feedback sample is |
| Judge feasibility | Intuition plus scattered notes | Seven-dimension assessment with cited evidence, grades and gaps | Makes the reasoning inspectable |
| Share and revisit | Documents go out of date | PDF export, and a later run shows changes | Turns one-off research into a repeatable process |

### Core User Stories

| Epic | Story | Acceptance criteria |
| --- | --- | --- |
| A. Intake | **US-1** As a founder, I want to describe my product and target market so that the system researches the right market. | Given a completed form, when I submit it, then the system shows a proposed market definition and competitor list with a reason for each. Given the proposal, when I edit or confirm it, then research starts only after confirmation. Required fields are product description, target customer, region and price range. |
| B. Research | **US-2** As a founder, I want market statistics with their year, region and source so that I can judge how current and comparable they are. | Each figure shows value, unit, currency, year, region, definition and source. When sources disagree, then all figures are shown as a range with their sources. A figure older than the configured age is marked stale. When no figure is found, then the report says "insufficient evidence". |
| B. Research | **US-3** As an analyst, I want a structured comparison of competing products so that I can see features and pricing side by side. | Each competitor lists features, price and source. Products the system could not verify are listed separately. |
| C. Verification | **US-4** As a founder, I want to open the source behind any finding so that I can check it myself. | When I select a finding, then I see the excerpt, source, publication date, retrieval date and evidence grade. Claims that fail verification are excluded or clearly flagged. |
| D. Assessment | **US-5** As a founder, I want a rating for each dimension of feasibility so that I can see where the product is strong or weak. | Seven dimensions are rated favourable, mixed, unfavourable or insufficient evidence. Every item and recommendation cites verified claim IDs. The report states that it covers market feasibility only. |
| D. Assessment | **US-6** As a founder, I want to export the report so that I can share it. | When I choose export, then I receive a PDF that includes ratings, citations, data gaps and unavailable sources. |
| E. History | **US-7** As an analyst, I want to compare two runs of the same product so that I can see what changed. | The comparison lists changed figures, claims and ratings, with the old and new value for each. |
| F. Accounts | **US-8** As an administrator, I want to approve users and see usage and cost so that the system stays controlled. | Pending registrations can be approved or rejected. Usage and cost per run are visible. |

### Priority and Dependencies

| Story | Priority | Depends on |
| --- | --- | --- |
| US-1 Intake | Must | Data schemas |
| US-2 Market statistics | Must | US-1, source-feasibility results |
| US-3 Competitor comparison | Must | US-1 |
| US-4 Evidence explorer | Must | US-2 and US-3 plus verification |
| US-5 Assessment | Must | US-2, US-3, US-4 |
| US-6 PDF export | Must | US-5 |
| US-7 Run comparison | Should | Run storage, US-5 |
| US-8 Admin tools | Should | Accounts |

## 4. Functional Requirements

### Core Features (Must Have)

| ID | Feature | Inputs and outputs | Business logic |
| --- | --- | --- | --- |
| F1 | Product intake and market definition | Input: product description, target customer, region, price range, optional known competitors. Output: a confirmed market definition and competitor list. | The system proposes the product category, market boundaries and competitors with a reason for each. The user confirms or edits them, and research does not start until they confirm. |
| F2 | Market statistics research | Output: numeric claims with value, unit, currency, year, region, market definition and source. | Only publicly accessible sources are used. Figures are normalised, figures older than a configurable age are flagged as stale, conflicting figures are kept and shown as a range, and a missing figure is reported as missing, never estimated silently. |
| F3 | Competitor product research | Output: for each competitor, features, pricing, positioning, recent launches and sources. | Products that cannot be verified are listed separately from verified ones. |
| F4 | Claim extraction and verification | Output: claims with verification status (verified, unsupported, unchecked), evidence grade A to D and an independence group. | Excerpts are first checked by exact or fuzzy matching against the stored source text, then a language-model judge checks that the excerpt supports the claim. Syndicated copies count once. Fetched text is untrusted and its instructions are never followed. |
| F5 | Feasibility assessment | Output: a rating of favourable, mixed, unfavourable or insufficient evidence for each of seven dimensions, with evidence, grades, gaps and recommendations. | Ratings use documented rules over verified claims only. Every item and recommendation must cite claim IDs, and items without citations are rejected. The roll-up rules are still to be written (see open question 1 in section 11). |
| F6 | Report and evidence explorer | Output: a PDF report and an on-screen explorer that opens any finding to its excerpt, source, dates and grade. | The report states that it covers market feasibility only, lists data gaps and unavailable sources, and is labelled decision support. |
| F7 | Run storage | Output: a stored snapshot of inputs, fetched sources, claims and outputs for each run. | Snapshots are immutable so that a run can be inspected and compared later. |
| F8 | Accounts and dashboard | Output: login, per-user run list and live run status. | A user can see only their own runs. |

### Secondary Features (Nice to Have)

- **Customer Voice Agent (Should):** themes and pain points from one or two permitted public sources, reported with sample size, refusing to summarise a sample below a minimum size.
- **Run comparison (Should):** shows changed figures, claims and ratings between two runs.
- **Saved product profiles (Should):** reuse the inputs of an earlier run.
- **Genericness check (Should):** rejects a recommendation that would read the same for any product.
- **Administrator tools (Should):** approve registrations, view usage and cost.
- **Market Momentum Agent (Could):** news, funding and public hiring postings, labelled as hypotheses.
- **Mobile client, optional payments, scheduled monitoring and alerts, semantic search (Could, later):** enhancements outside the first release.

### Feature Prioritization (MoSCoW)

| Priority | Features |
| --- | --- |
| **Must** | F1 to F8 |
| **Should** | Customer Voice Agent, run comparison, saved profiles, genericness check, administrator tools |
| **Could** | Market Momentum Agent, mobile client, optional payments, scheduled monitoring and alerts, semantic search |
| **Won't (this release)** | Technical or financial feasibility, forecasting, training custom machine-learning models, paywalled or login-protected sources |

### Impact and Effort

These are the team's initial judgements and should be revisited after Phase 0.

| Feature | User and business value | Effort | Note |
| --- | --- | --- | --- |
| F4 Verification | High | Medium | The main differentiator |
| F2 Market statistics | High | High | Depends on accessible statistics sources |
| F5 Assessment | High | Medium | Needs written roll-up rules |
| F3 Competitor research | High | Medium | Mostly web collection and extraction |
| Run comparison | Medium | Medium | Needs stable claim keys from the start |
| Customer Voice Agent | Medium | Medium | Limited by which sources are permitted |
| Market Momentum Agent | Low | Low to medium | Weak signal for product feasibility |
| Mobile client | Low for the MVP | High | Responsive web covers the need |

### Dependencies and Sequencing

- Data schemas, especially claim keys and numeric-claim fields, come first because every later feature uses them.
- The source-feasibility spike decides which agents are viable before they are built.
- Verification (F4) must exist before the assessment (F5), because the assessment uses only verified claims.
- Run storage (F7) must be designed from the start, even though run comparison ships later.

## 5. Technical Requirements

This is a greenfield project, so there is no existing system to integrate with. The design below is a proposal, and nothing in it is implemented yet.

### Architecture Specifications

The system is a client-server web application. A controlled research pipeline, written as ordinary program logic, runs a fixed sequence of stages and calls language models inside individual stages. The pipeline order, limits and retries are never decided by a language model.

| Component | Responsibility | Planned technology |
| --- | --- | --- |
| Web client | Registration, run configuration, status, report view, evidence explorer, export | Next.js / React, responsive |
| API server | Authentication, REST endpoints, background jobs, status updates | FastAPI (Python); Node.js with Express as an alternative |
| Research pipeline | Runs stages in order, runs agents in parallel, enforces time, request and cost limits, reports partial failures | Python with asyncio and Pydantic schemas |
| Market Statistics Agent | Collects statistics from official and published sources | Search API, data-portal APIs, BeautifulSoup |
| Competitor Product Agent | Collects competing products, features and pricing | Search API, BeautifulSoup, Playwright only for permitted pages that need rendering |
| Customer Voice Agent (Should) | Summarises public reviews and discussions | Documented public APIs |
| Verification component | Checks excerpts and support for each claim, grades evidence | String matching plus a language-model judge |
| Assessment component | Rates dimensions and drafts recommendations from verified claims | One hosted language-model API |
| Database | Users, runs, sources, claims, evidence, assessments, history | PostgreSQL through Supabase (SQLite for local development) |
| Report generator | PDF export | WeasyPrint or ReportLab |

**Data flow:**

1. The client sends the product input to the API server, which creates a run.
2. The pipeline proposes a market definition and competitor list, and the user confirms them.
3. The agents collect data in parallel, and raw source text is stored as a snapshot.
4. The pipeline normalises units, currencies, years and regions and removes duplicates.
5. Claims are extracted, verified and graded.
6. The assessment component builds ratings and recommendations from verified claims only.
7. The report is stored, the client is notified, and the run is kept as a snapshot.

### API Requirements

The endpoints below are a proposed design.

| Method and path | Purpose | Access |
| --- | --- | --- |
| POST /auth/register, POST /auth/login | Create an account and obtain a token | Public |
| POST /runs | Create a run from the product input | User |
| POST /runs/{id}/market-definition | Confirm or edit the proposed market definition and competitors | Owner |
| GET /runs/{id} | Run status and stage progress | Owner |
| WebSocket /runs/{id}/events | Live progress updates | Owner |
| GET /runs/{id}/report | Assessment with ratings, citations and gaps | Owner |
| GET /runs/{id}/claims, GET /claims/{id}/evidence | Claims and the evidence behind each one | Owner |
| GET /runs/{id}/export | PDF report | Owner |
| GET /runs/{id}/compare/{other\_id} | Differences between two runs | Owner |
| GET /admin/users, POST /admin/users/{id}/approve, GET /admin/usage | Registration approval, usage and cost | Admin |

- **Request and response format:** JSON, with Pydantic-validated schemas.
- **Authentication and authorisation:** token-based login with role checks (user and administrator), and ownership checks on every run.
- **Rate limiting:** per-user limits on run creation and API calls. The limit values will be set once costs per run are measured.
- **Error handling:** consistent error objects with a code and message. A run that partly fails returns its results with warnings that name the sources that failed.

### Data Requirements

| Entity | Key fields |
| --- | --- |
| User | Identifier, email, role, approval status |
| Run | Identifier, owner, product input, confirmed market definition, status, cost and time per stage |
| Source | Address, publisher, publication date, retrieval date, content hash, stored text |
| Claim | Identifier, claim key (subject, attribute, period), text, type (source-reported fact, calculation, inference or hypothesis), verification status, evidence grade, independence group |
| Numeric details (on a claim) | Value, unit, currency, year or period, region, market definition |
| Evidence | Claim, source, excerpt and its position, relation (supports or contradicts) |
| Assessment | Run, dimension, rating, linked claim IDs, gaps, confidence note |

**Validation and constraints:** every claim has at least one evidence record, an excerpt must appear in its stored source text, numeric claims must have unit, year and region, and a calculated figure records the inputs it came from.

**Data sources and integrations:** the table reflects an earlier documentation-level check that could not test live endpoints. Terms, prices and limits change, so confirm each before building on it.

| Source | Used for | Status | Notes |
| --- | --- | --- | --- |
| Official statistics and published industry information | Market size, growth, adoption | Not yet checked | Often annual and delayed, and detailed reports are often paywalled |
| Search APIs (for example Tavily, Exa, Serper) | Page discovery | Go, with a fallback | Free allowances are small, and sources disagree on current limits |
| Company and product pages | Features and pricing | Test per company | Check robots policy and terms for each site |
| Hacker News API | Customer discussion | Go | Free and keyless, audience skews technical |
| Reddit API | Customer discussion | Conditional | Free only for non-commercial use, with authentication and rate limits |
| App-store reviews | Customer feedback | Conditional | Only for products with apps, and Apple's feed status is unclear |
| Public job-board endpoints (Greenhouse, Lever, Ashby) | Hiring signals | Go, optional | Only employers that use them, and current openings only |
| X (Twitter) | Social discussion | No-go on budget | Paid per post |
| LinkedIn, Indeed, Glassdoor | Jobs and reviews | No-go | Terms prohibit scraping |
| Gemini free tier (LLM) | Extraction and synthesis | Conditional | Limits are unclear, and free-tier data may be used by Google, so send only public data |

**Privacy and security:** personal identifiers in public posts are not stored beyond what is needed to remove duplicates, each user's runs are isolated from other users, and the data retention period is an open item.

### Performance Specifications

The values are proposals to validate in a pilot. They are not measured results.

| Aspect | Proposed requirement |
| --- | --- |
| Run duration | A standard run finishes or returns partial results within 10 minutes. |
| Dashboard response | Dashboard and report pages load in under 3 seconds on a normal connection. |
| Throughput | Concurrent runs are queued, and the number allowed at once is set from the rate limits of the free tiers in use. |
| Availability | Best effort during development and demonstration, with no uptime guarantee. |
| Scalability | Designed for a small number of users. Growth beyond that is out of scope for the first release. |

## 6. User Experience Requirements

### Design Principles

- **Evidence first:** any finding should lead to its source in two clicks or fewer (proposed).
- **Honest uncertainty:** gaps, stale figures, conflicts and small samples are shown, not hidden.
- **Progressive disclosure:** summary first, then each dimension, then the evidence.
- **Plain language:** findings are written for non-specialists, and no false precision is shown.
- **Design system:** one established component library and a single style guide, to be chosen at the design phase.
- **Accessibility (proposed target):** WCAG 2.1 AA, keyboard navigation, labelled form fields, sufficient contrast, and ratings shown as text as well as colour.

### Interface Requirements

| Screen | Content | Key interactions |
| --- | --- | --- |
| Register and login | Account form, approval status message | Submit, recover from errors |
| Dashboard | List of runs with status | Open a run, start a new run |
| New run | Product description, target customer, region, price range, known competitors | Validation before submit, cost-cap notice |
| Market definition | Proposed category, boundaries and competitors with reasons | Edit, confirm |
| Run progress | Stage progress, agent status, warnings | Live updates, view partial results |
| Assessment report | Overall picture and seven dimension cards with rating, grade and gaps | Expand a dimension, export PDF |
| Evidence explorer | Excerpt, source, dates, grade, verification status | Filter by grade and status, open the source |
| Competitor view | Side-by-side features and pricing | Sort, open source |
| Run comparison | Changed figures, claims and ratings | Pick two runs |
| Admin console | Pending registrations, usage and cost | Approve, reject |

**Navigation and information architecture:** a top navigation with Runs, New run and Admin (administrators only), and, inside a run, tabs for Summary, Market, Competitors, Customer feedback, Evidence and History.

**Responsive design:** the interface works on phone and desktop browsers, and wide tables scroll inside their own container so the page does not scroll sideways.

**Wireframes:** to be produced in the design and prototyping phase.

### Usability Criteria

The targets are proposals for the pilot user trials.

| Criterion | Proposed target |
| --- | --- |
| Task completion | At least 90% of trial users create a run and reach the assessment without help |
| User satisfaction | System Usability Scale score of at least 68, the commonly cited average |
| Learning curve and onboarding | A sample report and short guided hints on first use |
| Error prevention | Form validation, confirmation of the market definition before research starts, and a notice of run limits |
| Error recovery | Failed sources can be retried, and partial results stay available |

## 7. Non-Functional Requirements

### Security Requirements

- **Authentication and authorisation:** token-based login, hashed passwords, role checks, and ownership checks on every run.
- **Data protection:** encrypted connections, API keys kept on the server, and input validation on every endpoint.
- **Untrusted content:** fetched web text is treated as data, kept out of instructions, and tools have limited permissions, which defends against prompt injection.
- **Compliance:** each source's terms, robots policy and rate limits are respected, and paywalls and access controls are not bypassed. Confirm the data-protection obligations that apply, for example India's Digital Personal Data Protection Act, 2023.
- **Security testing:** basic tests for authentication bypass, injection and access to other users' runs before any demonstration.

### Performance Requirements

The run and page-load targets are in section 5. In addition, database queries that serve the dashboard and evidence explorer should use indexes on run and claim identifiers, and external-service calls always carry timeouts.

### Reliability Requirements

- **Availability:** best effort for the demonstration, with no uptime guarantee.
- **Failure tolerance:** bounded retries (proposed: two), timeouts on every source, and partial results with named warnings when a source fails.
- **Backup and recovery:** use the database provider's backups, and keep stored source snapshots so a run can be replayed.
- **Monitoring:** log time, cost and errors for every stage of every run, and review the logs after each test run.

### Scalability Requirements

- **User growth:** designed for a small number of users, with growth beyond that out of scope.
- **Data growth:** stored snapshots grow with each run, so a retention policy is needed and is an open item.
- **Geographic expansion:** the first version targets one region, to be confirmed.
- **Infrastructure scaling:** limited by free-tier quotas, so these quotas are tracked as constraints.

## 8. Success Metrics & Analytics

Nothing has been measured yet. The targets are proposals to confirm after a pilot, and no result may be reported before it has been measured.

### Key Performance Indicators

**Quality metrics** (the primary success measures, evaluated on a small hand-labelled set of sample products):

| Metric | Definition | Proposed target |
| --- | --- | --- |
| Citation support | Share of sampled material claims whose excerpt supports the claim, judged by a person | At least 90% |
| Numeric accuracy | Share of figures whose value, unit, year and region match the source | At least 90% |
| Unsupported claims in the report | Share of sampled claims in final reports that fail a human audit | At most 5% |
| Citation coverage | Share of assessment items and recommendations that cite verified claims | 100%, enforced by a rule |
| Stale and conflict detection | Share of labelled stale or conflicting figures that the system flags | At least 90% |
| Coverage | Share of known important facts for a sample product that the report contains | At least 70% |
| Cost per run | Language-model and search cost for one standard run | At most ₹20, so that about 50 runs fit within a ₹1,000 budget |
| Run time | Time for a standard run | At most 10 minutes |
| Usefulness | Blind rating by several reviewers against a general assistant with web search | Not worse on specificity and correctness, and better on traceability |

**Usage metrics** (collected during the pilot, with no revenue metrics because the project is academic):

| Area | Metric |
| --- | --- |
| Activation | Share of registered pilot users who complete a first run |
| Engagement | Runs per user, and evidence-explorer opens per report |
| Retention | Share of users who re-run a product to see changes |
| Feature adoption | PDF exports and run comparisons |

### Analytics Implementation

- **Events to track:** run created, market definition confirmed, run completed, partial or failed, evidence opened, report exported and runs compared.
- **Per-stage logs:** time, cost, errors and the sources reached or missed for each run.
- **Dashboards and reports:** an admin view of usage and cost, and an evaluation sheet that records each metric for each sample product.
- **A/B testing:** not planned. The blind comparison against a general assistant replaces it.
- **Behaviour analysis:** pilot interviews and a short System Usability Scale survey.
- **Privacy:** events carry a user identifier but no product text beyond what the user chose to store.

### Success Measurement

- **Baseline:** none exists yet. The first measurement runs the labelled set through the system and through the baseline assistant.
- **Timing:** measure once when the first end-to-end prototype is ready, and again before final submission.
- **Thresholds:** each metric has a pass or fail threshold, which is its proposed target until the pilot shows it is unrealistic.
- **Review and optimisation:** after each round, group failures by stage (collection, extraction, verification or assessment) and fix the most frequent category first.

## 9. Implementation Plan

### Development Phases

The timeline is not set, so phases carry exit criteria instead of dates. The MVP is Phases 0 to 4. Phases 5 and 6 add comparison and the full evaluation.

| Phase | Scope | Exit criterion | Depends on |
| --- | --- | --- | --- |
| 0. Foundations | Data schemas, including claim keys and numeric fields, and a source-feasibility spike covering statistics sources | Each planned source is marked go, conditional or no-go with evidence | None |
| 1. Intake and statistics | Intake, market definition, Market Statistics Agent, claim extraction with excerpt check | A sample product yields figures with unit, year, region and source | Phase 0 |
| 2. Verification and competitors | Verification, evidence grading, Competitor Product Agent | Claims carry status and grade, and competitors have sourced features and prices | Phase 1 |
| 3. Customer voice | Customer Voice Agent on one or two permitted sources | Themes are reported with sample sizes | Phase 0 |
| 4. Assessment and interface | Assessment rules, PDF report, evidence explorer, dashboard, accounts | A user completes a run end to end in the interface | Phases 2 and 3 |
| 5. History | Run storage and run comparison | Two runs of a product can be compared | Phase 4 |
| 6. Evaluation | Labelled test set, baseline comparison, pilot user trials | Metrics in section 8 are measured and reported | Phases 4 and 5 |

**Rollout strategy:** an internal demonstration first, then a pilot with a small number of real users, then the final evaluation.

**Risk handling in the plan:** if a source proves inaccessible in Phase 0, it is cut from the plan instead of being faked.

### Resource Allocation

The team has six members. The roles below are needed, and assigning them is an open item.

| Role | Work |
| --- | --- |
| Backend and pipeline | API server, pipeline controller, database |
| Data collection and extraction | Agents, source connectors, normalisation |
| Verification and evaluation | Verifier, grading rules, labelled set, metrics |
| Frontend and design | Interface, evidence explorer, report layout |
| Testing and user trials | Test plans, security checks, pilot sessions |
| Documentation and infrastructure | Hosting on free tiers, deployment, project documents |

### Timeline and Milestones

| Stage | Output |
| --- | --- |
| Kickoff and discovery | Stakeholder discussions, source-feasibility results, written assessment rules |
| Design and prototyping | Wireframes for the screens in section 6 and a clickable prototype |
| Development sprints | Phases 1 to 5, each ending with a demonstration |
| Testing and quality assurance | End-to-end tests, security checks, accuracy checks on the labelled set |
| Launch and post-launch optimisation | Final demonstration, evaluation report, fixes from the failure analysis |

## 10. Risk Assessment & Mitigation

Probability and impact are the team's initial judgements (high, medium or low), not measured values, and they should be reviewed as evidence comes in.

### Technical Risks

| Risk | Probability | Impact | Prevention | Early warning and contingency |
| --- | --- | --- | --- | --- |
| Reliable, recent market statistics are scarce or paywalled for some product categories | High | High | Run the source check first and choose demo products with available data | Many "insufficient evidence" results: narrow the product categories or report the gaps openly |
| The verifier shares the language model's failure modes | Medium | High | Deterministic excerpt matching first, then a measured language-model judge | Human audit of a sample finds errors: tighten rules and re-measure |
| Free-tier limits or costs exceed the budget | High | Medium | Per-run caps, caching of fetched pages and model calls, a small model for extraction | Cost per run above target: reduce pages and queries per run |
| Prompt injection from fetched pages | Medium | High | Treat fetched text as data, keep it out of instructions, limit tool permissions | Unexpected agent behaviour in tests: block the source and add a test |
| A source changes its terms or withdraws access | Medium | Medium | Keep sources behind separate connectors and record the terms checked | Connector failures: switch to the fallback source |
| Runs take longer than the target | Medium | Medium | Run agents in parallel with timeouts | Run time above target: lower limits and return partial results |

### Business Risks

| Risk | Probability | Impact | Prevention | Early warning and contingency |
| --- | --- | --- | --- | --- |
| The product is not meaningfully better than a general assistant with web search | Medium | High | Test the differentiation hypothesis early with the blind comparison | Reviewers rate it no better: emphasise traceability and run comparison |
| Scope grows beyond the team's capacity (mobile app, payments, extra agents) | High | Medium | Keep these in the "Could" list and out of the MVP | Phase exit criteria slip: drop Should features first |
| Timeline and team availability are unclear | High | High | Confirm the timeline and roles, and plan in phases with exit criteria | Phases slip repeatedly: cut to the MVP |
| Too few pilot users | Medium | Medium | Recruit early from founders and mentors the team already knows | Few sign-ups: run observed sessions instead |
| Legal, licensing or ownership issues with sources, libraries and authorship | Low to medium | High | Respect source terms, check each library's licence and the college's IP policy | A source's terms prohibit use: remove it |

### Mitigation Strategies

- **Monitor:** review costs, quotas, source failures and the audit results after every test round.
- **Decide early:** the source spike and the first blind comparison are the two checkpoints that can change the project's direction.
- **Fallback scope:** if the schedule is at risk, keep F1 to F8 and defer the Should features.

## 11. Quality Checklist, Assumptions & Open Questions

### Quality Checklist

This is an honest status for version 0.2.

| Check | Status | Comment |
| --- | --- | --- |
| Problem is clearly defined with evidence | Partial | The problem is defined, but evidence from user research has not been collected yet |
| Solution aligns with user needs and business goals | Partial | User needs are assumptions, and no business goals have been set |
| Requirements are specific and measurable | Mostly | Targets are proposals that need pilot validation |
| Acceptance criteria are testable | Yes for the core stories | US-1 to US-8 have testable criteria, and later features still need them |
| Technical feasibility is validated | Partial | Competitor-oriented sources were checked at documentation level only, statistics sources are unchecked, and there is no prototype |
| Success metrics are defined and trackable | Yes | Definitions and events are set, and targets are proposals |
| Risks are identified with mitigation plans | Yes | Probabilities are judgements to review |
| Stakeholder alignment is confirmed | No | This draft has not been reviewed by the team or mentors |

### Definition of Done (per user story)

- The feature works in the supported browsers and on phone and desktop screens.
- Acceptance criteria for the story pass in testing.
- Security requirements in section 7 are met for the feature.
- Analytics events in section 8 are recorded.
- Performance is within the proposed targets in section 5.
- The feature has been tried by pilot users, with the task-completion target in section 6 as the goal.

### Assumptions

- The team can use free or low-cost tiers of search and language-model APIs within the budget.
- Public sources provide enough evidence for the chosen demo products.
- Users will confirm the proposed market definition and will not skip it.
- A responsive web application is enough for the first release.
- The personas in section 3 reflect real needs, which Phase 1 will test.

### Open Questions

1. What rules turn verified claims into favourable, mixed or unfavourable ratings for each dimension? They must be written and reviewed before Phase 4.
2. What is the project timeline, and who takes each role?
3. Which user group and region should the first version target?
4. Which two or three sample products will be used for the demonstration and the labelled test set?
5. Which market-statistics sources are accessible and affordable?
6. Does the institution require a mobile app or payment features?
7. Which tool will serve as the baseline in the blind comparison?
8. How long should collected source data be kept?
9. How does the college's intellectual-property policy affect ownership and authorship?

### Glossary

- **Claim:** one specific statement the system makes, stored with its evidence.
- **Evidence:** a source excerpt that supports or contradicts a claim.
- **Evidence grade:** a rule-based label from A (primary source with a verified excerpt) to D (unverified or inferred), not a probability of truth.
- **Market definition:** the category and boundaries that decide which statistics and competitors count.
- **Run:** one complete execution of the research pipeline for a product.
