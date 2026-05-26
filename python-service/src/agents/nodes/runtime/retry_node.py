"""Retry Node for handling retryable errors.

This node manages retry attempts for failed operations.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("retry_node")
def retry_node(state: AgentState) -> Dict[str, Any]:
    """Retry node function.

    Manages retry attempts and determines if we should continue retrying.

    Args:
        state: Current agent state

    Returns:
        State updates with retry_count and whether to abort.
    """
    retry_count = state["retry_count"]
    max_retries = 3

    # Increment retry count
    new_retry_count = retry_count + 1

    if new_retry_count >= max_retries:
        # Max retries exceeded - abort
        return {
            "retry_count": new_retry_count,
            "finished": True,
            "error": f"Max retries ({max_retries}) exceeded",
            "final_response": "操作失败，请检查卡片连接或重试。",
        }

    # Retry allowed
    return {
        "retry_count": new_retry_count,
        "finished": False,
        "need_retry": False,  # Will be set by think_node
    }


@log_node_io("reconnect_retry")
def reconnect_retry(state: AgentState) -> Dict[str, Any]:
    """Reconnect retry strategy.

    Used when connection was lost.

    Args:
        state: Current agent state

    Returns:
        State updates for reconnect retry.
    """
    retry_count = state["retry_count"]

    if retry_count >= 3:
        return {
            "retry_count": retry_count + 1,
            "finished": True,
            "error": "Connection repeatedly lost, cannot reconnect",
        }

    # Reset runtime state for reconnect
    runtime_state = state["runtime_state"]
    runtime_state["connected"] = False
    runtime_state["selected_path"] = []

    return {
        "retry_count": retry_count + 1,
        "runtime_state": runtime_state,
        "finished": False,
    }


def get_retry_message(retry_count: int) -> str:
    """Get retry status message.

    Args:
        retry_count: Current retry count

    Returns:
        Retry message.
    """
    messages = {
        0: "",
        1: "第一次重试...",
        2: "第二次重试...",
        3: "第三次重试（最后一次）...",
    }

    return messages.get(retry_count, f"第{retry_count}次重试...")