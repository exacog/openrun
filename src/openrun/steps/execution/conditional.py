"""Conditional step - branches flow based on conditions."""

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from openrun.core.interpolation import Interpolated
from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class StepConditionalConfig(BaseModel):
    """Configuration for conditional step."""

    left: Interpolated[str] = Field(
        description="Left side of comparison",
        json_schema_extra={"placeholder": "{{user.role}}"},
    )
    operator: Literal[
        "equals", "not_equals", "contains", "not_contains", "greater_than", "less_than"
    ] = Field(
        default="equals",
        description="Comparison operator",
    )
    right: Interpolated[str] = Field(
        description="Right side of comparison",
        json_schema_extra={"placeholder": "admin"},
    )


def evaluate_condition(left: str, operator: str, right: str) -> bool:
    """Evaluate a condition with the given operator."""
    if operator == "equals":
        return left == right
    elif operator == "not_equals":
        return left != right
    elif operator == "contains":
        return right in left
    elif operator == "not_contains":
        return right not in left
    elif operator == "greater_than":
        try:
            return float(left) > float(right)
        except ValueError:
            return left > right
    elif operator == "less_than":
        try:
            return float(left) < float(right)
        except ValueError:
            return left < right
    return False


class StepConditional(Step):
    """Branches flow execution based on a condition.

    Evaluates a comparison between left and right values using
    the specified operator, then fires the appropriate port.

    Ports:
    - true: Fires when condition is true
    - false: Fires when condition is false
    """

    type: StepType = StepType.CONDITIONAL
    config: StepConditionalConfig

    _ports: ClassVar[list[str]] = ["true", "false"]

    async def run(
        self, state: StateContainer, config: StepConditionalConfig
    ) -> StepRunResult:
        # Config values are already resolved
        result = evaluate_condition(config.left, config.operator, config.right)

        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["true" if result else "false"],
            output_data={"condition_result": result},
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Conditional",
            description="Branch based on a condition",
            icon="fork",
            category="logic",
            color="#FF5722",
        )
