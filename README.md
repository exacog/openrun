# OpenRun

A flexible, LLM-agnostic engine for orchestrating AI agents and complex conversational automation behind the firewall.

## Installation

```bash
pip install openrun
```

## Quick Start

See [`examples/basic_flow.py`](examples/basic_flow.py) for a complete working example.

## Overview

```python
import asyncio
from openrun import Flow, TriggerWebhook, StepRequest, StepSetState
from openrun.steps.triggers.webhook import TriggerWebhookConfig
from openrun.steps.execution.request import StepRequestConfig
from openrun.steps.execution.set_state import StepSetStateConfig

# Create a flow
flow = Flow(name="Fetch Data")

# Define steps
trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/fetch"))
fetch = StepRequest(config=StepRequestConfig(
    url="https://api.example.com/data",
    method="GET"
))
store = StepSetState(config=StepSetStateConfig(
    key="result",
    value="{{response.body}}"
))

# Add steps and connect them
flow.add_step(trigger)
flow.add_step(fetch)
flow.add_step(store)
flow.add_edge(trigger, fetch)
flow.add_edge(fetch, store)

# Run the flow
async def main():
    async for event in flow.run(trigger_step=trigger):
        print(event)

asyncio.run(main())
```

## Core Concepts

### Flows

A `Flow` is a directed graph of steps connected by edges. Steps execute in order based on edge connections.

```python
from openrun import Flow

flow = Flow(name="My Workflow")
```

### Steps

Steps are the execution units. Each step has:
- A **config** defining its behavior
- **Ports** for branching (default: `["default"]`)
- A **run()** method that executes the step logic

### Edges

Edges connect steps via ports:

```python
flow.add_edge(step_a, step_b)  # default -> default
flow.add_edge(step_a, step_b, source_port="success")  # success -> default
```

### State

`StateContainer` holds data that flows between steps. Steps read from and write to state.

```python
from openrun import StateContainer

state = StateContainer()
state.set("user_id", "123")
state.get("user_id")  # "123"
state.get_nested("user.profile.email")  # nested access
```

## Interpolation

Use `{{path}}` syntax to reference state values in step configs:

```python
from openrun.steps.execution.set_state import StepSetStateConfig

StepSetState(config=StepSetStateConfig(
    key="greeting",
    value="Hello, {{user.name}}!"  # Resolves from state
))
```

Supports:
- Simple refs: `{{user_id}}`
- Nested paths: `{{user.profile.email}}`
- Array indices: `{{items.0.name}}`

## Built-in Steps

### Triggers

Entry points for flow execution:

```python
from openrun import TriggerWebhook, TriggerSchedule, TriggerEvent
from openrun.steps.triggers.webhook import TriggerWebhookConfig
from openrun.steps.triggers.schedule import TriggerScheduleConfig
from openrun.steps.triggers.event import TriggerEventConfig

# Webhook trigger
TriggerWebhook(config=TriggerWebhookConfig(path="/api/start"))

# Schedule trigger (cron)
TriggerSchedule(config=TriggerScheduleConfig(cron="0 9 * * *"))

# Event trigger
TriggerEvent(config=TriggerEventConfig(event_type="user.created"))
```

### StepRequest

Make HTTP requests:

```python
from openrun import StepRequest
from openrun.steps.execution.request import StepRequestConfig

step = StepRequest(config=StepRequestConfig(
    url="https://api.example.com/users/{{user_id}}",
    method="POST",
    headers={"Authorization": "Bearer {{token}}"},
    body={"name": "{{name}}"}
))
```

### StepSetState

Store values in state:

```python
from openrun import StepSetState
from openrun.steps.execution.set_state import StepSetStateConfig

step = StepSetState(config=StepSetStateConfig(
    key="processed",
    value="{{response.data}}"
))
```

### StepConditional

Branch based on conditions:

```python
from openrun import StepConditional
from openrun.steps.execution.conditional import StepConditionalConfig

step = StepConditional(config=StepConditionalConfig(
    left="{{user.role}}",
    operator="equals",  # equals, not_equals, contains, greater_than, less_than
    right="admin"
))
# Ports: "true" and "false"

flow.add_edge(step, admin_step, source_port="true")
flow.add_edge(step, user_step, source_port="false")
```

### StepSwitch

Multi-way branching:

```python
from openrun import StepSwitch
from openrun.steps.execution.switch import StepSwitchConfig

step = StepSwitch(config=StepSwitchConfig(
    value="{{status}}",
    cases=["pending", "approved", "rejected"]
))
# Ports: "pending", "approved", "rejected", "default"
```

### StepDelay

Pause execution:

```python
from openrun import StepDelay
from openrun.steps.execution.delay import StepDelayConfig

step = StepDelay(config=StepDelayConfig(seconds=5))
```

## Join Modes

Control how steps handle multiple incoming edges:

```python
from openrun import JoinMode, StepDelay
from openrun.steps.execution.delay import StepDelayConfig

step = StepDelay(
    config=StepDelayConfig(seconds=1),
    join_mode=JoinMode.ALL_SUCCESS  # Wait for all inputs
)
```

| Mode | Behavior |
|------|----------|
| `NO_WAIT` | Each arrival triggers independently (default) |
| `ALL_SUCCESS` | Wait for all inputs, fail if any fails |
| `ALL_DONE` | Wait for all inputs regardless of success/failure |
| `FIRST_SUCCESS` | Proceed when first input succeeds |

## Events

Flow execution emits events:

```python
from openrun import FlowStarted, StepStarted, StepCompleted, FlowCompleted

async for event in flow.run(trigger_step=trigger):
    match event:
        case FlowStarted():
            print(f"Flow started: {event.flow_id}")
        case StepStarted():
            print(f"Step started: {event.step_id}")
        case StepCompleted():
            print(f"Step completed: {event.result.status}")
        case FlowCompleted():
            print(f"Flow finished: {event.status}")
```

## Custom Steps

Create custom steps by extending `Step`:

```python
from openrun import Step, StepConfig, StepRunResult, StepInfo, StateContainer
from openrun.core.types import StepType, StepRunStatus
from pydantic import Field

class MyStepConfig(StepConfig):
    message: str = Field(description="Message to log")

class MyStep(Step):
    type: StepType = StepType.TRANSFORM  # or define your own
    config: MyStepConfig

    async def run(self, state: StateContainer, config: MyStepConfig) -> StepRunResult:
        print(config.message)
        return StepRunResult.success(step_id=self.id)

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="My Step",
            description="Logs a message",
            category="custom"
        )
```

## Flow Validation

Validate flows before execution:

```python
from openrun import validate_flow, ValidationError

errors = validate_flow(flow)
for error in errors:
    print(f"{error.step_id}: {error.message}")
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Prerequisites

Install uv if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/exacog/openrun.git
cd openrun
uv sync
```

This will create a virtual environment and install all dependencies (including dev dependencies).

### Running Tests

```bash
uv run pytest
```

### Linting & Formatting

Check for linting issues:

```bash
uv run ruff check .
```

Auto-fix linting issues:

```bash
uv run ruff check . --fix
```

Format code:

```bash
uv run ruff format .
```

### Building

```bash
uv build
```

This will create distribution files in the `dist/` directory.
