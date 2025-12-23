"""Flow validation for state references."""

from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import BaseModel

from openrun.core.interpolation import extract_refs
from openrun.steps.base import Step

if TYPE_CHECKING:
    from openrun.flow.flow import Flow


class ValidationError(BaseModel):
    """Error from flow validation."""

    step_id: UUID
    field: str
    reference: str
    message: str
    level: Literal["error", "warning"] = "error"


def get_available_keys_before(flow: "Flow", step: Step) -> set[str]:
    """Get all state keys available before a step executes.

    Computes the set of state keys that are available for reference
    in a step's config based on:
    - Declared outputs from upstream steps
    - User-defined keys from StepSetState configs

    Args:
        flow: The flow containing the step
        step: The step to check availability for

    Returns:
        Set of available state key names
    """
    keys: set[str] = set()

    for upstream in flow.steps_before(step):
        # Add declared outputs from the step class
        for output in upstream.outputs():
            keys.add(output.key)

        # Handle StepSetState (user-defined keys)
        if hasattr(upstream.config, "key") and upstream.config.key:
            keys.add(upstream.config.key)

    return keys


def validate_flow(flow: "Flow") -> list[ValidationError]:
    """Validate all state references in a flow.

    Checks that all {{ref}} patterns in step configs reference
    state keys that are available at that point in the flow.

    Args:
        flow: The flow to validate

    Returns:
        List of validation errors found
    """
    errors: list[ValidationError] = []

    for step in flow.steps:
        available_keys = get_available_keys_before(flow, step)

        # For trigger steps, they define their own outputs but don't
        # have upstream refs to check - they set initial state
        if step.is_trigger:
            # Add trigger's own outputs since they're available during execution
            for output in step.outputs():
                available_keys.add(output.key)

        # Extract all refs from config
        refs = extract_refs(step.config)

        for field_name, ref in refs:
            # Get the root key (e.g., "user" from "user.name")
            root_key = ref.split(".")[0]

            if root_key not in available_keys:
                errors.append(
                    ValidationError(
                        step_id=step.id,
                        field=field_name,
                        reference=ref,
                        message=f"'{ref}' not found. Available: {sorted(available_keys)}",
                    )
                )

    return errors


def validate_edges(flow: "Flow") -> list[ValidationError]:
    """Validate all edges in a flow.

    Checks that:
    - Source ports exist on source steps
    - Source and target steps exist in the flow

    Args:
        flow: The flow to validate

    Returns:
        List of validation errors found
    """
    errors: list[ValidationError] = []

    for edge in flow.edges:
        source_step = flow.get_step(edge.source_step_id)
        target_step = flow.get_step(edge.target_step_id)

        if source_step is None:
            errors.append(
                ValidationError(
                    step_id=edge.source_step_id,
                    field="edge",
                    reference=str(edge.id),
                    message=f"Source step {edge.source_step_id} not found",
                )
            )
            continue

        if target_step is None:
            errors.append(
                ValidationError(
                    step_id=edge.target_step_id,
                    field="edge",
                    reference=str(edge.id),
                    message=f"Target step {edge.target_step_id} not found",
                )
            )
            continue

        if edge.source_port not in source_step.ports:
            errors.append(
                ValidationError(
                    step_id=edge.source_step_id,
                    field="source_port",
                    reference=edge.source_port,
                    message=f"Port '{edge.source_port}' not found. "
                    f"Available: {source_step.ports}",
                )
            )

    return errors


def validate_triggers(flow: "Flow") -> list[ValidationError]:
    """Validate that flow has at least one trigger step.

    Args:
        flow: The flow to validate

    Returns:
        List of validation errors (warning level)
    """
    errors: list[ValidationError] = []

    triggers = flow.get_trigger_steps()
    if not triggers:
        # Use first step ID if available, otherwise a nil UUID
        step_id = flow.steps[0].id if flow.steps else UUID(int=0)
        errors.append(
            ValidationError(
                step_id=step_id,
                field="flow",
                reference="triggers",
                message="Flow has no trigger steps",
                level="warning",
            )
        )

    return errors


def validate_all(flow: "Flow") -> list[ValidationError]:
    """Run all validations on a flow.

    Args:
        flow: The flow to validate

    Returns:
        Combined list of all validation errors
    """
    errors: list[ValidationError] = []
    errors.extend(validate_flow(flow))
    errors.extend(validate_edges(flow))
    errors.extend(validate_triggers(flow))
    return errors
