"""Switch step - routes flow based on matching cases (dynamic ports)."""

from typing import ClassVar

from pydantic import BaseModel, Field

from openrun.core.interpolation import Interpolated
from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class Case(BaseModel):
    """A single case in a switch statement."""

    name: str = Field(description="Port name for this case")
    value: Interpolated[str] = Field(description="Value to match against")


class StepSwitchConfig(BaseModel):
    """Configuration for switch step."""

    value: Interpolated[str] = Field(
        description="Value to switch on",
        json_schema_extra={"placeholder": "{{user.tier}}"},
    )
    cases: list[Case] = Field(
        default_factory=list,
        description="Cases to match against",
    )


class StepSwitch(Step):
    """Routes flow based on matching a value against configured cases.

    This step has dynamic ports - the available output ports are
    derived from the configured cases plus an "else" port.

    Example:
        Switch on {{user.tier}} with cases:
        - premium -> premium port
        - pro -> pro port
        - free -> free port
        No match -> else port
    """

    type: StepType = StepType.SWITCH
    config: StepSwitchConfig

    _ports: ClassVar[list[str]] = ["else"]  # Base port, extended by cases

    @property
    def ports(self) -> list[str]:
        """Derive ports from configured cases."""
        return [case.name for case in self.config.cases] + ["else"]

    async def run(
        self, state: StateContainer, config: StepSwitchConfig
    ) -> StepRunResult:
        # Config values are already resolved
        for case in config.cases:
            if config.value == case.value:
                return StepRunResult(
                    step_id=self.id,
                    status=StepRunStatus.SUCCESS,
                    fired_ports=[case.name],
                    output_data={"matched_case": case.name},
                )

        # No match - fire else port
        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["else"],
            output_data={"matched_case": None},
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Switch",
            description="Route flow based on value matching",
            icon="switch",
            category="logic",
            color="#E91E63",
        )
