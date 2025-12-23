"""SetState step - saves values to the state container."""

from typing import ClassVar

from pydantic import BaseModel, Field

from openrun.core.interpolation import Interpolated
from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class StepSetStateConfig(BaseModel):
    """Configuration for set state step."""

    key: str = Field(
        description="State key to set",
        json_schema_extra={"placeholder": "my_variable"},
    )
    value: Interpolated[str] = Field(
        description="Value to set (supports {{state}} references)",
        json_schema_extra={"ui_widget": "textarea"},
    )


class StepSetState(Step):
    """Saves a value to the state container.

    The output key is user-defined via config.key, so this step
    doesn't declare outputs() - the validator reads config.key instead.
    """

    type: StepType = StepType.SET_STATE
    config: StepSetStateConfig

    _ports: ClassVar[list[str]] = ["default"]

    # No outputs() - key is user-defined, validator reads config.key

    async def run(
        self, state: StateContainer, config: StepSetStateConfig
    ) -> StepRunResult:
        # Value is already resolved by runner
        state.set(config.key, config.value)

        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
            output_data={config.key: config.value},
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Set State",
            description="Save a value to flow state",
            icon="save",
            category="utility",
            color="#795548",
        )
