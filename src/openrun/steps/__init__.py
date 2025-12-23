"""Step implementations for the workflow engine."""

from openrun.steps.base import (
    Step,
    StepError,
    StepInfo,
    StepRunResult,
)

# Import all step types and configs for registration
from openrun.steps.triggers.webhook import TriggerWebhook, TriggerWebhookConfig
from openrun.steps.triggers.schedule import TriggerSchedule, TriggerScheduleConfig
from openrun.steps.triggers.event import TriggerEvent, TriggerEventConfig
from openrun.steps.execution.delay import StepDelay, StepDelayConfig
from openrun.steps.execution.request import StepRequest, StepRequestConfig
from openrun.steps.execution.set_state import StepSetState, StepSetStateConfig
from openrun.steps.execution.conditional import StepConditional, StepConditionalConfig
from openrun.steps.execution.switch import StepSwitch, StepSwitchConfig
from openrun.steps.execution.reply import StepReply, StepReplyConfig
from openrun.steps.execution.conversation import (
    StepConversationStart,
    StepConversationStartConfig,
    StepUserMessage,
    StepUserMessageConfig,
)

# Step registry for discovery
STEP_REGISTRY: dict[str, type[Step]] = {}


def register_step(step_type: str):
    """Decorator to register a step class in the registry."""

    def decorator(cls: type[Step]) -> type[Step]:
        STEP_REGISTRY[step_type] = cls
        return cls

    return decorator


def get_step_class(step_type: str) -> type[Step] | None:
    """Get a step class by type string."""
    return STEP_REGISTRY.get(step_type)


def register_all_steps() -> None:
    """Register all built-in step types."""
    # Triggers
    STEP_REGISTRY["trigger_webhook"] = TriggerWebhook
    STEP_REGISTRY["trigger_schedule"] = TriggerSchedule
    STEP_REGISTRY["trigger_event"] = TriggerEvent

    # Execution steps
    STEP_REGISTRY["delay"] = StepDelay
    STEP_REGISTRY["request"] = StepRequest
    STEP_REGISTRY["set_state"] = StepSetState
    STEP_REGISTRY["conditional"] = StepConditional
    STEP_REGISTRY["switch"] = StepSwitch
    STEP_REGISTRY["reply"] = StepReply
    STEP_REGISTRY["conversation_start"] = StepConversationStart
    STEP_REGISTRY["user_message"] = StepUserMessage


# Auto-register on import
register_all_steps()

# Union type for all steps (for Pydantic discriminated unions)
AnyStep = (
    TriggerWebhook
    | TriggerSchedule
    | TriggerEvent
    | StepDelay
    | StepRequest
    | StepSetState
    | StepConditional
    | StepSwitch
    | StepReply
    | StepConversationStart
    | StepUserMessage
)

__all__ = [
    # Base
    "Step",
    "StepError",
    "StepInfo",
    "StepRunResult",
    # Triggers
    "TriggerWebhook",
    "TriggerWebhookConfig",
    "TriggerSchedule",
    "TriggerScheduleConfig",
    "TriggerEvent",
    "TriggerEventConfig",
    # Execution
    "StepDelay",
    "StepDelayConfig",
    "StepRequest",
    "StepRequestConfig",
    "StepSetState",
    "StepSetStateConfig",
    "StepConditional",
    "StepConditionalConfig",
    "StepSwitch",
    "StepSwitchConfig",
    "StepReply",
    "StepReplyConfig",
    "StepConversationStart",
    "StepConversationStartConfig",
    "StepUserMessage",
    "StepUserMessageConfig",
    # Registry
    "STEP_REGISTRY",
    "register_step",
    "get_step_class",
    "register_all_steps",
    "AnyStep",
]
