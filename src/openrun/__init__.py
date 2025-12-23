"""Workflow Engine - Flow-based workflow system.

A Python library for building flow-based workflow systems with support for
concurrent execution, conditional branching, and composable steps.

Example:
    from openrun import Flow, StepRequest, StepSetState

    # Create a flow
    flow = Flow(name="Fetch and Store")

    # Add steps
    fetch = StepRequest(config=StepRequest.Config(
        url="https://api.example.com/data",
        method="GET"
    ))
    store = StepSetState(config=StepSetState.Config(
        key="api_response",
        value="{{response}}"
    ))

    flow.add_step(fetch)
    flow.add_step(store)
    flow.add_edge(fetch, store)

    # Run
    async for event in flow.run(trigger_step=fetch):
        print(event)
"""

# Core types
from openrun.core.types import (
    JoinMode,
    StateType,
    StepRunStatus,
    StepType,
)
from openrun.core.output import Output
from openrun.core.state import StateContainer, StateSlot
from openrun.core.interpolation import (
    Interpolated,
    InterpolatedMarker,
    resolve_config,
    resolve_template,
)

# Step base
from openrun.steps.base import (
    Step,
    StepConfig,
    StepError,
    StepInfo,
    StepRunResult,
)

# Steps
from openrun.steps import (
    # Triggers
    TriggerWebhook,
    TriggerWebhookConfig,
    TriggerSchedule,
    TriggerScheduleConfig,
    TriggerEvent,
    TriggerEventConfig,
    # Execution
    StepDelay,
    StepDelayConfig,
    StepRequest,
    StepRequestConfig,
    StepSetState,
    StepSetStateConfig,
    StepConditional,
    StepConditionalConfig,
    StepSwitch,
    StepSwitchConfig,
    StepReply,
    StepReplyConfig,
    StepConversationStart,
    StepConversationStartConfig,
    StepUserMessage,
    StepUserMessageConfig,
    # Registry
    STEP_REGISTRY,
    register_step,
    get_step_class,
    AnyStep,
)

# Flow
from openrun.flow import Edge, Flow, FlowRunResult, run_flow

# Events
from openrun.events import (
    Event,
    FlowCompleted,
    FlowStarted,
    StepCompleted,
    StepStarted,
)

# Validation
from openrun.validation import (
    ValidationError,
    get_available_keys_before,
    validate_flow,
)

__all__ = [
    # Core types
    "JoinMode",
    "StateType",
    "StepRunStatus",
    "StepType",
    "Output",
    "StateContainer",
    "StateSlot",
    "Interpolated",
    "InterpolatedMarker",
    "resolve_config",
    "resolve_template",
    # Step base
    "Step",
    "StepConfig",
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
    # Execution steps
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
    "AnyStep",
    # Flow
    "Edge",
    "Flow",
    "FlowRunResult",
    "run_flow",
    # Events
    "Event",
    "FlowCompleted",
    "FlowStarted",
    "StepCompleted",
    "StepStarted",
    # Validation
    "ValidationError",
    "get_available_keys_before",
    "validate_flow",
]
