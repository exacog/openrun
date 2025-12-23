"""Base step class and related models for the workflow engine."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import JoinMode, StepRunStatus, StepType


class StepError(BaseModel):
    """Error information from a failed step execution."""

    message: str
    code: str | None = None
    details: dict[str, Any] | None = None


class StepRunResult(BaseModel):
    """Result of a step execution."""

    step_id: UUID
    status: StepRunStatus
    fired_ports: list[str] = Field(default_factory=lambda: ["default"])
    continue_without_waiting: bool = False
    output_data: dict[str, Any] | None = None
    error: StepError | None = None

    @classmethod
    def success(
        cls,
        step_id: UUID,
        fired_ports: list[str] | None = None,
        output_data: dict[str, Any] | None = None,
        continue_without_waiting: bool = False,
    ) -> "StepRunResult":
        """Create a successful result."""
        return cls(
            step_id=step_id,
            status=StepRunStatus.SUCCESS,
            fired_ports=fired_ports or ["default"],
            output_data=output_data,
            continue_without_waiting=continue_without_waiting,
        )

    @classmethod
    def failure(
        cls,
        step_id: UUID,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        fired_ports: list[str] | None = None,
    ) -> "StepRunResult":
        """Create a failed result."""
        return cls(
            step_id=step_id,
            status=StepRunStatus.ERROR,
            fired_ports=fired_ports or ["error"]
            if "error" in (fired_ports or [])
            else ["default"],
            error=StepError(message=message, code=code, details=details),
        )


class StepInfo(BaseModel):
    """Metadata about a step type for UI display."""

    name: str
    description: str
    icon: str | None = None
    category: str
    color: str | None = None


class StepConfig(BaseModel):
    """Base class for step configuration."""

    model_config = ConfigDict(frozen=True)


class Step(BaseModel, ABC):
    """Base class for all workflow steps.

    Steps are execution units within a flow. Each step defines:
    - Input/output ports for edge connections
    - Configuration as a nested Pydantic model
    - Execution logic in the run() method
    - Declared outputs for downstream steps
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    type: StepType
    join_mode: JoinMode = JoinMode.NO_WAIT
    position: tuple[int, int] = (0, 0)
    is_trigger: bool = False

    # Class-level port definition (override in subclasses)
    _ports: ClassVar[list[str]] = ["default"]

    @property
    def ports(self) -> list[str]:
        """Output ports for this step.

        Override in subclasses for dynamic ports based on config.
        """
        return self._ports

    @classmethod
    def outputs(cls) -> list[Output]:
        """Declare what state keys this step produces.

        Override in subclasses to declare outputs for validation
        and UI display of available {{refs}} downstream.
        """
        return []

    @abstractmethod
    async def run(self, state: StateContainer, config: BaseModel) -> StepRunResult:
        """Execute the step.

        Args:
            state: Full state container for reading/writing during execution
            config: Pre-resolved config (all {{refs}} already replaced with values)

        Returns:
            StepRunResult indicating success/failure and which ports to fire
        """
        raise NotImplementedError()

    @classmethod
    def info(cls) -> StepInfo:
        """Return metadata about this step type for UI display.

        Override in subclasses to provide step-specific metadata.
        """
        return StepInfo(
            name=cls.__name__,
            description="No description provided",
            category="general",
        )
