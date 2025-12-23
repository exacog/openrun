"""State management for the workflow engine."""

import json
from typing import Any

from pydantic import BaseModel, Field

from openrun.core.types import StateType


class StateSlot(BaseModel):
    """Defines a typed slot in the state container.

    Slots provide type information and casting for state values.
    """

    name: str
    type: StateType = StateType.ANY
    description: str | None = None

    def cast(self, value: Any) -> Any:
        """Coerce value to the slot's type."""
        if value is None:
            return None

        if self.type == StateType.TEXT:
            return str(value)
        elif self.type == StateType.NUMBER:
            if isinstance(value, str):
                # Try int first, then float
                try:
                    return int(value)
                except ValueError:
                    return float(value)
            return float(value)
        elif self.type == StateType.BOOLEAN:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        elif self.type == StateType.OBJECT:
            if isinstance(value, str):
                return json.loads(value)
            return value
        elif self.type == StateType.ARRAY:
            if isinstance(value, str):
                return json.loads(value)
            return value
        # StateType.ANY - return as-is
        return value


class StateContainer(BaseModel):
    """Runtime state container with typed slots.

    State flows through execution as a key-value store with optional
    type definitions for validation and casting.
    """

    slots: dict[str, StateSlot] = Field(default_factory=dict)
    values: dict[str, Any] = Field(default_factory=dict)

    def define(
        self,
        name: str,
        type: StateType = StateType.ANY,
        description: str | None = None,
    ) -> StateSlot:
        """Define a new state slot with type information."""
        slot = StateSlot(name=name, type=type, description=description)
        self.slots[name] = slot
        return slot

    def set(self, name: str, value: Any) -> None:
        """Set a value, casting to slot type if defined."""
        if name in self.slots:
            value = self.slots[name].cast(value)
        self.values[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        """Get a value by name."""
        return self.values.get(name, default)

    def get_nested(self, path: str, default: Any = None) -> Any:
        """Get a nested value using dot notation.

        Supports:
        - Simple keys: "user"
        - Nested objects: "user.profile.email"
        - Array indices: "items.0.name"
        """
        parts = path.split(".")
        current = self.values

        for part in parts:
            if current is None:
                return default

            # Try array index
            if isinstance(current, list):
                try:
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return default
                except ValueError:
                    return default
            # Try dict key
            elif isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default

        return current

    def get_as_string(self, name: str) -> str:
        """Get a value as a string (JSON-encodes objects/arrays)."""
        value = self.values.get(name)
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def copy(self) -> "StateContainer":
        """Create a shallow copy of the state container."""
        return StateContainer(
            slots=self.slots.copy(),
            values=self.values.copy(),
        )
