# Application Architecture

**Product:** AI-Powered Multi-Agent System for Cross-Market Competitor Intelligence  
**Status:** Implementation baseline  
**Related documents:** [`PRD.md`](./PRD.md), [`DESIGN.md`](./DESIGN.md)

## 1. Decision summary

The system will use a **deterministic Python orchestrator** to control a set of specialized research agents. The orchestrator is ordinary application code, not an AI model.

Language models are used only inside bounded agent tasks such as extraction, classification, evidence support judgment and assessment drafting. The model provider is accessed through an adapter so the project can use one hosted model during development and optionally switch to a local open-weight model later.

```text
Responsive web client
        |
        v
FastAPI API server
        |
        v
Deterministic research orchestrator
        |
        +--> Market definition task
        +--> Market statistics task
        +--> Competitor research task
        +--> Customer voice task (optional)
        +--> Claim extraction task
        +--> Evidence verification task
        +--> Assessment task
        |
        v
PostgreSQL/Supabase run snapshots and report artifacts
```

## 2. Why the orchestrator is not an AI model

The product's main differentiator is traceability and repeatability. The workflow must therefore be controlled by code with explicit rules.

The orchestrator decides:

- Which stage runs next.
- Which stages can run in parallel.
- When a human confirmation is required.
- How many retries are allowed.
- Which time and cost budgets apply.
- When a result is partial or failed.
- Which artifacts are stored.
- Whether a report is eligible for publication.

These decisions must not be delegated to a language model. If an AI model controlled the workflow, the system could skip verification, exceed a budget, change its process between runs or include unsupported claims.

The model performs bounded work inside a stage. It does not control the system's state machine.

## 3. Responsibilities by layer

### Web client

The web client is responsible for:

- Authentication screens.
- Intake and market-definition editing.
- Live run progress.
- Report and evidence views.
- Run comparison.
- PDF export initiation.
- Admin views for authorized users.

The web client never calls search or language-model providers directly. Secrets and cost controls stay on the server.

### API server

The API server is responsible for:

- Authentication and ownership checks.
- Request validation.
- Run creation and retrieval.
- Market-definition confirmation.
- Starting and retrying orchestration stages.
- Streaming run events.
- Returning report and evidence data.
- Enforcing user and administrator permissions.

### Orchestrator

The orchestrator is responsible for the controlled pipeline. It should be a testable application service with no UI concerns and no provider-specific prompt logic.

### Agent tasks

An agent task is a focused module with:

- A typed input schema.
- A typed output schema.
- A narrow responsibility.
- A configured budget.
- A timeout.
- Structured errors.
- No authority to advance the global pipeline.

### Verification and policy components

Deterministic components handle rules that should not depend on model interpretation:

- Exact and fuzzy excerpt matching.
- Required numeric fields.
- Stale-data age checks.
- Conflict grouping.
- Duplicate source detection.
- Claim and evidence constraints.
- Report eligibility.

## 4. Controlled research workflow

```text
CREATE RUN
    |
    v
VALIDATE INTAKE
    |
    v
PROPOSE MARKET DEFINITION
    |
    v
WAIT FOR USER CONFIRMATION
    |
    v
FAN OUT RESEARCH TASKS
    |-----------------------------|
    v                             v
MARKET STATISTICS          COMPETITOR PRODUCTS
    |                             |
    |                         CUSTOMER VOICE
    |-----------------------------|
                  |
                  v
          NORMALIZE AND DEDUPLICATE
                  |
                  v
            EXTRACT STRUCTURED CLAIMS
                  |
                  v
             VERIFY CLAIM EVIDENCE
                  |
                  v
              BUILD ASSESSMENT
                  |
                  v
             GENERATE REPORT
                  |
                  v
             STORE IMMUTABLE SNAPSHOT
```

The customer voice task is optional and may be skipped when the feature is disabled or no permitted source is available. A skipped optional task must be visible in the run output.

## 5. Run and stage state machines

### Run states

```text
DRAFT
AWAITING_MARKET_CONFIRMATION
QUEUED
RUNNING
PARTIAL
COMPLETED
FAILED
CANCELLED
```

Allowed high-level transitions:

```text
DRAFT -> AWAITING_MARKET_CONFIRMATION
AWAITING_MARKET_CONFIRMATION -> QUEUED
QUEUED -> RUNNING
RUNNING -> PARTIAL
RUNNING -> COMPLETED
RUNNING -> FAILED
RUNNING -> CANCELLED
PARTIAL -> QUEUED       (retry or rerun)
FAILED -> QUEUED        (retry when allowed)
```

### Stage states

```text
PENDING
RUNNING
COMPLETED
PARTIAL
FAILED
RETRYING
SKIPPED
```

Every state transition should record:

- Run ID.
- Stage name.
- Previous state.
- New state.
- Timestamp.
- User or system actor.
- Error code, when applicable.
- Source or artifact counts, when available.

## 6. Specialized agent tasks

### 6.1 Market definition task

**Input:** product description, target customer, region, price range and known competitors.

**Output:** proposed category, market boundaries, exclusions, competitors, reasons and assumptions.

This task proposes a definition only. It cannot start research or bypass the user-confirmation gate.

### 6.2 Market statistics task

**Responsibilities:**

- Discover public statistics sources.
- Extract numeric figures.
- Capture value, unit, currency, year and period.
- Capture region and market definition.
- Store source metadata and an exact excerpt.
- Mark unavailable figures as insufficient evidence.

The task must preserve conflicting source-backed values instead of silently averaging them.

### 6.3 Competitor research task

**Responsibilities:**

- Verify competitor identity.
- Collect features, pricing and positioning.
- Collect recent launches where available.
- Capture source-backed excerpts.
- Mark unavailable fields.

Competitors are classified as verified, partially verified or unverified. Unverified suggestions must not be displayed as confirmed competitors.

### 6.4 Customer voice task

This is optional for the MVP. When enabled, it must return:

- Source or platform.
- Collection period.
- Sample size.
- Themes and pain points.
- Representative excerpts.
- Minimum-sample validation result.

The task must refuse to summarize a sample below the configured minimum.

### 6.5 Claim extraction task

The claim extraction task converts collected source material into structured claims.

Claim types:

- `source_reported_fact`
- `calculation`
- `inference`
- `hypothesis`

Every claim requires:

- Stable claim key.
- Claim text.
- Subject.
- Attribute.
- Period or year.
- Type.
- Source reference.
- Evidence excerpt.
- Independence group.

Recommended claim-key format:

```text
<subject>:<attribute>:<period>:<region>
```

The key must be stable enough to compare claims across two runs.

### 6.6 Evidence verification task

Verification is a two-layer process:

```text
Stored source text
        |
        v
Exact or fuzzy excerpt match
        |
        v
Source metadata and claim-field checks
        |
        v
Bounded model support judgment
        |
        v
Verification status and evidence grade
```

Statuses:

- `verified`
- `unsupported`
- `unchecked`

Evidence grades:

- `A`: primary source with a verified excerpt.
- `B`: strong published source with a verified excerpt.
- `C`: weaker or indirect source.
- `D`: unverified or inferred.

The model judgment is not allowed to override a missing excerpt or missing required numeric metadata.

### 6.7 Assessment task

The assessment task receives verified claims, evidence grades, conflicts, stale flags and data gaps. It returns:

- One rating per feasibility dimension.
- Plain-language explanation.
- Supporting claim IDs.
- Contradicting claim IDs, when applicable.
- Data gaps.
- Recommendation.
- Confidence or evidence note.

It must reject an assessment item or recommendation that has no verified claim ID.

## 7. Agent contract

Each task should follow a common contract:

```python
class AgentTask(Protocol):
    name: str

    async def run(
        self,
        context: RunContext,
        budget: AgentBudget,
    ) -> AgentResult:
        ...
```

The implementation should use Pydantic models for all task inputs and outputs. A task result should contain:

```python
class AgentResult(BaseModel):
    status: Literal["completed", "partial", "failed"]
    artifacts: list[ArtifactRef]
    warnings: list[RunWarning]
    usage: UsageSummary
    error: AgentError | None = None
```

The orchestrator handles the result. An agent cannot mutate another agent's state or advance the run directly.

## 8. Model provider abstraction

The application should use one provider interface so the orchestrator and agents are independent of the selected model.

```python
class LLMProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_content: str,
        output_model: type[BaseModel],
        budget: ModelBudget,
    ) -> BaseModel:
        ...
```

Possible implementations:

```text
HostedProvider
LocalOllamaProvider
OpenAICompatibleProvider
```

Agents should receive an `LLMProvider` through dependency injection. They should not import a specific vendor SDK directly.

### Recommended initial strategy

Start with one hosted, low-cost provider behind the adapter to validate the complete workflow. Use the same provider for the specialized roles, with separate prompts and output schemas.

Later, add a local open-weight provider through Ollama if local development, cost control or offline demonstrations justify it.

The first release does not need multiple different models. Multiple specialized agent tasks using one model provider is sufficient for a multi-agent architecture.

## 9. Model boundaries

### Model may perform

- Market-definition proposal.
- Structured source extraction.
- Competitor feature extraction.
- Customer-feedback theme classification.
- Claim extraction.
- Bounded evidence support judgment.
- Plain-language assessment drafting from verified claims.

### Model may not control

- Pipeline order.
- Stage transitions.
- User confirmation requirements.
- Retry count.
- Timeouts.
- Cost limits.
- Currency/unit/date normalization rules.
- Stale-data rules.
- Conflict-preservation rules.
- Authentication or permissions.
- Final claim eligibility.

## 10. Budgets and retries

The orchestrator enforces budgets at run and task level.

### Run budget

- Maximum runtime.
- Maximum search requests.
- Maximum model calls.
- Maximum model tokens.
- Maximum estimated cost.
- Maximum concurrent tasks.

### Task budget

- Request timeout.
- Retry limit.
- Backoff policy.
- Maximum sources.
- Maximum excerpt length.
- Maximum output records.

An agent must receive a budget object and must return usage information. The orchestrator records actual usage even when a task fails.

Retries should be bounded and should not duplicate stored claims or sources. A retry gets a new attempt identifier while the run retains the history of previous attempts.

## 11. Failure and partial-result policy

One agent failure must not destroy successful results from other agents.

Example:

```text
Market statistics       completed
Competitor research     completed
Customer voice          failed: source unavailable
Claim extraction        completed for available artifacts
Verification            completed
Assessment              partial
Report                  available with warning
```

When a stage fails, the system must:

1. Preserve successful artifacts.
2. Record the failing stage and source.
3. Explain how completeness is affected.
4. Offer a retry when the failure is retryable.
5. Mark the run as partial when the report is usable but incomplete.

The frontend should never show a partial report as an unqualified completed report.

## 12. Source and run snapshots

The system stores an immutable snapshot for every run:

```text
Run
 ├── Intake snapshot
 ├── Confirmed market definition
 ├── Source snapshots
 ├── Normalized records
 ├── Claims
 ├── Evidence records
 ├── Verification results
 ├── Assessment
 └── Report artifact
```

Source snapshots should include:

- URL.
- Publisher.
- Publication date.
- Retrieval date.
- Content hash.
- Stored text or permitted excerpt.

Run snapshots are required for reproducibility and run comparison. A rerun creates a new snapshot rather than overwriting an old result.

## 13. Orchestrator events

The API should publish structured events for the frontend through the run events endpoint.

Example event types:

```text
run.created
market_definition.proposed
market_definition.confirmed
stage.queued
stage.started
stage.progressed
stage.completed
stage.partial
stage.failed
source.failed
claim.verified
assessment.ready
report.ready
run.completed
run.partial
run.failed
```

Event payloads should include:

- Event ID.
- Run ID.
- Stage name, when applicable.
- Timestamp.
- Human-readable message.
- Machine-readable status.
- Counts or warning details.

The frontend must be able to reconnect and fetch the current run state so that a temporary WebSocket failure does not lose progress.

## 14. Frontend implications

The interface should expose orchestration without exposing private prompts or hidden reasoning.

### Dashboard

Show:

- Run status.
- Last update time.
- Completed stages.
- Partial-result warning.
- Report availability.

### Progress page

Render the stage state machine:

```text
01 Market statistics       Complete
02 Competitor research     Complete
03 Customer feedback       Partial
04 Claim extraction        Complete
05 Evidence verification   Running
06 Assessment              Pending
07 Report generation       Pending
```

### Report

Show:

- Which dimensions have sufficient verified evidence.
- Which dimensions have limited evidence.
- Which sources failed.
- Which figures are stale or conflicting.

The product should provide traceable outcomes, not transcripts of model reasoning.

## 15. Proposed backend structure

```text
backend/
  api/
    auth.py
    runs.py
    reports.py
    claims.py
    admin.py

  orchestration/
    orchestrator.py
    state_machine.py
    events.py
    budgets.py
    retry_policy.py

  agents/
    market_definition.py
    market_statistics.py
    competitors.py
    customer_voice.py
    claim_extraction.py
    assessment.py

  verification/
    excerpt_matcher.py
    claim_judge.py
    evidence_grader.py

  pipeline/
    normalize.py
    deduplicate.py
    conflict_detection.py
    snapshot.py

  providers/
    base.py
    hosted.py
    ollama.py

  schemas/
    runs.py
    sources.py
    claims.py
    evidence.py
    assessments.py
```

The initial implementation can use Python `asyncio` and FastAPI background execution. A persistent task queue can be introduced when measured concurrency requires it; it should not be added only for architectural appearance.

## 16. MVP implementation boundary

The first end-to-end implementation should include:

1. Deterministic run state machine.
2. Market-definition task.
3. Market statistics task.
4. Competitor research task.
5. Claim extraction task.
6. Deterministic excerpt matching.
7. Bounded model evidence judgment.
8. Assessment task using verified claims only.
9. Report and progress events.
10. Immutable run snapshot.

Customer Voice should be added after the evidence pipeline works because it introduces additional source, sampling and permission constraints.

## 17. Architecture acceptance criteria

The architecture is ready for implementation when:

- The orchestrator can run the stages in a fixed, testable order.
- Market definition confirmation is a required gate.
- Independent collection tasks can run in parallel.
- Every task has typed input and output models.
- Model calls go through a provider adapter.
- Provider credentials are never sent to the browser.
- The orchestrator enforces time, request and cost limits.
- Retries are bounded and recorded.
- A source failure produces a visible partial-result state.
- Claims retain stable keys across runs.
- Every claim has evidence or is rejected/flagged.
- Numeric claims require unit, year and region.
- Assessment items require verified claim IDs.
- Completed runs retain immutable source and result snapshots.
- The frontend can reconstruct current progress after reconnecting.
- A hosted provider can be replaced by a local provider without changing agent interfaces.
