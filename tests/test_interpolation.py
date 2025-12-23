"""Tests for interpolation and config resolution."""

from pydantic import BaseModel

from openrun.core.interpolation import (
    Interpolated,
    extract_refs,
    is_interpolated_field,
    resolve_config,
    resolve_template,
)
from openrun.core.state import StateContainer


class TestResolveTemplate:
    """Tests for resolve_template function."""

    def test_simple_ref(self, state_with_data: StateContainer):
        result = resolve_template("Hello {{user.name}}", state_with_data)
        assert result == "Hello Alice"

    def test_multiple_refs(self, state_with_data: StateContainer):
        result = resolve_template(
            "User {{user.name}} has {{count}} items",
            state_with_data,
        )
        assert result == "User Alice has 5 items"

    def test_nested_ref(self, state_with_data: StateContainer):
        result = resolve_template("Email: {{user.profile.email}}", state_with_data)
        assert result == "Email: alice@example.com"

    def test_array_index_ref(self, state_with_data: StateContainer):
        result = resolve_template("First item: {{items.0.name}}", state_with_data)
        assert result == "First item: Item1"

    def test_missing_ref(self, state_with_data: StateContainer):
        # Missing refs become empty strings
        result = resolve_template("Value: {{missing.key}}", state_with_data)
        assert result == "Value: "

    def test_no_refs(self, state: StateContainer):
        result = resolve_template("Plain text", state)
        assert result == "Plain text"

    def test_object_ref_json_encoded(self, state_with_data: StateContainer):
        result = resolve_template("User: {{user}}", state_with_data)
        assert '"name": "Alice"' in result


class TestIsInterpolatedField:
    """Tests for detecting Interpolated type annotations."""

    def test_interpolated_string(self):
        assert is_interpolated_field(Interpolated[str]) is True

    def test_interpolated_int(self):
        assert is_interpolated_field(Interpolated[int]) is True

    def test_plain_string(self):
        assert is_interpolated_field(str) is False

    def test_plain_int(self):
        assert is_interpolated_field(int) is False


class TestResolveConfig:
    """Tests for resolve_config function."""

    def test_resolve_simple_config(self, state_with_data: StateContainer):
        class Config(BaseModel):
            message: Interpolated[str]
            count: int = 10

        config = Config(message="Hello {{user.name}}", count=5)
        resolved = resolve_config(config, state_with_data)

        assert resolved.message == "Hello Alice"
        assert resolved.count == 5

    def test_resolve_nested_refs(self, state_with_data: StateContainer):
        class Config(BaseModel):
            email: Interpolated[str]

        config = Config(email="{{user.profile.email}}")
        resolved = resolve_config(config, state_with_data)

        assert resolved.email == "alice@example.com"

    def test_resolve_dict_values(self, state_with_data: StateContainer):
        class Config(BaseModel):
            headers: dict[str, str]

        config = Config(headers={"X-User": "{{user.name}}", "X-Count": "{{count}}"})
        resolved = resolve_config(config, state_with_data)

        assert resolved.headers["X-User"] == "Alice"
        assert resolved.headers["X-Count"] == "5"

    def test_resolve_preserves_non_interpolated(self, state: StateContainer):
        class Config(BaseModel):
            url: str
            timeout: int

        config = Config(url="https://example.com", timeout=30)
        resolved = resolve_config(config, state)

        assert resolved.url == "https://example.com"
        assert resolved.timeout == 30


class TestExtractRefs:
    """Tests for extracting refs from configs."""

    def test_extract_simple_refs(self):
        class Config(BaseModel):
            message: Interpolated[str]

        config = Config(message="Hello {{user.name}}")
        refs = extract_refs(config)

        assert ("message", "user.name") in refs

    def test_extract_multiple_refs(self):
        class Config(BaseModel):
            template: Interpolated[str]

        config = Config(template="{{user.name}} has {{count}} items")
        refs = extract_refs(config)

        assert ("template", "user.name") in refs
        assert ("template", "count") in refs

    def test_extract_no_refs(self):
        class Config(BaseModel):
            static: str

        config = Config(static="no refs here")
        refs = extract_refs(config)

        assert refs == []

    def test_extract_dict_refs(self):
        class Config(BaseModel):
            headers: dict[str, str]

        config = Config(headers={"Authorization": "Bearer {{token}}"})
        refs = extract_refs(config)

        assert ("headers", "token") in refs
