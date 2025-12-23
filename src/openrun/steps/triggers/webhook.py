"""Webhook trigger step."""

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class TriggerWebhookConfig(BaseModel):
    """Configuration for webhook trigger."""

    method: Literal["GET", "POST", "PUT", "DELETE"] = Field(
        default="POST",
        description="HTTP method to accept",
    )
    path: str = Field(
        description="Webhook endpoint path",
        json_schema_extra={"placeholder": "/webhook/my-flow"},
    )


class TriggerWebhook(Step):
    """Starts a flow when an HTTP request is received.

    The webhook handler injects request data into state before running:
    - body: Request body (parsed JSON or raw text)
    - headers: Request headers as dict
    - method: HTTP method used
    - query: Query parameters as dict
    """

    type: StepType = StepType.TRIGGER_WEBHOOK
    is_trigger: bool = True
    config: TriggerWebhookConfig

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(key="body", type=StateType.ANY, description="Request body"),
            Output(key="headers", type=StateType.OBJECT, description="Request headers"),
            Output(key="method", type=StateType.TEXT, description="HTTP method"),
            Output(key="query", type=StateType.OBJECT, description="Query parameters"),
        ]

    async def run(
        self, state: StateContainer, config: TriggerWebhookConfig
    ) -> StepRunResult:
        # Trigger steps receive their data via state (injected by the runner)
        # The runner sets body, headers, method, query before calling run()
        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Webhook",
            description="Start flow when HTTP request received",
            icon="webhook",
            category="triggers",
            color="#4CAF50",
        )
