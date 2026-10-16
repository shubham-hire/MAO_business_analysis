from __future__ import annotations

from app.domain.run_service import RunService
from app.orchestration.pipeline import DemoPipeline, DeterministicPipeline


class RunRunner:
    def __init__(self, service: RunService, pipeline: DeterministicPipeline | None = None) -> None:
        self.service = service
        self.pipeline = pipeline or DemoPipeline()

    async def run(self, run_id: str, owner_id: str) -> None:
        run = await self.service.start_running(run_id, owner_id)
        try:
            result = await self.pipeline.run(run)
        except Exception as exc:
            await self.service.fail_pipeline(
                run_id,
                owner_id,
                message=f"Research pipeline failed: {type(exc).__name__}.",
            )
            return
        await self.service.finish_pipeline(run_id, owner_id, result)
