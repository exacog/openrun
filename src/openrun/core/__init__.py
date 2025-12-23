"""Core primitives for the workflow engine."""

from openrun.core.types import (
    JoinMode,
    StateType,
    StepRunStatus,
    StepType,
)
from openrun.core.output import Output
from openrun.core.state import StateContainer, StateSlot
from openrun.core.interpolation import (
    Interpolated,
    InterpolatedMarker,
    resolve_config,
    resolve_template,
)

__all__ = [
    # Enums
    "JoinMode",
    "StateType",
    "StepRunStatus",
    "StepType",
    # Models
    "Output",
    "StateContainer",
    "StateSlot",
    # Interpolation
    "Interpolated",
    "InterpolatedMarker",
    "resolve_config",
    "resolve_template",
]
