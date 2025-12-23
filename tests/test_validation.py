"""Tests for flow validation."""

from openrun.flow.flow import Flow
from openrun.steps.execution.delay import StepDelay, StepDelayConfig
from openrun.steps.execution.set_state import StepSetState, StepSetStateConfig
from openrun.steps.triggers.webhook import TriggerWebhook, TriggerWebhookConfig
from openrun.validation.validator import (
    get_available_keys_before,
    validate_edges,
    validate_flow,
    validate_triggers,
)


class TestGetAvailableKeysBefore:
    """Tests for get_available_keys_before function."""

    def test_trigger_outputs_available(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(delay)
        flow.add_edge(trigger, delay)

        # Delay should see trigger's outputs
        keys = get_available_keys_before(flow, delay)
        assert "body" in keys
        assert "headers" in keys
        assert "method" in keys
        assert "query" in keys

    def test_set_state_key_available(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        set_state = StepSetState(config=StepSetStateConfig(key="my_var", value="hello"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(set_state)
        flow.add_step(delay)
        flow.add_edge(trigger, set_state)
        flow.add_edge(set_state, delay)

        # Delay should see set_state's configured key
        keys = get_available_keys_before(flow, delay)
        assert "my_var" in keys

    def test_step_outputs_available(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))
        set_state = StepSetState(config=StepSetStateConfig(key="x", value="y"))

        flow.add_step(trigger)
        flow.add_step(delay)
        flow.add_step(set_state)
        flow.add_edge(trigger, delay)
        flow.add_edge(delay, set_state)

        # set_state should see delay's outputs
        keys = get_available_keys_before(flow, set_state)
        assert "delayed_seconds" in keys


class TestValidateFlow:
    """Tests for validate_flow function."""

    def test_valid_flow_no_errors(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        set_state = StepSetState(
            config=StepSetStateConfig(
                key="greeting",
                value="Hello {{body}}",  # body is from trigger
            )
        )

        flow.add_step(trigger)
        flow.add_step(set_state)
        flow.add_edge(trigger, set_state)

        errors = validate_flow(flow)
        assert len(errors) == 0

    def test_invalid_ref_error(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        set_state = StepSetState(
            config=StepSetStateConfig(
                key="greeting",
                value="Hello {{nonexistent}}",  # Invalid ref
            )
        )

        flow.add_step(trigger)
        flow.add_step(set_state)
        flow.add_edge(trigger, set_state)

        errors = validate_flow(flow)
        assert len(errors) == 1
        assert errors[0].reference == "nonexistent"


class TestValidateEdges:
    """Tests for validate_edges function."""

    def test_valid_edges(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(delay)
        flow.add_edge(trigger, delay)

        errors = validate_edges(flow)
        assert len(errors) == 0

    def test_invalid_source_port(self):
        from openrun.flow.edge import Edge

        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(delay)

        # Manually add edge with invalid port (bypassing validation)
        flow.edges.append(
            Edge(
                source_step_id=trigger.id,
                source_port="invalid_port",
                target_step_id=delay.id,
            )
        )

        errors = validate_edges(flow)
        assert len(errors) == 1
        assert "invalid_port" in errors[0].message


class TestValidateTriggers:
    """Tests for validate_triggers function."""

    def test_flow_with_trigger(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        flow.add_step(trigger)

        errors = validate_triggers(flow)
        assert len(errors) == 0

    def test_flow_without_trigger(self):
        flow = Flow(name="Test")
        delay = StepDelay(config=StepDelayConfig(seconds=1))
        flow.add_step(delay)

        errors = validate_triggers(flow)
        assert len(errors) == 1
        assert errors[0].level == "warning"
        assert "no trigger" in errors[0].message.lower()
