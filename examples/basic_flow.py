"""Basic flow example demonstrating API requests, state management, and replies.

This example creates a flow that:
1. Triggers via webhook
2. Fetches a user from JSONPlaceholder API
3. Saves the user's name and email to state
4. Generates a reply with the user info

Run with: uv run python examples/basic_flow.py
"""

import asyncio

from openrun import (
    Flow,
    TriggerWebhook,
    StepRequest,
    StepSetState,
    StepReply,
    StateContainer,
    FlowStarted,
    StepStarted,
    StepCompleted,
    FlowCompleted,
)
from openrun.steps.triggers.webhook import TriggerWebhookConfig
from openrun.steps.execution.request import StepRequestConfig
from openrun.steps.execution.set_state import StepSetStateConfig
from openrun.steps.execution.reply import StepReplyConfig


def create_flow() -> Flow:
    """Create a flow that fetches user data and generates a reply."""
    flow = Flow(name="Fetch User Info")

    # Step 1: Webhook trigger (entry point)
    trigger = TriggerWebhook(config=TriggerWebhookConfig(path="/get-user"))

    # Step 2: Fetch user from API
    fetch_user = StepRequest(
        config=StepRequestConfig(
            url="https://jsonplaceholder.typicode.com/users/1",
            method="GET",
        )
    )

    # Step 3: Save user info to state
    save_name = StepSetState(
        config=StepSetStateConfig(
            key="user_name",
            value="{{response.name}}",
        )
    )

    save_email = StepSetState(
        config=StepSetStateConfig(
            key="user_email",
            value="{{response.email}}",
        )
    )

    # Step 4: Generate reply with user info
    reply = StepReply(
        config=StepReplyConfig(
            template="User: {{user_name}} ({{user_email}})",
        )
    )

    # Add steps to flow
    flow.add_step(trigger)
    flow.add_step(fetch_user)
    flow.add_step(save_name)
    flow.add_step(save_email)
    flow.add_step(reply)

    # Connect steps: trigger -> fetch -> save_name -> save_email -> reply
    flow.add_edge(trigger, fetch_user)
    flow.add_edge(fetch_user, save_name, source_port="success")
    flow.add_edge(save_name, save_email)
    flow.add_edge(save_email, reply)

    return flow


async def main():
    """Run the flow and print all events."""
    flow = create_flow()
    trigger = flow.get_trigger_steps()[0]

    # Create initial state (simulating webhook request data)
    initial_state = StateContainer()
    initial_state.set("body", {"user_id": 1})
    initial_state.set("headers", {"content-type": "application/json"})

    print(f"Running flow: {flow.name}")
    print("-" * 40)

    # Track final state from step completions
    final_state = None

    # Run flow and handle events
    async for event in flow.run(trigger_step=trigger, initial_state=initial_state):
        match event:
            case FlowStarted():
                print(f"Flow started (run_id: {event.run_id})")

            case StepStarted():
                step = flow.get_step(event.step_id)
                step_name = step.__class__.__name__ if step else "Unknown"
                print(f"  Step started: {step_name}")

            case StepCompleted():
                step = flow.get_step(event.step_id)
                step_name = step.__class__.__name__ if step else "Unknown"
                status = event.result.status.value
                print(f"  Step completed: {step_name} ({status})")

                # Save state snapshot for final output
                final_state = event.state_snapshot

                # Print output data if available
                if event.result.output_data:
                    for key, value in event.result.output_data.items():
                        # Truncate long values
                        str_value = str(value)
                        if len(str_value) > 60:
                            str_value = str_value[:60] + "..."
                        print(f"    -> {key}: {str_value}")

            case FlowCompleted():
                print("-" * 40)
                print(f"Flow completed: {event.status}")

                # Print final state
                if final_state:
                    print("\nFinal state:")
                    for key in ["user_name", "user_email", "reply"]:
                        value = final_state.get(key)
                        if value:
                            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
