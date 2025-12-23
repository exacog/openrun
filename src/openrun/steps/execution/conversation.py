"""Conversation steps - entry points for conversational flows."""

from typing import ClassVar

from pydantic import BaseModel

from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class StepConversationStartConfig(BaseModel):
    """Configuration for conversation start step (empty - no config needed)."""

    pass


class StepConversationStart(Step):
    """Marks the start of a conversational flow.

    This is a trigger step that represents the beginning of a
    conversation. It has no configuration and simply passes through.

    Outputs:
    - conversation_id: Unique identifier for the conversation
    """

    type: StepType = StepType.CONVERSATION_START
    is_trigger: bool = True
    config: StepConversationStartConfig = StepConversationStartConfig()

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(
                key="conversation_id",
                type=StateType.TEXT,
                description="Conversation identifier",
            ),
        ]

    async def run(
        self, state: StateContainer, config: StepConversationStartConfig
    ) -> StepRunResult:
        # Conversation ID should be set externally before run
        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="Conversation Start",
            description="Start of a conversation flow",
            icon="chat",
            category="conversation",
            color="#4CAF50",
        )


class StepUserMessageConfig(BaseModel):
    """Configuration for user message step (empty - no config needed)."""

    pass


class StepUserMessage(Step):
    """Represents receipt of a user message in a conversation.

    This step receives user input and makes it available in state
    for subsequent processing steps.

    Outputs:
    - user_message: The user's message text
    - user_id: Identifier of the user (if available)
    """

    type: StepType = StepType.USER_MESSAGE
    config: StepUserMessageConfig = StepUserMessageConfig()

    _ports: ClassVar[list[str]] = ["default"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(
                key="user_message",
                type=StateType.TEXT,
                description="User's message text",
            ),
            Output(
                key="user_id",
                type=StateType.TEXT,
                description="User identifier",
            ),
        ]

    async def run(
        self, state: StateContainer, config: StepUserMessageConfig
    ) -> StepRunResult:
        # User message should be set externally before run
        return StepRunResult(
            step_id=self.id,
            status=StepRunStatus.SUCCESS,
            fired_ports=["default"],
        )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="User Message",
            description="Receive user message input",
            icon="user",
            category="conversation",
            color="#2196F3",
        )
