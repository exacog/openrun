"""Flow execution runner with concurrent execution support."""

import asyncio
import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from openrun.core.interpolation import resolve_config
from openrun.core.state import StateContainer
from openrun.core.types import JoinMode, StepRunStatus
from openrun.events import (
    Event,
    FlowCompleted,
    FlowStarted,
    StepCompleted,
    StepStarted,
)
from openrun.flow.edge import Edge
from openrun.steps.base import Step, StepRunResult

if TYPE_CHECKING:
    from openrun.flow.flow import Flow


@dataclass
class JoinTracker:
    """Tracks incoming edge completions for join semantics.

    When a step has multiple incoming edges, the JoinTracker keeps
    track of which edges have completed and their results, allowing
    the runner to determine when the step should execute based on
    its join_mode.
    """

    arrivals: dict[UUID, StepRunResult] = field(default_factory=dict)

    def record(self, result: StepRunResult, edge: Edge) -> None:
        """Record that an edge has completed with a result."""
        self.arrivals[edge.source_step_id] = result

    def is_ready(self, join_mode: JoinMode, incoming_edges: list[Edge]) -> bool:
        """Check if the step is ready to execute based on join mode.

        Args:
            join_mode: How to handle multiple incoming edges
            incoming_edges: All edges pointing to this step

        Returns:
            True if the step should execute
        """
        expected_sources = {e.source_step_id for e in incoming_edges}
        arrived_sources = set(self.arrivals.keys())

        if join_mode == JoinMode.NO_WAIT:
            # Execute on any arrival
            return len(self.arrivals) > 0

        elif join_mode == JoinMode.ALL_SUCCESS:
            # Wait for all to arrive, and all must succeed
            if arrived_sources != expected_sources:
                return False
            return all(
                r.status == StepRunStatus.SUCCESS for r in self.arrivals.values()
            )

        elif join_mode == JoinMode.ALL_DONE:
            # Wait for all regardless of success/failure
            return arrived_sources == expected_sources

        elif join_mode == JoinMode.FIRST_SUCCESS:
            # Execute when first success arrives
            return any(
                r.status == StepRunStatus.SUCCESS for r in self.arrivals.values()
            )

        return False


async def execute_step(
    step: Step, state: StateContainer, resolved_config: Any
) -> StepRunResult:
    """Execute a single step with error handling.

    Args:
        step: The step to execute
        state: Current state container
        resolved_config: Config with all {{refs}} already resolved

    Returns:
        StepRunResult from the step's run() method
    """
    try:
        return await step.run(state, resolved_config)
    except Exception as e:
        return StepRunResult.failure(
            step_id=step.id,
            message=f"Step execution failed: {e}",
            code="EXECUTION_ERROR",
            details={"exception_type": type(e).__name__},
        )


async def run_flow(
    flow: "Flow",
    trigger_step_id: UUID,
    initial_state: StateContainer | None = None,
) -> AsyncGenerator[Event, None]:
    """Execute a flow with concurrent fan-out and join semantics.

    This is the main execution engine for flows. It:
    1. Starts from the trigger step
    2. Executes steps concurrently when multiple edges fan out
    3. Respects join modes when edges converge
    4. Resolves {{refs}} in config before each step runs
    5. Yields events throughout execution

    Args:
        flow: The flow to execute
        trigger_step_id: ID of the trigger step to start from
        initial_state: Optional initial state container

    Yields:
        Events: FlowStarted, StepStarted, StepCompleted, FlowCompleted
    """
    run_id = uuid4()
    state = initial_state or StateContainer()

    # Track execution state
    pending: set[UUID] = {trigger_step_id}
    running: dict[UUID, asyncio.Task] = {}
    join_trackers: defaultdict[UUID, JoinTracker] = defaultdict(JoinTracker)
    results: list[StepRunResult] = []
    step_start_times: dict[UUID, float] = {}

    yield FlowStarted(run_id=run_id, flow_name=flow.name)

    while pending or running:
        # Launch ready steps
        steps_to_launch: list[UUID] = []

        for step_id in list(pending):
            step = flow.get_step(step_id)
            if step is None:
                pending.discard(step_id)
                continue

            # Check join conditions
            incoming_edges = flow.get_edges_to(step_id)
            if incoming_edges and step.join_mode != JoinMode.NO_WAIT:
                tracker = join_trackers[step_id]
                if not tracker.is_ready(step.join_mode, incoming_edges):
                    continue

            steps_to_launch.append(step_id)

        # Launch steps that are ready
        for step_id in steps_to_launch:
            pending.discard(step_id)
            step = flow.get_step(step_id)
            if step is None:
                continue

            yield StepStarted(
                run_id=run_id,
                step_id=step_id,
                step_type=step.type.value,
            )

            # Resolve config BEFORE execution
            try:
                resolved_config = resolve_config(step.config, state)
            except Exception as e:
                # Config resolution failed - create error result
                result = StepRunResult.failure(
                    step_id=step_id,
                    message=f"Config resolution failed: {e}",
                    code="CONFIG_RESOLUTION_ERROR",
                )
                results.append(result)
                yield StepCompleted(
                    run_id=run_id,
                    step_id=step_id,
                    result=result,
                    duration_ms=0,
                )
                continue

            # Record start time
            step_start_times[step_id] = time.perf_counter()

            # Create async task
            task = asyncio.create_task(
                execute_step(step, state, resolved_config),
                name=str(step_id),
            )
            running[step_id] = task

        if not running:
            break

        # Wait for any task to complete
        done, _ = await asyncio.wait(
            running.values(),
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Process completed tasks
        for task in done:
            # Get step_id from task name
            step_id = UUID(task.get_name())
            result = task.result()
            results.append(result)
            del running[step_id]

            # Calculate duration
            start_time = step_start_times.pop(step_id, time.perf_counter())
            duration_ms = (time.perf_counter() - start_time) * 1000

            yield StepCompleted(
                run_id=run_id,
                step_id=step_id,
                result=result,
                duration_ms=duration_ms,
                state_snapshot=state.values.copy(),
            )

            # Handle fire-and-forget
            if result.continue_without_waiting:
                continue

            # Route via fired ports to successor steps
            for port in result.fired_ports:
                for edge in flow.get_edges_from(step_id, port):
                    join_trackers[edge.target_step_id].record(result, edge)
                    pending.add(edge.target_step_id)

    # Determine final status
    final_status = (
        "succeeded"
        if all(r.status == StepRunStatus.SUCCESS for r in results)
        else "failed"
    )

    yield FlowCompleted(run_id=run_id, status=final_status)
