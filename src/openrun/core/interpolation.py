"""Interpolation support for step configuration.

This module provides the Interpolated[T] type marker and resolution functions
for replacing {{ref}} patterns with actual state values.
"""

import re
from typing import Annotated, Any, TypeVar, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from openrun.core.state import StateContainer

T = TypeVar("T")


class InterpolatedMarker:
    """Marker class to identify Interpolated fields in type annotations."""

    pass


# Type alias using Annotated - indicates a field supports {{ref}} syntax
# At runtime, the value is just T (a plain string, int, etc.), not a wrapper
Interpolated = Annotated[T, InterpolatedMarker()]

# Pattern to match {{path.to.value}} references
REF_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


def is_interpolated_field(annotation: Any) -> bool:
    """Check if a type annotation is Interpolated[T]."""
    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        return any(isinstance(arg, InterpolatedMarker) for arg in args[1:])
    return False


def get_interpolated_target_type(annotation: Any) -> type:
    """Extract the target type T from Interpolated[T]."""
    if is_interpolated_field(annotation):
        # Annotated[T, InterpolatedMarker()] -> T is first arg
        return get_args(annotation)[0]
    return annotation


def resolve_template(template: str, state: StateContainer) -> str:
    """Replace {{path.to.value}} patterns with actual state values.

    Supports:
    - Simple references: {{user_id}} -> state.get("user_id")
    - Nested access: {{user.profile.email}} -> state.get_nested("user.profile.email")
    - Array indices: {{items.0.name}} -> state.get_nested("items.0.name")
    """
    if not isinstance(template, str):
        return template

    def replace_ref(match: re.Match) -> str:
        path = match.group(1).strip()
        value = state.get_nested(path)
        if value is None:
            # Return empty string for missing refs
            return ""
        if isinstance(value, (dict, list)):
            import json

            return json.dumps(value)
        return str(value)

    return REF_PATTERN.sub(replace_ref, template)


def cast_to_type(value: str, target_type: type) -> Any:
    """Cast a string value to the target type."""
    if target_type is str:
        return value
    elif target_type is int:
        return int(value) if value else 0
    elif target_type is float:
        return float(value) if value else 0.0
    elif target_type is bool:
        return value.lower() in ("true", "1", "yes") if value else False
    # For complex types (dict, list), try JSON parsing
    elif target_type in (dict, list):
        import json

        return json.loads(value) if value else (target_type())
    # Default: return as-is
    return value


def resolve_value(value: Any, state: StateContainer, target_type: type) -> Any:
    """Resolve a single value, handling interpolation if it's a string with refs."""
    if isinstance(value, str) and "{{" in value:
        resolved = resolve_template(value, state)
        return cast_to_type(resolved, target_type)
    return value


def resolve_dict_values(d: dict[str, Any], state: StateContainer) -> dict[str, Any]:
    """Resolve all string values in a dictionary that contain {{refs}}."""
    result = {}
    for key, value in d.items():
        if isinstance(value, str) and "{{" in value:
            result[key] = resolve_template(value, state)
        elif isinstance(value, dict):
            result[key] = resolve_dict_values(value, state)
        else:
            result[key] = value
    return result


def resolve_config(config: BaseModel, state: StateContainer) -> BaseModel:
    """Create a new config instance with all Interpolated fields resolved.

    Walks the config's type hints, finds Interpolated fields,
    resolves {{refs}}, casts to target type, returns new config instance.

    The step's run() method receives the resolved config - no interpolation
    needed during step execution.
    """
    try:
        hints = get_type_hints(config.__class__, include_extras=True)
    except Exception:
        # If type hints fail, return config as-is
        return config

    resolved_values = {}

    for field_name in config.model_fields:
        value = getattr(config, field_name)
        annotation = hints.get(field_name)

        if annotation and is_interpolated_field(annotation):
            target_type = get_interpolated_target_type(annotation)
            resolved_values[field_name] = resolve_value(value, state, target_type)
        elif isinstance(value, dict):
            # Handle dict[str, Interpolated[str]] or nested dicts
            resolved_values[field_name] = resolve_dict_values(value, state)
        elif isinstance(value, list):
            # Handle lists that might contain interpolated strings
            resolved_list = []
            for item in value:
                if isinstance(item, str) and "{{" in item:
                    resolved_list.append(resolve_template(item, state))
                elif isinstance(item, BaseModel):
                    resolved_list.append(resolve_config(item, state))
                else:
                    resolved_list.append(item)
            resolved_values[field_name] = resolved_list
        elif isinstance(value, BaseModel):
            # Recursively resolve nested config models
            resolved_values[field_name] = resolve_config(value, state)
        else:
            resolved_values[field_name] = value

    return config.__class__(**resolved_values)


def extract_refs(config: BaseModel) -> list[tuple[str, str]]:
    """Extract all {{ref}} patterns from a config's Interpolated fields.

    Returns a list of (field_name, ref) tuples for validation purposes.
    """
    refs: list[tuple[str, str]] = []

    try:
        hints = get_type_hints(config.__class__, include_extras=True)
    except Exception:
        return refs

    for field_name in config.model_fields:
        value = getattr(config, field_name)
        annotation = hints.get(field_name)

        if annotation and is_interpolated_field(annotation):
            if isinstance(value, str):
                for match in REF_PATTERN.finditer(value):
                    refs.append((field_name, match.group(1).strip()))
        elif isinstance(value, dict):
            for v in value.values():
                if isinstance(v, str):
                    for match in REF_PATTERN.finditer(v):
                        refs.append((field_name, match.group(1).strip()))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    for match in REF_PATTERN.finditer(item):
                        refs.append((field_name, match.group(1).strip()))
                elif isinstance(item, BaseModel):
                    refs.extend(extract_refs(item))
        elif isinstance(value, BaseModel):
            refs.extend(extract_refs(value))

    return refs
