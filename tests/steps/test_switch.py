"""Tests for StepSwitch."""

import pytest

from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus
from openrun.steps.execution.switch import StepSwitch, StepSwitchConfig, Case


@pytest.mark.asyncio(loop_scope="session")
class TestStepSwitch:
    """Tests for the switch step with dynamic ports."""

    async def test_matches_first_case(self):
        """Test matching the first case."""
        step = StepSwitch(
            config=StepSwitchConfig(
                value="premium",
                cases=[
                    Case(name="premium", value="premium"),
                    Case(name="pro", value="pro"),
                    Case(name="free", value="free"),
                ],
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["premium"]
        assert result.output_data == {"matched_case": "premium"}

    async def test_matches_middle_case(self):
        """Test matching a middle case."""
        step = StepSwitch(
            config=StepSwitchConfig(
                value="pro",
                cases=[
                    Case(name="premium", value="premium"),
                    Case(name="pro", value="pro"),
                    Case(name="free", value="free"),
                ],
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.fired_ports == ["pro"]

    async def test_no_match_fires_else(self):
        """Test that no match fires else port."""
        step = StepSwitch(
            config=StepSwitchConfig(
                value="unknown",
                cases=[
                    Case(name="premium", value="premium"),
                    Case(name="pro", value="pro"),
                ],
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.fired_ports == ["else"]
        assert result.output_data == {"matched_case": None}

    def test_dynamic_ports(self):
        """Test that ports are derived from cases."""
        step = StepSwitch(
            config=StepSwitchConfig(
                value="test",
                cases=[
                    Case(name="option_a", value="a"),
                    Case(name="option_b", value="b"),
                    Case(name="option_c", value="c"),
                ],
            )
        )

        ports = step.ports
        assert "option_a" in ports
        assert "option_b" in ports
        assert "option_c" in ports
        assert "else" in ports
        assert len(ports) == 4

    def test_empty_cases_only_else(self):
        """Test that empty cases only has else port."""
        step = StepSwitch(
            config=StepSwitchConfig(
                value="test",
                cases=[],
            )
        )

        assert step.ports == ["else"]

    def test_info(self):
        """Test step info metadata."""
        info = StepSwitch.info()
        assert info.name == "Switch"
        assert info.category == "logic"
