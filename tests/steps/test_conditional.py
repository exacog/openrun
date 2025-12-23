"""Tests for StepConditional."""

import pytest

from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus
from openrun.steps.execution.conditional import (
    StepConditional,
    StepConditionalConfig,
    evaluate_condition,
)


class TestEvaluateCondition:
    """Tests for the evaluate_condition function."""

    def test_equals_true(self):
        assert evaluate_condition("admin", "equals", "admin") is True

    def test_equals_false(self):
        assert evaluate_condition("user", "equals", "admin") is False

    def test_not_equals_true(self):
        assert evaluate_condition("user", "not_equals", "admin") is True

    def test_not_equals_false(self):
        assert evaluate_condition("admin", "not_equals", "admin") is False

    def test_contains_true(self):
        assert evaluate_condition("hello world", "contains", "world") is True

    def test_contains_false(self):
        assert evaluate_condition("hello world", "contains", "foo") is False

    def test_not_contains_true(self):
        assert evaluate_condition("hello world", "not_contains", "foo") is True

    def test_not_contains_false(self):
        assert evaluate_condition("hello world", "not_contains", "world") is False

    def test_greater_than_numbers(self):
        assert evaluate_condition("10", "greater_than", "5") is True
        assert evaluate_condition("5", "greater_than", "10") is False
        assert evaluate_condition("5", "greater_than", "5") is False

    def test_less_than_numbers(self):
        assert evaluate_condition("5", "less_than", "10") is True
        assert evaluate_condition("10", "less_than", "5") is False
        assert evaluate_condition("5", "less_than", "5") is False

    def test_greater_than_strings(self):
        # Falls back to string comparison if not numbers
        assert evaluate_condition("b", "greater_than", "a") is True
        assert evaluate_condition("a", "greater_than", "b") is False


@pytest.mark.asyncio(loop_scope="session")
class TestStepConditional:
    """Tests for the conditional step."""

    async def test_fires_true_port(self):
        """Test that true condition fires true port."""
        step = StepConditional(
            config=StepConditionalConfig(
                left="admin",
                operator="equals",
                right="admin",
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["true"]

    async def test_fires_false_port(self):
        """Test that false condition fires false port."""
        step = StepConditional(
            config=StepConditionalConfig(
                left="user",
                operator="equals",
                right="admin",
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["false"]

    async def test_output_data_contains_result(self):
        """Test that output_data contains condition result."""
        step = StepConditional(
            config=StepConditionalConfig(
                left="a",
                operator="equals",
                right="a",
            )
        )
        state = StateContainer()

        result = await step.run(state, step.config)

        assert result.output_data == {"condition_result": True}

    def test_ports(self):
        """Test that conditional has true and false ports."""
        step = StepConditional(
            config=StepConditionalConfig(left="a", operator="equals", right="b")
        )
        assert "true" in step.ports
        assert "false" in step.ports

    def test_info(self):
        """Test step info metadata."""
        info = StepConditional.info()
        assert info.name == "Conditional"
        assert info.category == "logic"
