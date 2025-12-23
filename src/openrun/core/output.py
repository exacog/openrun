"""Output declaration model for steps."""

from pydantic import BaseModel

from openrun.core.types import StateType


class Output(BaseModel):
    """Declares a state key that a step produces.

    Steps declare their outputs via a class method, enabling:
    - UI to show available {{refs}} downstream
    - Validation to catch invalid references
    """

    key: str
    type: StateType = StateType.ANY
    description: str | None = None
