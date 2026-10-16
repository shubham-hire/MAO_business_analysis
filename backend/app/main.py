from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.contracts import AgentBudget
from app.config import Settings, build_llm_provider, build_source_provider
from app.domain.run_service import InvalidTransition, MissingRun, RunService
from app.infrastructure.memory_repository import MemoryRunRepository
from app.orchestration.pipeline import DeterministicPipeline
from app.orchestration.runner import RunRunner
from app.providers.protocols import SourceProvider
from app.schemas import EventPage, MarketDefinitionProposal, ProductIntake, RunDetail, RunSummary


def create_app(
    repository: MemoryRunRepository | None = None,
    runner: RunRunner | None = None,
    settings: Settings | None = None,
    source_provider: SourceProvider | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Tracer Market Feasibility API",
        version="0.1.0",
        description="Deterministic run control plane for evidence-first market research.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:4173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.repository = repository or MemoryRunRepository()
    app.state.service = RunService(app.state.repository)
    app.state.settings = settings or Settings.from_env()
    configured_provider = source_provider or build_source_provider(app.state.settings)
    configured_llm = build_llm_provider(app.state.settings)
    market_budget = AgentBudget(
        max_iterations=app.state.settings.market_agent_max_iterations,
        max_queries=app.state.settings.market_agent_max_queries,
        max_model_calls=app.state.settings.market_agent_max_model_calls,
        max_sources=app.state.settings.market_agent_max_sources,
        timeout_seconds=app.state.settings.market_agent_timeout_seconds,
    )
    app.state.runner = runner or RunRunner(
        app.state.service,
        DeterministicPipeline(configured_provider, configured_llm, market_budget, market_budget),
    )

    @app.exception_handler(MissingRun)
    async def missing_run_handler(_request: Request, exc: MissingRun) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": {"code": "run_not_found", "message": f"Run {exc.args[0]} was not found.", "details": {}}})

    @app.exception_handler(InvalidTransition)
    async def invalid_transition_handler(_request: Request, exc: InvalidTransition) -> JSONResponse:
        return JSONResponse(status_code=409, content={"error": {"code": "invalid_state_transition", "message": str(exc), "details": {}}})

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs", response_model=list[RunSummary])
    async def list_runs(x_user_id: str = Header(default="demo-user")) -> list[RunSummary]:
        return await app.state.service.list_runs(x_user_id)

    @app.post("/runs", response_model=RunSummary, status_code=201)
    async def create_run(intake: ProductIntake, x_user_id: str = Header(default="demo-user")) -> RunSummary:
        return await app.state.service.create_run(intake, x_user_id)

    @app.get("/runs/{run_id}", response_model=RunDetail)
    async def get_run(run_id: str, x_user_id: str = Header(default="demo-user")) -> RunDetail:
        return await app.state.service.get_run(run_id, x_user_id)

    @app.post("/runs/{run_id}/market-definition", response_model=RunSummary, status_code=202)
    async def confirm_market_definition(
        run_id: str,
        definition: MarketDefinitionProposal,
        background_tasks: BackgroundTasks,
        x_user_id: str = Header(default="demo-user"),
    ) -> RunSummary:
        result = await app.state.service.confirm_market_definition(run_id, x_user_id, definition)
        background_tasks.add_task(app.state.runner.run, run_id, x_user_id)
        return result

    @app.get("/runs/{run_id}/events", response_model=EventPage)
    async def get_events(
        run_id: str,
        after: str | None = Query(default=None),
        x_user_id: str = Header(default="demo-user"),
    ) -> EventPage:
        events = await app.state.repository.events(run_id, x_user_id, after)
        if events is None:
            raise MissingRun(run_id)
        return EventPage(events=events)

    return app


app = create_app()
