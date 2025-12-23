"""Flow class - container for steps and edges."""

from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from openrun.core.state import StateContainer
from openrun.flow.edge import Edge
from openrun.steps.base import Step, StepRunResult

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from openrun.events import Event


class FlowRunResult(BaseModel):
    """Result of a complete flow execution."""

    status: str  # "succeeded" or "failed"
    step_results: list[StepRunResult]
    final_state: StateContainer


class Flow(BaseModel):
    """A container holding steps and the edges that connect them.

    Flows represent directed graphs where steps are nodes and edges
    define execution paths between them.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str | None = None
    steps: list[Step] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)

    # Index for fast step lookup (not serialized)
    _step_index: dict[UUID, Step] = {}

    def model_post_init(self, __context: Any) -> None:
        """Build step index after initialization."""
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the step lookup index."""
        self._step_index = {step.id: step for step in self.steps}

    def add_step(self, step: Step) -> None:
        """Add a step to the flow."""
        self.steps.append(step)
        self._step_index[step.id] = step

    def add_edge(
        self,
        source: Step | UUID,
        target: Step | UUID,
        source_port: str = "default",
        target_port: str = "default",
    ) -> Edge:
        """Connect two steps. Returns the created edge.

        Args:
            source: Source step or its ID
            target: Target step or its ID
            source_port: Output port on source step
            target_port: Input port on target step

        Returns:
            The created Edge

        Raises:
            ValueError: If source port doesn't exist on source step
        """
        source_id = source.id if isinstance(source, Step) else source
        target_id = target.id if isinstance(target, Step) else target

        # Validate source step and port exist
        source_step = self.get_step(source_id)
        if source_step is None:
            raise ValueError(f"Source step {source_id} not found in flow")
        if source_port not in source_step.ports:
            raise ValueError(
                f"Port '{source_port}' not found on step. "
                f"Available ports: {source_step.ports}"
            )

        # Validate target step exists
        if self.get_step(target_id) is None:
            raise ValueError(f"Target step {target_id} not found in flow")

        edge = Edge(
            source_step_id=source_id,
            source_port=source_port,
            target_step_id=target_id,
            target_port=target_port,
        )
        self.edges.append(edge)
        return edge

    def get_step(self, step_id: UUID) -> Step | None:
        """Find a step by ID."""
        return self._step_index.get(step_id)

    def get_edges_from(self, step_id: UUID, port: str | None = None) -> list[Edge]:
        """Get all edges originating from a step.

        Args:
            step_id: ID of the source step
            port: Optionally filter by source port

        Returns:
            List of matching edges
        """
        edges = [e for e in self.edges if e.source_step_id == step_id]
        if port is not None:
            edges = [e for e in edges if e.source_port == port]
        return edges

    def get_edges_to(self, step_id: UUID) -> list[Edge]:
        """Get all edges targeting a step."""
        return [e for e in self.edges if e.target_step_id == step_id]

    def get_trigger_steps(self) -> list[Step]:
        """Get all steps that are triggers (entry points)."""
        return [step for step in self.steps if step.is_trigger]

    def steps_before(self, step: Step) -> list[Step]:
        """Get all steps that execute before a given step.

        Uses BFS to find all upstream steps.
        """
        visited: set[UUID] = set()
        result: list[Step] = []

        # Start from all edges pointing to this step
        queue = [e.source_step_id for e in self.get_edges_to(step.id)]

        while queue:
            step_id = queue.pop(0)
            if step_id in visited:
                continue
            visited.add(step_id)

            upstream_step = self.get_step(step_id)
            if upstream_step:
                result.append(upstream_step)
                # Add this step's predecessors to queue
                queue.extend(e.source_step_id for e in self.get_edges_to(step_id))

        return result

    async def run(
        self,
        trigger_step: Step | UUID,
        initial_state: StateContainer | None = None,
    ) -> "AsyncGenerator[Event, None]":
        """Execute the flow starting from a trigger step.

        Args:
            trigger_step: The trigger step or its ID to start from
            initial_state: Optional initial state container

        Yields:
            Events during execution (FlowStarted, StepStarted, etc.)

        Returns:
            FlowRunResult with final state and step results
        """
        from openrun.flow.runner import run_flow

        trigger_id = trigger_step.id if isinstance(trigger_step, Step) else trigger_step
        async for event in run_flow(self, trigger_id, initial_state):
            yield event
