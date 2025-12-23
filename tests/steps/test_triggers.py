"""Tests for trigger steps."""

import pytest

from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus
from openrun.steps.triggers.webhook import TriggerWebhook, TriggerWebhookConfig
from openrun.steps.triggers.schedule import TriggerSchedule, TriggerScheduleConfig
from openrun.steps.triggers.event import TriggerEvent, TriggerEventConfig


@pytest.mark.asyncio(loop_scope="session")
class TestTriggerWebhook:
    """Tests for the webhook trigger."""

    async def test_fires_default_port(self):
        """Test that webhook trigger fires default port."""
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        state = StateContainer()

        result = await trigger.run(state, trigger.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["default"]

    def test_is_trigger(self):
        """Test that webhook is marked as trigger."""
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        assert trigger.is_trigger is True

    def test_outputs_declared(self):
        """Test webhook declares expected outputs."""
        outputs = TriggerWebhook.outputs()
        keys = [o.key for o in outputs]

        assert "body" in keys
        assert "headers" in keys
        assert "method" in keys
        assert "query" in keys

    def test_output_types(self):
        """Test webhook output types."""
        outputs = TriggerWebhook.outputs()
        output_dict = {o.key: o for o in outputs}

        assert output_dict["body"].type == StateType.ANY
        assert output_dict["headers"].type == StateType.OBJECT
        assert output_dict["method"].type == StateType.TEXT
        assert output_dict["query"].type == StateType.OBJECT

    def test_ports(self):
        """Test that webhook has only default port."""
        trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/test"))
        assert trigger.ports == ["default"]

    def test_info(self):
        """Test step info metadata."""
        info = TriggerWebhook.info()
        assert info.name == "Webhook"
        assert info.category == "triggers"


@pytest.mark.asyncio(loop_scope="session")
class TestTriggerSchedule:
    """Tests for the schedule trigger."""

    async def test_fires_default_port(self):
        """Test that schedule trigger fires default port."""
        trigger = TriggerSchedule(config=TriggerScheduleConfig(cron="0 * * * *"))
        state = StateContainer()

        result = await trigger.run(state, trigger.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["default"]

    def test_is_trigger(self):
        """Test that schedule is marked as trigger."""
        trigger = TriggerSchedule(config=TriggerScheduleConfig(cron="0 * * * *"))
        assert trigger.is_trigger is True

    def test_outputs_declared(self):
        """Test schedule declares expected outputs."""
        outputs = TriggerSchedule.outputs()
        keys = [o.key for o in outputs]

        assert "scheduled_time" in keys
        assert "actual_time" in keys

    def test_default_timezone(self):
        """Test that schedule has UTC as default timezone."""
        trigger = TriggerSchedule(config=TriggerScheduleConfig(cron="0 * * * *"))
        assert trigger.config.timezone == "UTC"

    def test_info(self):
        """Test step info metadata."""
        info = TriggerSchedule.info()
        assert info.name == "Schedule"
        assert info.category == "triggers"


@pytest.mark.asyncio(loop_scope="session")
class TestTriggerEvent:
    """Tests for the event trigger."""

    async def test_fires_default_port(self):
        """Test that event trigger fires default port."""
        trigger = TriggerEvent(config=TriggerEventConfig(event_name="user.created"))
        state = StateContainer()

        result = await trigger.run(state, trigger.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["default"]

    def test_is_trigger(self):
        """Test that event is marked as trigger."""
        trigger = TriggerEvent(config=TriggerEventConfig(event_name="user.created"))
        assert trigger.is_trigger is True

    def test_outputs_declared(self):
        """Test event declares expected outputs."""
        outputs = TriggerEvent.outputs()
        keys = [o.key for o in outputs]

        assert "event_name" in keys
        assert "event_data" in keys
        assert "event_timestamp" in keys

    def test_info(self):
        """Test step info metadata."""
        info = TriggerEvent.info()
        assert info.name == "Event"
        assert info.category == "triggers"
