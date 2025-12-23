"""Events yielded during flow execution."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from openrun.steps.base import StepRunResult


@dataclass
class FlowStarted:
    """Emitted when flow execution begins."""

    run_id: UUID
    flow_name: str | None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StepStarted:
    """Emitted when a step begins execution."""

    run_id: UUID
    step_id: UUID
    step_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StepCompleted:
    """Emitted when a step finishes execution."""

    run_id: UUID
    step_id: UUID
    result: StepRunResult
    duration_ms: float
    state_snapshot: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FlowCompleted:
    """Emitted when flow execution finishes."""

    run_id: UUID
    status: str  # "succeeded" or "failed"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Union type for all events
Event = FlowStarted | StepStarted | StepCompleted | FlowCompleted

__all__ = [
    "FlowStarted",
    "StepStarted",
    "StepCompleted",
    "FlowCompleted",
    "Event",
]
