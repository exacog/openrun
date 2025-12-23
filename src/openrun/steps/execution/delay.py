"""Delay step - pauses execution for a specified duration."""

import asyncio
from typing import ClassVar

from pydantic import BaseModel, Field

from openrun.core.interpolation import Interpolated
from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class StepDelayConfig(BaseModel):
    """Configuration for delay step."""

    seconds: Interpolated[float] | float = Field(
        default=1.0,
        ge=0,
        le=300,
        description="Number of seconds to delay",
        json_schema_extra={"ui_widget": "updown"},
    )


class StepDelay(Step):
    """Pauses flow execution for a specified number of seconds.

    Outputs:
    - delayed_seconds: The actual delay duration used
    """

    type: StepType = StepType.DELAY
    config: StepDelayConfig

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(
                key="delayed_seconds",
                type=StateType.NUMBER,
                description="Actual delay duration",
            ),
        ]

    async def run(
        self, state: StateContainer, config: StepDelayConfig
    ) -> StepRunResult:
        seconds = config.seconds
        if isinstance(seconds, str):
            seconds = float(seconds)

        await asyncio.sleep(seconds)

        state.set("delayed_seconds", seconds)

        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
            output_data={"delayed_seconds": seconds},
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Delay",
            description="Pause execution for specified seconds",
            icon="timer",
            category="utility",
            color="#607D8B",
        )
