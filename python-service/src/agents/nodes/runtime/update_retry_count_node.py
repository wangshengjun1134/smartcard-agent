"""Update Retry Count Node for managing retry attempts.

This node increments the retry count after a retry operation.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("update_retry_count_node")
def update_retry_count_node(state: AgentState) -> Dict[str, Any]:
    """Update retry count node function.

    Increments retry count and prepares for retry attempt.

    Args:
        state: Current agent state

    Returns:
        State updates with new retry_count.
    """
    retry_count = state["retry_count"]

    # Increment retry count
    new_retry_count = retry_count + 1

    # Clear injected knowledge for retry
    return {
        "retry_count": new_retry_count,
        "injected_knowledge": "",
        "finished": False,
    }


@log_node_io("check_retry_limit")
def check_retry_limit(state: AgentState) -> Dict[str, Any]:
    """Check if retry limit has been exceeded.

    Args:
        state: Current agent state

    Returns:
        State updates indicating if retry is possible.
    """
    retry_count = state["retry_count"]
    max_retries = state["max_retries"]

    if retry_count >= max_retries:
        return {
            "execution_status": "RETRYABLE_EXCEEDED",
            "error": f"重试次数超过上限 ({max_retries})",
            "finished": False,
        }

    return {
        "finished": False,
    }