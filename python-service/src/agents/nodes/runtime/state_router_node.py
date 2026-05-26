"""State Router Node for routing based on execution status.

This node determines the next path based on execution_status
from the observe node.

Routing paths:
- SUCCESS_COMPLETE → Finalize
- SUCCESS_CONTINUE → UpdateState → InputPrepare
- NEEDS_KNOWLEDGE → ProactiveRAG → InjectKnowledge → InputPrepare
- RETRYABLE (not exceeded) → Retry → UpdateRetryCount → InputPrepare
- RETRYABLE_EXCEEDED → Finalize
- NEEDS_USER_INPUT → UserConfirm → WaitUserResponse → InputPrepare
- FATAL_ERROR → Finalize
- NEEDS_REPLAN → RePlan → Planner
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io
from agents.graph.state import (
    EXEC_STATUS_SUCCESS_COMPLETE,
    EXEC_STATUS_SUCCESS_CONTINUE,
    EXEC_STATUS_NEEDS_KNOWLEDGE,
    EXEC_STATUS_RETRYABLE,
    EXEC_STATUS_RETRYABLE_EXCEEDED,
    EXEC_STATUS_NEEDS_USER_INPUT,
    EXEC_STATUS_FATAL_ERROR,
    EXEC_STATUS_NEEDS_REPLAN,
)


@log_node_io("state_router_node")
def state_router_node(state: AgentState) -> Dict[str, Any]:
    """State router node function.

    Pass-through node that allows conditional routing based on execution_status.

    Args:
        state: Current agent state

    Returns:
        State updates (pass-through, routing happens in workflow).
    """
    # This node is a pass-through for conditional routing
    # The actual routing is handled by the workflow's conditional_edges
    return {
        "finished": False,
    }


def get_routing_decision(state: AgentState) -> str:
    """Get routing decision based on execution_status.

    This function is used by workflow's conditional_edges.

    Args:
        state: Current agent state

    Returns:
        Route target node name.
    """
    execution_status = state["execution_status"]
    retry_count = state["retry_count"]
    max_retries = state["max_retries"]

    # Route based on execution status
    if execution_status == EXEC_STATUS_SUCCESS_COMPLETE:
        return "finalize"

    if execution_status == EXEC_STATUS_SUCCESS_CONTINUE:
        return "update_state"

    if execution_status == EXEC_STATUS_NEEDS_KNOWLEDGE:
        return "proactive_rag"

    if execution_status == EXEC_STATUS_RETRYABLE:
        # Check retry limit
        if retry_count < max_retries:
            return "retry"
        else:
            return "finalize"  # Retry exceeded

    if execution_status == EXEC_STATUS_RETRYABLE_EXCEEDED:
        return "finalize"

    if execution_status == EXEC_STATUS_NEEDS_USER_INPUT:
        return "user_confirm"

    if execution_status == EXEC_STATUS_FATAL_ERROR:
        return "finalize"

    if execution_status == EXEC_STATUS_NEEDS_REPLAN:
        return "replan"

    # Default: continue with input_prepare
    return "update_state"