from __future__ import annotations

import asyncio
from copy import deepcopy

from app.domain.run_snapshot import RunSnapshot
from app.schemas import RunEvent


class MemoryRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, RunSnapshot] = {}
        self._lock = asyncio.Lock()

    async def create(self, run: RunSnapshot) -> None:
        async with self._lock:
            self._runs[run.id] = deepcopy(run)

    async def get(self, run_id: str, owner_id: str) -> RunSnapshot | None:
        async with self._lock:
            run = self._runs.get(run_id)
            if run is None or run.owner_id != owner_id:
                return None
            return deepcopy(run)

    async def list(self, owner_id: str) -> list[RunSnapshot]:
        async with self._lock:
            return [deepcopy(run) for run in self._runs.values() if run.owner_id == owner_id]

    async def save(self, run: RunSnapshot) -> None:
        async with self._lock:
            self._runs[run.id] = deepcopy(run)

    async def events(self, run_id: str, owner_id: str, after: str | None = None) -> list[RunEvent] | None:
        run = await self.get(run_id, owner_id)
        if run is None:
            return None
        if after is None:
            return run.events
        for index, event in enumerate(run.events):
            if event.id == after:
                return run.events[index + 1 :]
        return run.events
