"""Tests for StateContainer and StateSlot."""

from openrun.core.state import StateContainer, StateSlot
from openrun.core.types import StateType


class TestStateSlot:
    """Tests for StateSlot type casting."""

    def test_cast_text(self):
        slot = StateSlot(name="test", type=StateType.TEXT)
        assert slot.cast(123) == "123"
        assert slot.cast(True) == "True"
        assert slot.cast(None) is None

    def test_cast_number_from_string(self):
        slot = StateSlot(name="test", type=StateType.NUMBER)
        assert slot.cast("42") == 42
        assert slot.cast("3.14") == 3.14
        assert slot.cast(100) == 100.0

    def test_cast_boolean(self):
        slot = StateSlot(name="test", type=StateType.BOOLEAN)
        assert slot.cast("true") is True
        assert slot.cast("false") is False
        assert slot.cast("1") is True
        assert slot.cast("yes") is True
        assert slot.cast(1) is True
        assert slot.cast(0) is False

    def test_cast_object_from_string(self):
        slot = StateSlot(name="test", type=StateType.OBJECT)
        assert slot.cast('{"key": "value"}') == {"key": "value"}
        # Dict stays as dict
        assert slot.cast({"key": "value"}) == {"key": "value"}

    def test_cast_array_from_string(self):
        slot = StateSlot(name="test", type=StateType.ARRAY)
        assert slot.cast("[1, 2, 3]") == [1, 2, 3]
        # List stays as list
        assert slot.cast([1, 2, 3]) == [1, 2, 3]

    def test_cast_any(self):
        slot = StateSlot(name="test", type=StateType.ANY)
        # ANY type returns value as-is
        assert slot.cast("hello") == "hello"
        assert slot.cast(42) == 42
        assert slot.cast({"a": 1}) == {"a": 1}


class TestStateContainer:
    """Tests for StateContainer operations."""

    def test_define_and_get(self, state: StateContainer):
        state.define("user_id", StateType.NUMBER)
        state.set("user_id", "42")
        # Should be cast to number
        assert state.get("user_id") == 42

    def test_set_without_definition(self, state: StateContainer):
        # Can set values without defining slot first
        state.set("name", "Alice")
        assert state.get("name") == "Alice"

    def test_get_with_default(self, state: StateContainer):
        assert state.get("nonexistent", "default") == "default"
        assert state.get("nonexistent") is None

    def test_get_nested_object(self, state_with_data: StateContainer):
        # Simple nested access
        assert state_with_data.get_nested("user.name") == "Alice"
        assert state_with_data.get_nested("user.profile.email") == "alice@example.com"

    def test_get_nested_array(self, state_with_data: StateContainer):
        # Array index access
        assert state_with_data.get_nested("items.0.name") == "Item1"
        assert state_with_data.get_nested("items.1.price") == 20

    def test_get_nested_missing(self, state_with_data: StateContainer):
        assert state_with_data.get_nested("user.missing", "default") == "default"
        assert state_with_data.get_nested("items.99.name", "default") == "default"
        assert state_with_data.get_nested("nonexistent.path") is None

    def test_get_as_string_primitives(self, state_with_data: StateContainer):
        assert state_with_data.get_as_string("count") == "5"
        assert state_with_data.get_as_string("message") == "Hello, World!"

    def test_get_as_string_complex(self, state_with_data: StateContainer):
        # Objects/arrays get JSON-encoded
        user_str = state_with_data.get_as_string("user")
        assert '"name": "Alice"' in user_str
        assert '"id": 42' in user_str

    def test_get_as_string_missing(self, state: StateContainer):
        assert state.get_as_string("missing") == ""

    def test_copy(self, state_with_data: StateContainer):
        copy = state_with_data.copy()
        # Should have same values
        assert copy.get("user") == state_with_data.get("user")
        # But be independent
        copy.set("user", {"name": "Bob"})
        assert state_with_data.get("user")["name"] == "Alice"
