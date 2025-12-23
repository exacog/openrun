"""Core type definitions for the workflow engine."""

from enum import Enum


class StateType(str, Enum):
    """Type classification for state values."""

    ANY = "any"
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class JoinMode(str, Enum):
    """Determines how a step handles multiple incoming edges."""

    NO_WAIT = "no_wait"  # Each arrival triggers independently (default)
    ALL_SUCCESS = "all_success"  # Wait for all incoming edges, fail if any fails
    ALL_DONE = "all_done"  # Wait for all regardless of success/failure
    FIRST_SUCCESS = "first_success"  # Proceed when first branch succeeds


class StepType(str, Enum):
    """Classification of step types."""

    # Triggers (entry points)
    TRIGGER_WEBHOOK = "trigger_webhook"
    TRIGGER_SCHEDULE = "trigger_schedule"
    TRIGGER_EVENT = "trigger_event"

    # Execution steps
    REQUEST = "request"
    SET_STATE = "set_state"
    CONDITIONAL = "conditional"
    TRANSFORM = "transform"
    SUB_FLOW = "sub_flow"
    DELAY = "delay"
    SWITCH = "switch"

    # Conversation steps (migrated from legacy)
    CONVERSATION_START = "conversation_start"
    USER_MESSAGE = "user_message"
    REPLY = "reply"


class StepRunStatus(str, Enum):
    """Result status of a step execution."""

    SUCCESS = "success"
    ERROR = "error"
