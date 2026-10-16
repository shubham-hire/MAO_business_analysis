from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.domain.run_snapshot import STAGE_NAMES, RunSnapshot
from app.domain.run_state import InvalidTransition, transition
from app.infrastructure.memory_repository import MemoryRunRepository
from app.orchestration.pipeline import PipelineResult
from app.schemas import (
    MarketDefinitionProposal,
    ProductIntake,
    RunDetail,
    RunEvent,
    RunStatus,
    RunSummary,
    RunWarning,
    StageSnapshot,
    StageState,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


class MissingRun(Exception):
    pass


class RunService:
    def __init__(self, repository: MemoryRunRepository) -> None:
        self.repository = repository

    async def create_run(self, intake: ProductIntake, owner_id: str) -> RunSummary:
        timestamp = now()
        proposal = self._propose_market(intake)
        run_id = f"run-{uuid4().hex[:12]}"
        run = RunSnapshot(
            id=run_id,
            owner_id=owner_id,
            intake=intake,
            created_at=timestamp,
            updated_at=timestamp,
            status=RunStatus.DRAFT,
            market_definition="Market definition proposed; confirmation required",
            proposed_market_definition=proposal,
            stages=[
                StageSnapshot(name=name, state=StageState.SKIPPED if name == "customer_voice" else StageState.PENDING)
                for name in STAGE_NAMES
            ],
        )
        await self.repository.create(run)
        await self._change_status(run, RunStatus.AWAITING_MARKET_CONFIRMATION, owner_id, "Market definition proposed.")
        return self._summary(run)

    async def list_runs(self, owner_id: str) -> list[RunSummary]:
        runs = await self.repository.list(owner_id)
        return [self._summary(run) for run in sorted(runs, key=lambda item: item.updated_at, reverse=True)]

    async def get_run(self, run_id: str, owner_id: str) -> RunDetail:
        run = await self._get(run_id, owner_id)
        return self._detail(run)

    async def confirm_market_definition(
        self, run_id: str, owner_id: str, definition: MarketDefinitionProposal
    ) -> RunSummary:
        run = await self._get(run_id, owner_id)
        self._ensure_status(run, RunStatus.AWAITING_MARKET_CONFIRMATION)
        run.confirmed_market_definition = definition
        run.proposed_market_definition = definition
        run.market_definition = definition.category
        await self._change_status(run, RunStatus.QUEUED, owner_id, "Market definition confirmed; run queued.")
        return self._summary(run)

    async def append_warning(self, run_id: str, owner_id: str, warning: RunWarning) -> None:
        run = await self._get(run_id, owner_id)
        run.warnings.append(warning)
        run.updated_at = now()
        await self.repository.save(run)

    async def _change_status(self, run: RunSnapshot, target: RunStatus, actor: str, message: str) -> None:
        previous = run.status
        run.status = transition(previous, target)
        run.updated_at = now()
        run.events.append(
            RunEvent(
                id=f"event-{uuid4().hex[:12]}",
                run_id=run.id,
                type="run.status_changed",
                timestamp=run.updated_at,
                message=message,
                status=target.value,
                actor=actor,
            )
        )
        await self.repository.save(run)

    async def start_running(self, run_id: str, owner_id: str) -> RunSnapshot:
        run = await self._get(run_id, owner_id)
        await self._change_status(run, RunStatus.RUNNING, "system", "Research pipeline started.")
        for stage in run.stages:
            if stage.state == StageState.PENDING:
                started_at = now()
                stage.state = StageState.RUNNING
                stage.started_at = started_at
                run.events.append(
                    RunEvent(
                        id=f"event-{uuid4().hex[:12]}",
                        run_id=run.id,
                        type="stage.started",
                        timestamp=started_at,
                        message=f"{stage.name} stage started.",
                        status=stage.state.value,
                        actor="system",
                        stage=stage.name,
                    )
                )
                run.updated_at = started_at
                await self.repository.save(run)
                break
        return run

    async def fail_pipeline(
        self,
        run_id: str,
        owner_id: str,
        message: str,
        error_code: str = "pipeline_failed",
    ) -> RunSummary:
        run = await self._get(run_id, owner_id)
        active_stage = next((stage for stage in run.stages if stage.state == StageState.RUNNING), None)
        if active_stage is not None:
            active_stage.state = StageState.FAILED
            active_stage.completed_at = now()
            active_stage.warning = message
            active_stage.error_code = error_code
            run.events.append(self._stage_event(run.id, active_stage.name, StageState.FAILED, message))
        if not any(warning.message == message for warning in run.warnings):
            run.warnings.append(RunWarning(stage=active_stage.name if active_stage else None, message=message))
        await self._change_status(run, RunStatus.FAILED, "system", message)
        return self._summary(run)

    async def finish_pipeline(self, run_id: str, owner_id: str, result: PipelineResult) -> RunSummary:
        run = await self._get(run_id, owner_id)
        run.sources = result.sources
        run.claims = result.claims
        run.evidence = result.evidence
        run.evidence_count = len(run.evidence)
        run.report_available = result.report_available
        for warning in result.warnings:
            if warning and warning not in {item.message for item in run.warnings}:
                run.warnings.append(RunWarning(message=warning))
        stage_by_name = {stage.name: stage for stage in run.stages}
        output_names: set[str] = set()
        for output in result.stage_results:
            stage = stage_by_name.get(output.name)
            if stage is None:
                continue
            output_names.add(output.name)
            stage.state = StageState(output.state)
            stage.provider = output.provider
            stage.source_ids = [source.id for source in output.sources]
            stage.claim_ids = [claim.id for claim in output.claims]
            stage.evidence_ids = [evidence.id for evidence in output.evidence]
            stage.source_count = len(output.sources)
            stage.claim_count = len(output.claims)
            stage.evidence_count = len(output.evidence)
            stage.warning = output.warning
            stage.error_code = output.error_code
            if stage.state != StageState.SKIPPED:
                if stage.started_at is None:
                    stage.started_at = output.started_at or now()
                    run.events.append(self._stage_event(
                        run.id,
                        stage.name,
                        StageState.RUNNING,
                        f"{stage.name} stage started.",
                        timestamp=stage.started_at,
                    ))
                stage.completed_at = output.completed_at or now()
            run.events.append(self._stage_event(
                run.id,
                stage.name,
                stage.state,
                output.warning or f"{stage.name} stage {stage.state.value}.",
                timestamp=stage.completed_at,
            ))
        if result.outcome == "failed":
            active_stage = next((stage for stage in run.stages if stage.state == StageState.RUNNING), None)
            if active_stage is not None and active_stage.name not in output_names:
                failure_message = result.warning or "Pipeline returned a failed outcome."
                active_stage.state = StageState.FAILED
                active_stage.completed_at = now()
                active_stage.warning = failure_message
                active_stage.error_code = "pipeline_failed"
                run.events.append(self._stage_event(run.id, active_stage.name, StageState.FAILED, failure_message))
            target = RunStatus.FAILED
        elif result.outcome == "completed" and self._is_complete_result(result):
            target = RunStatus.COMPLETED
        else:
            target = RunStatus.PARTIAL
            if result.outcome == "completed":
                warning = "Pipeline reported completion before all required stages and artifacts were ready; marked partial."
                if warning not in {item.message for item in run.warnings}:
                    run.warnings.append(RunWarning(message=warning))
        await self._change_status(run, target, "system", f"Research pipeline {target.value}.")
        return self._summary(run)

    @staticmethod
    def _is_complete_result(result: PipelineResult) -> bool:
        stages = {stage.name: stage for stage in result.stage_results}
        if set(STAGE_NAMES) - stages.keys() or not result.report_available:
            return False
        return all(stage.state in {StageState.COMPLETED.value, StageState.SKIPPED.value} for stage in stages.values())

    @staticmethod
    def _stage_event(
        run_id: str,
        stage: str,
        state: StageState,
        message: str,
        timestamp: datetime | None = None,
    ) -> RunEvent:
        return RunEvent(
            id=f"event-{uuid4().hex[:12]}",
            run_id=run_id,
            type=f"stage.{state.value}",
            timestamp=timestamp or now(),
            message=message,
            status=state.value,
            actor="system",
            stage=stage,
        )

    async def _get(self, run_id: str, owner_id: str) -> RunSnapshot:
        run = await self.repository.get(run_id, owner_id)
        if run is None:
            raise MissingRun(run_id)
        return run

    @staticmethod
    def _ensure_status(run: RunSnapshot, expected: RunStatus) -> None:
        if run.status != expected:
            raise InvalidTransition(run.status, expected)

    @staticmethod
    def _propose_market(intake: ProductIntake) -> MarketDefinitionProposal:
        category = f"{intake.product_name or 'Product'} market"
        included = (
            f"Products serving {intake.target_customer} in {intake.region}, priced between "
            f"{intake.price_range.currency} {intake.price_range.minimum:g} and {intake.price_range.maximum:g}."
        )
        excluded = "Enterprise-only offerings and markets outside the selected region."
        reasons = {competitor: "Provided by the user as a known competitor." for competitor in intake.competitors}
        return MarketDefinitionProposal(
            category=category,
            included_boundaries=included,
            excluded_boundaries=excluded,
            competitors=intake.competitors,
            competitor_reasons=reasons,
        )

    @staticmethod
    def _summary(run: RunSnapshot) -> RunSummary:
        return RunSummary(
            id=run.id,
            product_name=run.intake.product_name or "Untitled product idea",
            region=run.intake.region,
            market_definition=run.market_definition,
            created_at=run.created_at,
            updated_at=run.updated_at,
            status=run.status,
            evidence_count=run.evidence_count,
            source_count=len(run.sources),
            claim_count=len(run.claims),
            verified_claim_count=sum(1 for claim in run.claims if claim.verification_status.value == "verified"),
            report_available=run.report_available,
            warnings=run.warnings,
            proposed_market_definition=run.proposed_market_definition,
            confirmed_market_definition=run.confirmed_market_definition,
        )

    @staticmethod
    def _detail(run: RunSnapshot) -> RunDetail:
        summary = RunService._summary(run)
        return RunDetail(**summary.model_dump(), stages=run.stages, intake=run.intake, sources=run.sources, claims=run.claims, evidence=run.evidence)
