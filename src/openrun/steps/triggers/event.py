"""Event trigger step."""

from typing import ClassVar

from pydantic import BaseModel, Field

from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class TriggerEventConfig(BaseModel):
    """Configuration for event trigger."""

    event_name: str = Field(
        description="Name of the event to listen for",
        json_schema_extra={"placeholder": "user.created"},
    )


class TriggerEvent(Step):
    """Starts a flow when a named event fires.

    The event dispatcher injects event data into state:
    - event_name: Name of the event that fired
    - event_data: Payload data from the event
    - event_timestamp: ISO timestamp of event
    """

    type: StepType = StepType.TRIGGER_EVENT
    is_trigger: bool = True
    config: TriggerEventConfig

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(
                key="event_name",
                type=StateType.TEXT,
                description="Name of the event",
            ),
            Output(
                key="event_data",
                type=StateType.ANY,
                description="Event payload data",
            ),
            Output(
                key="event_timestamp",
                type=StateType.TEXT,
                description="Event timestamp (ISO)",
            ),
        ]

    async def run(
        self, state: StateContainer, config: TriggerEventConfig
    ) -> StepRunResult:
        # Event data injected by dispatcher before run()
        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Event",
            description="Start flow when event fires",
            icon="bolt",
            category="triggers",
            color="#9C27B0",
        )
