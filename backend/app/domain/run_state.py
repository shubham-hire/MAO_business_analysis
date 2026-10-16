from __future__ import annotations

from dataclasses import dataclass

from app.schemas import RunStatus


@dataclass
class InvalidTransition(Exception):
    current: RunStatus
    target: RunStatus

    def __str__(self) -> str:
        return f"cannot move run from {self.current.value} to {self.target.value}"


ALLOWED_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.DRAFT: {RunStatus.AWAITING_MARKET_CONFIRMATION},
    RunStatus.AWAITING_MARKET_CONFIRMATION: {RunStatus.QUEUED},
    RunStatus.QUEUED: {RunStatus.RUNNING},
    RunStatus.RUNNING: {RunStatus.COMPLETED, RunStatus.PARTIAL, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.PARTIAL: {RunStatus.QUEUED},
    RunStatus.FAILED: {RunStatus.QUEUED},
    RunStatus.COMPLETED: set(),
    RunStatus.CANCELLED: set(),
}


def transition(current: RunStatus, target: RunStatus) -> RunStatus:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(current, target)
    return target
