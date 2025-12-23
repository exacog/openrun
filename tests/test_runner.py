"""Tests for flow execution runner."""

import pytest
from unittest.mock import patch, AsyncMock

from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus
from openrun.events import FlowStarted, FlowCompleted, StepStarted, StepCompleted
from openrun.flow.flow import Flow
from openrun.flow.runner import run_flow, JoinTracker
from openrun.steps.execution.set_state import StepSetState, StepSetStateConfig
from openrun.steps.execution.conditional import StepConditional, StepConditionalConfig
from openrun.steps.triggers.webhook import TriggerWebhook, TriggerWebhookConfig


@pytest.mark.asyncio(loop_scope="session")
class TestRunFlow:
    """Tests for the run_flow function."""

    async def test_simple_flow_execution(self, simple_flow: Flow):
        """Test basic flow execution with trigger and delay."""
        events = []
        with patch("asyncio.sleep", new_callable=AsyncMock):
            async for event in run_flow(
                simple_flow, simple_flow.get_trigger_steps()[0].id
            ):
                events.append(event)

        # Should have FlowStarted, 2x StepStarted, 2x StepCompleted, FlowCompleted
        assert any(isinstance(e, FlowStarted) for e in events)
        assert any(isinstance(e, FlowCompleted) for e in events)
        assert len([e for e in events if isinstance(e, StepStarted)]) == 2
        assert len([e for e in events if isinstance(e, StepCompleted)]) == 2

        # Final status should be succeeded
        completed = next(e for e in events if isinstance(e, FlowCompleted))
        assert completed.status == "succeeded"

    async def test_flow_with_state(self):
        """Test flow that uses state."""
        flow = Flow(name="State Test")

        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        set_state = StepSetState(
            config=StepSetStateConfig(
                key="greeting",
                value="Hello, World!",
            )
        )

        flow.add_step(trigger)
        flow.add_step(set_state)
        flow.add_edge(trigger, set_state)

        state = StateContainer()
        events = []
        async for event in run_flow(flow, trigger.id, state):
            events.append(event)

        # State should have the value set
        assert state.get("greeting") == "Hello, World!"

    async def test_fan_out_parallel_execution(self, fan_out_flow: Flow):
        """Test that fan-out executes steps in parallel."""
        events = []
        execution_order = []

        with patch("asyncio.sleep", new_callable=AsyncMock):
            async for event in run_flow(
                fan_out_flow, fan_out_flow.get_trigger_steps()[0].id
            ):
                events.append(event)
                if isinstance(event, StepCompleted):
                    execution_order.append(event.step_id)

        # Should have completed 3 steps (trigger + 2 delays)
        completed_events = [e for e in events if isinstance(e, StepCompleted)]
        assert len(completed_events) == 3

    async def test_conditional_true_branch(self):
        """Test conditional step fires true port."""
        flow = Flow(name="Conditional Test")

        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        condition = StepConditional(
            config=StepConditionalConfig(
                left="admin",
                operator="equals",
                right="admin",
            )
        )
        true_step = StepSetState(config=StepSetStateConfig(key="branch", value="true"))
        false_step = StepSetState(
            config=StepSetStateConfig(key="branch", value="false")
        )

        flow.add_step(trigger)
        flow.add_step(condition)
        flow.add_step(true_step)
        flow.add_step(false_step)

        flow.add_edge(trigger, condition)
        flow.add_edge(condition, true_step, source_port="true")
        flow.add_edge(condition, false_step, source_port="false")

        state = StateContainer()
        async for _ in run_flow(flow, trigger.id, state):
            pass

        # Should have taken true branch
        assert state.get("branch") == "true"

    async def test_conditional_false_branch(self):
        """Test conditional step fires false port."""
        flow = Flow(name="Conditional Test")

        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        condition = StepConditional(
            config=StepConditionalConfig(
                left="user",
                operator="equals",
                right="admin",
            )
        )
        true_step = StepSetState(config=StepSetStateConfig(key="branch", value="true"))
        false_step = StepSetState(
            config=StepSetStateConfig(key="branch", value="false")
        )

        flow.add_step(trigger)
        flow.add_step(condition)
        flow.add_step(true_step)
        flow.add_step(false_step)

        flow.add_edge(trigger, condition)
        flow.add_edge(condition, true_step, source_port="true")
        flow.add_edge(condition, false_step, source_port="false")

        state = StateContainer()
        async for _ in run_flow(flow, trigger.id, state):
            pass

        # Should have taken false branch
        assert state.get("branch") == "false"

    async def test_interpolation_in_config(self):
        """Test that config values are interpolated from state."""
        flow = Flow(name="Interpolation Test")

        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        set_name = StepSetState(config=StepSetStateConfig(key="name", value="Alice"))
        greeting = StepSetState(
            config=StepSetStateConfig(
                key="greeting",
                value="Hello, {{name}}!",
            )
        )

        flow.add_step(trigger)
        flow.add_step(set_name)
        flow.add_step(greeting)

        flow.add_edge(trigger, set_name)
        flow.add_edge(set_name, greeting)

        state = StateContainer()
        async for _ in run_flow(flow, trigger.id, state):
            pass

        assert state.get("greeting") == "Hello, Alice!"


class TestJoinTracker:
    """Tests for JoinTracker join mode handling."""

    def test_no_wait_mode(self):
        from openrun.core.types import JoinMode
        from openrun.steps.base import StepRunResult
        from uuid import uuid4

        tracker = JoinTracker()
        step_id = uuid4()
        edges = [
            type("Edge", (), {"source_step_id": uuid4()})(),
            type("Edge", (), {"source_step_id": uuid4()})(),
        ]

        # Before any arrivals
        assert tracker.is_ready(JoinMode.NO_WAIT, edges) is False

        # After one arrival
        result = StepRunResult(step_id=step_id, status=StepRunStatus.SUCCESS)
        tracker.record(result, edges[0])
        assert tracker.is_ready(JoinMode.NO_WAIT, edges) is True

    def test_all_success_mode(self):
        from openrun.core.types import JoinMode
        from openrun.steps.base import StepRunResult
        from uuid import uuid4

        tracker = JoinTracker()
        source1_id = uuid4()
        source2_id = uuid4()
        edges = [
            type("Edge", (), {"source_step_id": source1_id})(),
            type("Edge", (), {"source_step_id": source2_id})(),
        ]

        # One arrival - not ready
        result1 = StepRunResult(step_id=uuid4(), status=StepRunStatus.SUCCESS)
        tracker.arrivals[source1_id] = result1
        assert tracker.is_ready(JoinMode.ALL_SUCCESS, edges) is False

        # Both arrived and succeeded - ready
        result2 = StepRunResult(step_id=uuid4(), status=StepRunStatus.SUCCESS)
        tracker.arrivals[source2_id] = result2
        assert tracker.is_ready(JoinMode.ALL_SUCCESS, edges) is True

    def test_all_success_mode_with_failure(self):
        from openrun.core.types import JoinMode
        from openrun.steps.base import StepRunResult
        from uuid import uuid4

        tracker = JoinTracker()
        source1_id = uuid4()
        source2_id = uuid4()
        edges = [
            type("Edge", (), {"source_step_id": source1_id})(),
            type("Edge", (), {"source_step_id": source2_id})(),
        ]

        # Both arrived but one failed - not ready
        result1 = StepRunResult(step_id=uuid4(), status=StepRunStatus.SUCCESS)
        result2 = StepRunResult(step_id=uuid4(), status=StepRunStatus.ERROR)
        tracker.arrivals[source1_id] = result1
        tracker.arrivals[source2_id] = result2
        assert tracker.is_ready(JoinMode.ALL_SUCCESS, edges) is False

    def test_all_done_mode(self):
        from openrun.core.types import JoinMode
        from openrun.steps.base import StepRunResult
        from uuid import uuid4

        tracker = JoinTracker()
        source1_id = uuid4()
        source2_id = uuid4()
        edges = [
            type("Edge", (), {"source_step_id": source1_id})(),
            type("Edge", (), {"source_step_id": source2_id})(),
        ]

        # Both arrived (one failed) - should be ready for ALL_DONE
        result1 = StepRunResult(step_id=uuid4(), status=StepRunStatus.SUCCESS)
        result2 = StepRunResult(step_id=uuid4(), status=StepRunStatus.ERROR)
        tracker.arrivals[source1_id] = result1
        tracker.arrivals[source2_id] = result2
        assert tracker.is_ready(JoinMode.ALL_DONE, edges) is True

    def test_first_success_mode(self):
        from openrun.core.types import JoinMode
        from openrun.steps.base import StepRunResult
        from uuid import uuid4

        tracker = JoinTracker()
        source1_id = uuid4()
        source2_id = uuid4()
        edges = [
            type("Edge", (), {"source_step_id": source1_id})(),
            type("Edge", (), {"source_step_id": source2_id})(),
        ]

        # First arrival fails - not ready
        result1 = StepRunResult(step_id=uuid4(), status=StepRunStatus.ERROR)
        tracker.arrivals[source1_id] = result1
        assert tracker.is_ready(JoinMode.FIRST_SUCCESS, edges) is False

        # Second arrival succeeds - ready
        result2 = StepRunResult(step_id=uuid4(), status=StepRunStatus.SUCCESS)
        tracker.arrivals[source2_id] = result2
        assert tracker.is_ready(JoinMode.FIRST_SUCCESS, edges) is True
