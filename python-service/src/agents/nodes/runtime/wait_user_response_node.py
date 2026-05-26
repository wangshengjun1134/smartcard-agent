"""Wait User Response Node for handling user input.

This node processes the user's response to a confirmation request.

Note: In LangGraph, this node should be designed to handle
interrupt/resume pattern for async user input.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("wait_user_response_node")
def wait_user_response_node(state: AgentState) -> Dict[str, Any]:
    """Wait user response node function.

    Processes user's response to confirmation request.

    Args:
        state: Current agent state

    Returns:
        State updates with processed user_response.
    """
    user_response = state["user_response"]
    user_confirm_message = state["user_confirm_message"]

    # If no response yet, this is a pause point
    # In actual implementation, this would trigger an interrupt
    if not user_response:
        # Return state indicating we're waiting for input
        return {
            "user_confirm_required": True,
            "finished": False,
            # In LangGraph, we might return Command(goto=END, update=...) for interrupt
        }

    # Process the response
    confirmed = parse_user_response(user_response)

    if confirmed:
        # User confirmed, clear confirmation state and continue
        return {
            "user_confirm_required": False,
            "user_confirm_message": "",
            "user_response": "",
            "finished": False,
        }
    else:
        # User declined, abort
        return {
            "user_confirm_required": False,
            "user_confirm_message": "",
            "user_response": "",
            "finished": True,
            "final_response": "用户取消操作。",
            "error": "User declined confirmation",
        }


def parse_user_response(response: str) -> bool:
    """Parse user response to determine confirmation.

    Args:
        response: User's response text

    Returns:
        True if confirmed, False if declined.
    """
    response_lower = response.lower()

    # Confirmation patterns
    confirm_patterns = [
        "是", "yes", "确认", "继续", "ok", "好的", "同意", "y",
        "可以", "没问题", "执行", "proceed",
    ]

    # Decline patterns
    decline_patterns = [
        "否", "no", "取消", "停止", "abort", "不", "拒绝", "n",
        "cancel", "不要", "算了",
    ]

    # Check for decline first (safety)
    for pattern in decline_patterns:
        if pattern in response_lower:
            return False

    # Check for confirmation
    for pattern in confirm_patterns:
        if pattern in response_lower:
            return True

    # Default: treat ambiguous responses as decline for safety
    return False


@log_node_io("wait_user_response_node_async")
async def wait_user_response_node_async(state: AgentState) -> Dict[str, Any]:
    """Async version of wait user response node.

    This version is designed to work with LangGraph's async patterns.

    Args:
        state: Current agent state

    Returns:
        State updates.
    """
    # Same logic as sync version
    return wait_user_response_node(state)


def set_user_response(state: AgentState, response: str) -> AgentState:
    """Set user response in state (for external input injection).

    Args:
        state: Current agent state
        response: User's response

    Returns:
        Updated state.
    """
    return AgentState(**{**state, "user_response": response})