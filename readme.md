
# Market Feasibility Intelligence

Evidence-first market research for founders, product managers and analysts.

The repository contains a responsive public landing page and the authenticated application foundation. The landing page is based on the supplied `stitch_tracer_market_validation_landing_page.zip` reference and is implemented as a React view. Its primary CTA opens the fixture-backed research workspace, which includes the runs dashboard, new-run intake and market-definition confirmation flow.

## Requirements

- Node.js `22.23.3` (see `frontend/.nvmrc`)
- npm 10+
- Python `3.11.2` (see `.python-version`)

## Setup

```bash
make install
```

## Run locally

```bash
make dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

The dashboard currently uses local fixtures through an API adapter. It includes loaded, partial-result, empty, loading and request-error states so the frontend can be developed before the API is available.

The public landing page is the default view at `/`. Choose **Open application** or **Start a research run** to enter the workspace. The product shell brand link returns to the landing page.

## Backend setup

The backend is a FastAPI run-control plane. It owns intake validation, deterministic market-definition proposals, ownership-scoped run retrieval, confirmation state transitions, structured run events and evidence artifacts. It remains offline by default. An optional Tavily source provider can collect live search results when explicitly enabled.

```bash
make backend-install
cp backend/.env.example backend/.env
make backend-dev
```

The API runs at `http://localhost:8000`. Useful endpoints:

```text
GET  /healthz
GET  /runs
POST /runs
GET  /runs/{id}
POST /runs/{id}/market-definition
GET  /runs/{id}/events
```

The default development identity is `demo-user`. A real authentication layer will replace the development `X-User-ID` header before multi-user use.

Keep `SOURCE_PROVIDER=offline` for deterministic local development. To enable Tavily, set these values in `backend/.env`:

```env
SOURCE_PROVIDER=tavily
TAVILY_API_KEY=your-server-side-key
TAVILY_SEARCH_DEPTH=advanced
TAVILY_MAX_RESULTS=5
TAVILY_MAX_QUERIES_PER_STAGE=2
TAVILY_INCLUDE_RAW_CONTENT=true
MARKET_AGENT_MAX_ITERATIONS=2
MARKET_AGENT_MAX_QUERIES=4
MARKET_AGENT_MAX_MODEL_CALLS=4
MARKET_AGENT_MAX_SOURCES=10
MARKET_AGENT_TIMEOUT_SECONDS=120
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=your-server-side-key
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

The Tavily and NVIDIA keys are server-side only and must never be placed in `frontend/.env`. The market and competitor agents run concurrently, use NVIDIA for bounded planning and coverage review, use Tavily for raw source snapshots, and leave deterministic Python as the final evidence verifier. Each agent is limited to two research rounds, four queries, four model attempts, ten retained sources and 120 seconds. Competitor observations distinguish user-listed competitors from discovered alternatives and keep unpublished pricing as unknown. When NVIDIA is unavailable, the pipeline falls back to deterministic query and claim extraction. A provider failure produces a partial run with a warning; it does not fabricate evidence. The current assessment and report stages are still intentionally unavailable, so research runs remain partial until those stages are implemented.

To point the frontend at the backend instead of local fixtures:

```bash
cp frontend/.env.example frontend/.env
```

Then run the frontend and backend together. When `VITE_API_BASE_URL` is present, the dashboard and new-run flow use the FastAPI endpoints. Without it, the frontend stays fixture-backed for offline UI development.

## Checks

```bash
make test
make typecheck
make lint
make build
```

The test command runs both frontend and backend suites offline. Frontend tests cover dashboard state rendering, readable run statuses, partial warnings, empty state, retry behavior, loading behavior and competitor observations. Backend tests cover intake validation, run creation, ownership isolation, market confirmation, state transitions, event replay, adaptive market and competitor agents, concurrent failure isolation, the honest no-provider pipeline and mocked Tavily/NVIDIA provider behavior. No normal test calls the network.

## Docker

```bash
docker build -t market-feasibility-frontend .
docker run --rm -p 4173:4173 market-feasibility-frontend
```

Open `http://localhost:4173`.

To run the frontend and backend together:

```bash
docker compose up --build
```

Open `http://localhost:4173`; the frontend is built with the backend API at `http://localhost:8000`.

## Frontend structure

```text
frontend/
  src/
    app/                 Application composition
    components/          Shared layout, feedback and run components
    features/landing/    Public landing page and scoped visual system
    features/runs/       Run models, fixtures, API adapter and dashboard
    styles/              Design tokens and global styles
    test/                Test setup
  package.json
  package-lock.json
  .nvmrc
```

The fixture API is deliberately replaceable. When the backend implements `GET /runs`, replace `fixtureRunsApi` with a fetch-backed adapter without changing the dashboard components.
