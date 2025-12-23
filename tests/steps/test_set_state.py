"""Tests for StepSetState."""

import pytest

from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus
from openrun.steps.execution.set_state import StepSetState, StepSetStateConfig


@pytest.mark.asyncio(loop_scope="session")
class TestStepSetState:
    """Tests for the set state step."""

    async def test_sets_simple_value(self):
        """Test setting a simple string value."""
        step = StepSetState(
            config=StepSetStateConfig(
                key="greeting",
                value="Hello, World!",
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["default"]
        assert state.get("greeting") == "Hello, World!"

    async def test_output_data(self):
        """Test that output_data contains the set value."""
        step = StepSetState(
            config=StepSetStateConfig(
                key="my_key",
                value="my_value",
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.output_data == {"my_key": "my_value"}

    async def test_overwrites_existing(self):
        """Test that existing values are overwritten."""
        step = StepSetState(
            config=StepSetStateConfig(
                key="counter",
                value="new_value",
            )
        )
        state = StateContainer()
        state.set("counter", "old_value")

        await step.run(state, step.config)

        assert state.get("counter") == "new_value"

    def test_ports(self):
        """Test that set_state has only default port."""
        step = StepSetState(config=StepSetStateConfig(key="x", value="y"))
        assert step.ports == ["default"]

    def test_no_outputs_declaration(self):
        """Test that StepSetState doesn't declare outputs (key is user-defined)."""
        outputs = StepSetState.outputs()
        assert outputs == []

    def test_info(self):
        """Test step info metadata."""
        info = StepSetState.info()
        assert info.name == "Set State"
        assert info.category == "utility"
