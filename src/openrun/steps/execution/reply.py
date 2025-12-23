"""Reply step - generates a reply message (migrated from NodeReply)."""

from typing import ClassVar

from pydantic import BaseModel, Field

from openrun.core.interpolation import Interpolated
from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class StepReplyConfig(BaseModel):
    """Configuration for reply step."""

    template: Interpolated[str] = Field(
        default="",
        description="Reply template (supports {{state}} references)",
        json_schema_extra={"ui_widget": "textarea"},
    )


class StepReply(Step):
    """Generates a reply message using a template.

    The template can include {{state}} references that are
    resolved before execution.

    Outputs:
    - reply: The generated reply text
    """

    type: StepType = StepType.REPLY
    config: StepReplyConfig

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(key="reply", type=StateType.TEXT, description="Generated reply"),
        ]

    async def run(
        self, state: StateContainer, config: StepReplyConfig
    ) -> StepRunResult:
        # Template is already resolved
        reply = config.template

        state.set("reply", reply)

        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
            output_data={"reply": reply},
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Reply",
            description="Generate a reply message",
            icon="message",
            category="conversation",
            color="#00BCD4",
        )
