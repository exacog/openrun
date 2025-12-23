"""Test fixtures for runtime module tests."""

import pytest

from openrun.core.state import StateContainer
from openrun.flow.flow import Flow
from openrun.steps.execution.delay import StepDelay, StepDelayConfig
from openrun.steps.triggers.webhook import TriggerWebhook, TriggerWebhookConfig


@pytest.fixture
def state() -> StateContainer:
    """Empty state container."""
    return StateContainer()


@pytest.fixture
def state_with_data() -> StateContainer:
    """State with sample data for interpolation tests."""
    state = StateContainer()
    state.set(
        "user", {"name": "Alice", "id": 42, "profile": {"email": "alice@example.com"}}
    )
    state.set("items", [{"name": "Item1", "price": 10}, {"name": "Item2", "price": 20}])
    state.set("count", 5)
    state.set("message", "Hello, World!")
    return state


@pytest.fixture
def simple_flow() -> Flow:
    """A simple two-step flow for basic tests."""
    flow = Flow(name="Simple Test Flow")

    trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
    delay = StepDelay(config=StepDelayConfig(seconds=0.01))

    flow.add_step(trigger)
    flow.add_step(delay)
    flow.add_edge(trigger, delay)

    return flow


@pytest.fixture
def branching_flow() -> Flow:
    """A flow with conditional branching."""
    from openrun.steps.execution.conditional import (
        StepConditional,
        StepConditionalConfig,
    )
    from openrun.steps.execution.reply import StepReply, StepReplyConfig

    flow = Flow(name="Branching Flow")

    trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/branch"))
    condition = StepConditional(
        config=StepConditionalConfig(
            left="{{user.role}}",
            operator="equals",
            right="admin",
        )
    )
    admin_reply = StepReply(config=StepReplyConfig(template="Admin access granted"))
    user_reply = StepReply(config=StepReplyConfig(template="User access"))

    flow.add_step(trigger)
    flow.add_step(condition)
    flow.add_step(admin_reply)
    flow.add_step(user_reply)

    flow.add_edge(trigger, condition)
    flow.add_edge(condition, admin_reply, source_port="true")
    flow.add_edge(condition, user_reply, source_port="false")

    return flow


@pytest.fixture
def fan_out_flow() -> Flow:
    """A flow with parallel execution (fan-out)."""
    flow = Flow(name="Fan-out Flow")

    trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/fanout"))
    delay1 = StepDelay(config=StepDelayConfig(seconds=0.01))
    delay2 = StepDelay(config=StepDelayConfig(seconds=0.01))

    flow.add_step(trigger)
    flow.add_step(delay1)
    flow.add_step(delay2)

    # Same port to multiple targets = parallel execution
    flow.add_edge(trigger, delay1)
    flow.add_edge(trigger, delay2)

    return flow
