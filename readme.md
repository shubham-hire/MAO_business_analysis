
# Market Feasibility Intelligence

Evidence-first market research for founders, product managers and analysts.

The repository contains a responsive public landing page and the authenticated application foundation. The landing page is based on the supplied `stitch_tracer_market_validation_landing_page.zip` reference and is implemented as a React view. Its primary CTA opens the fixture-backed research workspace, which includes the runs dashboard, new-run intake and market-definition confirmation flow.

## Requirements

- Node.js `22.23.3` (see `frontend/.nvmrc`)
- npm 10+

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

## Checks

```bash
make test
make typecheck
make lint
make build
```

The unit tests run offline and cover dashboard state rendering, readable run statuses, partial warnings, empty state, retry behavior and loading behavior.

## Docker

```bash
docker build -t market-feasibility-frontend .
docker run --rm -p 4173:4173 market-feasibility-frontend
```

Open `http://localhost:4173`.

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
