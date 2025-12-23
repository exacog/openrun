"""Tests for Flow and Edge models."""

import pytest
from uuid import uuid4

from openrun.flow.edge import Edge
from openrun.flow.flow import Flow
from openrun.steps.execution.delay import StepDelay, StepDelayConfig
from openrun.steps.execution.conditional import StepConditional, StepConditionalConfig
from openrun.steps.triggers.webhook import TriggerWebhook, TriggerWebhookConfig


class TestEdge:
    """Tests for Edge model."""

    def test_edge_creation(self):
        source_id = uuid4()
        target_id = uuid4()
        edge = Edge(
            source_step_id=source_id,
            source_port="success",
            target_step_id=target_id,
            target_port="default",
        )

        assert edge.source_step_id == source_id
        assert edge.source_port == "success"
        assert edge.target_step_id == target_id
        assert edge.target_port == "default"
        assert edge.id is not None

    def test_edge_default_ports(self):
        edge = Edge(source_step_id=uuid4(), target_step_id=uuid4())
        assert edge.source_port == "default"
        assert edge.target_port == "default"


class TestFlow:
    """Tests for Flow operations."""

    def test_add_step(self):
        flow = Flow(name="Test")
        step = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(step)

        assert step in flow.steps
        assert flow.get_step(step.id) == step

    def test_add_edge(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(delay)
        edge = flow.add_edge(trigger, delay)

        assert edge.source_step_id == trigger.id
        assert edge.target_step_id == delay.id
        assert edge in flow.edges

    def test_add_edge_with_ports(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        condition = StepConditional(
            config=StepConditionalConfig(left="a", operator="equals", right="b")
        )
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(condition)
        flow.add_step(delay)

        # Condition has "true" and "false" ports
        edge = flow.add_edge(condition, delay, source_port="true")

        assert edge.source_port == "true"

    def test_add_edge_invalid_port(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(delay)

        # Trigger only has "default" port
        with pytest.raises(ValueError, match="Port 'invalid' not found"):
            flow.add_edge(trigger, delay, source_port="invalid")

    def test_add_edge_missing_step(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        # delay not added to flow

        with pytest.raises(ValueError, match="Target step .* not found"):
            flow.add_edge(trigger, delay)

    def test_get_step(self):
        flow = Flow(name="Test")
        step = StepDelay(config=StepDelayConfig(seconds=1))
        flow.add_step(step)

        assert flow.get_step(step.id) == step
        assert flow.get_step(uuid4()) is None

    def test_get_edges_from(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay1 = StepDelay(config=StepDelayConfig(seconds=1))
        delay2 = StepDelay(config=StepDelayConfig(seconds=2))

        flow.add_step(trigger)
        flow.add_step(delay1)
        flow.add_step(delay2)
        flow.add_edge(trigger, delay1)
        flow.add_edge(trigger, delay2)

        edges = flow.get_edges_from(trigger.id)
        assert len(edges) == 2

    def test_get_edges_from_with_port_filter(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        condition = StepConditional(
            config=StepConditionalConfig(left="a", operator="equals", right="b")
        )
        delay1 = StepDelay(config=StepDelayConfig(seconds=1))
        delay2 = StepDelay(config=StepDelayConfig(seconds=2))

        flow.add_step(trigger)
        flow.add_step(condition)
        flow.add_step(delay1)
        flow.add_step(delay2)

        flow.add_edge(trigger, condition)
        flow.add_edge(condition, delay1, source_port="true")
        flow.add_edge(condition, delay2, source_port="false")

        true_edges = flow.get_edges_from(condition.id, port="true")
        assert len(true_edges) == 1
        assert true_edges[0].target_step_id == delay1.id

    def test_get_edges_to(self):
        flow = Flow(name="Test")
        trigger1 = TriggerWebhook(config=TriggerWebhookConfig(path="/test1"))
        trigger2 = TriggerWebhook(config=TriggerWebhookConfig(path="/test2"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger1)
        flow.add_step(trigger2)
        flow.add_step(delay)
        flow.add_edge(trigger1, delay)
        flow.add_edge(trigger2, delay)

        edges = flow.get_edges_to(delay.id)
        assert len(edges) == 2

    def test_get_trigger_steps(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay = StepDelay(config=StepDelayConfig(seconds=1))

        flow.add_step(trigger)
        flow.add_step(delay)

        triggers = flow.get_trigger_steps()
        assert len(triggers) == 1
        assert triggers[0] == trigger

    def test_steps_before(self):
        flow = Flow(name="Test")
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        delay1 = StepDelay(config=StepDelayConfig(seconds=1))
        delay2 = StepDelay(config=StepDelayConfig(seconds=2))

        flow.add_step(trigger)
        flow.add_step(delay1)
        flow.add_step(delay2)
        flow.add_edge(trigger, delay1)
        flow.add_edge(delay1, delay2)

        # delay2's predecessors should be delay1 and trigger
        before = flow.steps_before(delay2)
        step_ids = {s.id for s in before}

        assert trigger.id in step_ids
        assert delay1.id in step_ids
        assert delay2.id not in step_ids
