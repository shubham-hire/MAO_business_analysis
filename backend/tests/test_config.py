from app.config import Settings
from app.main import create_app


def test_settings_reads_market_agent_limits_and_raw_content_profile() -> None:
    settings = Settings.from_env({
        "SOURCE_PROVIDER": "offline",
        "LLM_PROVIDER": "offline",
        "TAVILY_INCLUDE_RAW_CONTENT": "true",
        "MARKET_AGENT_MAX_ITERATIONS": "3",
        "MARKET_AGENT_MAX_QUERIES": "6",
        "MARKET_AGENT_MAX_MODEL_CALLS": "5",
        "MARKET_AGENT_MAX_SOURCES": "12",
        "MARKET_AGENT_TIMEOUT_SECONDS": "90",
    })

    assert settings.tavily_include_raw_content is True
    assert settings.market_agent_max_iterations == 3
    assert settings.market_agent_max_queries == 6
    assert settings.market_agent_max_model_calls == 5
    assert settings.market_agent_max_sources == 12
    assert settings.market_agent_timeout_seconds == 90


def test_app_wires_market_agent_limits_into_the_pipeline() -> None:
    settings = Settings(
        market_agent_max_iterations=3,
        market_agent_max_queries=6,
        market_agent_max_model_calls=5,
        market_agent_max_sources=12,
        market_agent_timeout_seconds=90,
    )

    app = create_app(settings=settings)
    budget = app.state.runner.pipeline.market_budget

    assert budget.max_iterations == 3
    assert budget.max_queries == 6
    assert budget.max_model_calls == 5
    assert budget.max_sources == 12
    assert budget.timeout_seconds == 90
