"""Edge model for connecting steps in a flow."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Edge(BaseModel):
    """Connects two steps via their ports.

    An edge routes execution from a source step's output port
    to a target step's input port.
    """

    id: UUID = Field(default_factory=uuid4)
    source_step_id: UUID
    source_port: str = "default"
    target_step_id: UUID
    target_port: str = "default"
