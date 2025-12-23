"""Tests for StepDelay."""

import pytest
from unittest.mock import patch, AsyncMock

from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus
from openrun.steps.execution.delay import StepDelay, StepDelayConfig


@pytest.mark.asyncio(loop_scope="session")
class TestStepDelay:
    """Tests for the delay step."""

    async def test_execute_with_default_seconds(self):
        """Test delay with default 1 second."""
        step = StepDelay(config=StepDelayConfig())
        state = StateContainer()

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await step.run(state, step.config)

        mock_sleep.assert_awaited_once_with(1.0)
        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["default"]
        assert result.output_data == {"delayed_seconds": 1.0}

    async def test_execute_with_custom_seconds(self):
        """Test delay with custom duration."""
        step = StepDelay(config=StepDelayConfig(seconds=0.5))
        state = StateContainer()

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await step.run(state, step.config)

        mock_sleep.assert_awaited_once_with(0.5)
        assert result.status == StepRunStatus.SUCCESS
        assert result.output_data == {"delayed_seconds": 0.5}

    async def test_execute_with_zero_seconds(self):
        """Test delay with zero duration."""
        step = StepDelay(config=StepDelayConfig(seconds=0))
        state = StateContainer()

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await step.run(state, step.config)

        mock_sleep.assert_awaited_once_with(0)
        assert result.status == StepRunStatus.SUCCESS

    async def test_updates_state(self):
        """Test that delay updates state with delayed_seconds."""
        step = StepDelay(config=StepDelayConfig(seconds=2.5))
        state = StateContainer()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await step.run(state, step.config)

        assert state.get("delayed_seconds") == 2.5

    def test_outputs_declaration(self):
        """Test that outputs are correctly declared."""
        outputs = StepDelay.outputs()
        assert len(outputs) == 1
        assert outputs[0].key == "delayed_seconds"

    def test_info(self):
        """Test step info metadata."""
        info = StepDelay.info()
        assert info.name == "Delay"
        assert info.category == "utility"

    def test_ports(self):
        """Test that delay has only default port."""
        step = StepDelay(config=StepDelayConfig())
        assert step.ports == ["default"]
