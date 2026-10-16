from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.run_service import RunService
from app.infrastructure.memory_repository import MemoryRunRepository
from app.main import create_app
from app.orchestration.runner import RunRunner
from app.schemas import MarketDefinitionProposal, ProductIntake


INTAKE = {
    "productName": "Local delivery marketplace",
    "productDescription": "A delivery marketplace for independent local stores.",
    "targetCustomer": "Independent retailers",
    "region": "India",
    "priceRange": {"minimum": 100, "maximum": 500, "currency": "INR"},
    "competitors": ["Store A"],
}


class NoopRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def run(self, run_id: str, owner_id: str) -> None:
        self.calls.append((run_id, owner_id))


def test_create_and_confirm_lifecycle() -> None:
    repository = MemoryRunRepository()
    runner = NoopRunner()
    client = TestClient(create_app(repository=repository, runner=runner))

    response = client.post("/runs", json=INTAKE)
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "awaiting_market_confirmation"
    assert created["proposedMarketDefinition"]["competitors"] == ["Store A"]
    run_id = created["id"]

    response = client.post(
        f"/runs/{run_id}/market-definition",
        json={
            "category": "Local delivery market",
            "includedBoundaries": "Independent retailers in India",
            "excludedBoundaries": "Enterprise-only offerings",
            "competitors": ["Store A", "Store B"],
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert runner.calls == [(run_id, "demo-user")]

    detail = client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["confirmedMarketDefinition"]["category"] == "Local delivery market"
    assert detail.json()["stages"][-2]["state"] == "pending"


def test_invalid_intake_is_rejected() -> None:
    client = TestClient(create_app())
    invalid = {**INTAKE, "priceRange": {"minimum": 900, "maximum": 100, "currency": "INR"}}
    response = client.post("/runs", json=invalid)
    assert response.status_code == 422


def test_owner_cannot_read_another_users_run() -> None:
    client = TestClient(create_app())
    response = client.post("/runs", json=INTAKE, headers={"X-User-ID": "owner-a"})
    run_id = response.json()["id"]
    forbidden = client.get(f"/runs/{run_id}", headers={"X-User-ID": "owner-b"})
    assert forbidden.status_code == 404


@pytest.mark.asyncio
async def test_demo_runner_is_honest_about_missing_providers() -> None:
    repository = MemoryRunRepository()
    service = RunService(repository)
    run = await service.create_run(ProductIntake.model_validate(INTAKE), "demo-user")
    await service.confirm_market_definition(run.id, "demo-user", MarketDefinitionProposal(
        category="Local delivery market",
        included_boundaries="Independent retailers in India",
        excluded_boundaries="Enterprise-only offerings",
        competitors=["Store A"],
    ))
    runner = RunRunner(service)
    await runner.run(run.id, "demo-user")
    detail = await service.get_run(run.id, "demo-user")
    assert detail.status == "partial"
    assert detail.evidence_count == 0
    assert detail.report_available is False
    assert "providers are not configured" in detail.warnings[0].message


def test_event_replay_supports_after_cursor() -> None:
    client = TestClient(create_app())
    created = client.post("/runs", json=INTAKE).json()
    events = client.get(f"/runs/{created['id']}/events").json()["events"]
    assert len(events) == 1
    assert client.get(f"/runs/{created['id']}/events?after={events[0]['id']}").json()["events"] == []
