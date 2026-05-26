"""Update State Node for advancing plan steps.

This node updates the plan progress and step counter
after successful execution with remaining steps.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("update_state_node")
def update_state_node(state: AgentState) -> Dict[str, Any]:
    """Update state node function.

    Advances the plan step counter and updates progress.

    Args:
        state: Current agent state

    Returns:
        State updates with new current_step_index.
    """
    current_step_index = state["current_step_index"]
    plan_steps = state["plan_steps"]
    observations = state["observations"]

    # Increment step index
    new_step_index = current_step_index + 1

    # Check if plan is complete
    if plan_steps and new_step_index >= len(plan_steps):
        # All steps completed
        return {
            "current_step_index": new_step_index,
            "execution_status": "SUCCESS_COMPLETE",
            "finished": False,  # Will be finalized by next routing
        }

    # Clear injected knowledge for next step
    return {
        "current_step_index": new_step_index,
        "injected_knowledge": "",  # Clear for next step
        "finished": False,
    }


@log_node_io("update_state_node_with_progress")
def update_state_node_with_progress(state: AgentState) -> Dict[str, Any]:
    """Update state node with detailed progress tracking.

    Args:
        state: Current agent state

    Returns:
        State updates with progress information.
    """
    plan_steps = state["plan_steps"]
    current_step_index = state["current_step_index"]
    observations = state["observations"]

    # Calculate progress
    total_steps = len(plan_steps) if plan_steps else 1
    completed_steps = current_step_index + 1
    progress_percent = (completed_steps / total_steps) * 100

    # Update runtime state with progress
    runtime_state = state["runtime_state"]
    runtime_state["progress"] = {
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "current_step_name": plan_steps[current_step_index].get("name", "unknown") if plan_steps and current_step_index < len(plan_steps) else "completed",
        "percent": progress_percent,
    }

    # Increment step
    new_step_index = current_step_index + 1

    return {
        "current_step_index": new_step_index,
        "runtime_state": runtime_state,
        "injected_knowledge": "",
        "finished": False,
    }