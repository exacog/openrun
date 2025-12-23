"""Schedule trigger step."""

from typing import ClassVar

from pydantic import BaseModel, Field

from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class TriggerScheduleConfig(BaseModel):
    """Configuration for schedule trigger."""

    cron: str = Field(
        description="Cron expression for scheduling",
        json_schema_extra={"placeholder": "0 * * * *"},
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for the schedule",
    )


class TriggerSchedule(Step):
    """Starts a flow on a schedule (cron expression).

    The scheduler injects trigger metadata into state:
    - scheduled_time: ISO timestamp of scheduled execution
    - actual_time: ISO timestamp of actual execution
    """

    type: StepType = StepType.TRIGGER_SCHEDULE
    is_trigger: bool = True
    config: TriggerScheduleConfig

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(
                key="scheduled_time",
                type=StateType.TEXT,
                description="Scheduled execution time (ISO)",
            ),
            Output(
                key="actual_time",
                type=StateType.TEXT,
                description="Actual execution time (ISO)",
            ),
        ]

    async def run(
        self, state: StateContainer, config: TriggerScheduleConfig
    ) -> StepRunResult:
        # Schedule data injected by scheduler before run()
        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Schedule",
            description="Start flow on a schedule",
            icon="schedule",
            category="triggers",
            color="#FF9800",
        )
