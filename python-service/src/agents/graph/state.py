"""Agent State definition for LangGraph workflow.

This module defines the AgentState TypedDict that holds
all state during the agent workflow execution.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """State for the LangGraph agent workflow.

    This state is passed through all nodes in the workflow:
    - Intent Analyzer
    - Goal Planner
    - Runtime Think
    - Skill Runtime
    - Observe
    - Retry
    - Finalize

    Attributes:
        user_input: Original user request
        execution_intent: Classified intent (KNOWLEDGE_ONLY, REQUIRES_CARD, etc.)
        current_goal: High-level goal (read_imsi, establish_secure_channel, etc.)
        next_action: Next skill/action to execute
        selected_skill: Currently selected skill name
        skill_params: Parameters for selected skill
        observations: List of execution results
        runtime_state: Runtime context state dictionary
        rag_context: Retrieved RAG documents for context
        need_rag: Whether RAG lookup is needed
        need_retry: Whether retry is needed
        retry_count: Current retry count
        final_response: Final response to user
        finished: Whether workflow is complete
        error: Error message if any
    """

    # Input
    user_input: str

    # Intent analysis
    execution_intent: str

    # Goal planning
    current_goal: str

    # Runtime loop state
    next_action: Dict[str, Any]
    selected_skill: str
    skill_params: Dict[str, Any]
    observations: List[Dict[str, Any]]

    # Runtime context
    runtime_state: Dict[str, Any]

    # RAG
    rag_context: List[str]
    need_rag: bool

    # Retry
    need_retry: bool
    retry_count: int

    # Output
    final_response: str
    finished: bool
    error: Optional[str]


def create_initial_state(user_input: str) -> AgentState:
    """Create initial agent state for a request.

    Args:
        user_input: User's input request

    Returns:
        Initial AgentState dictionary.
    """
    return AgentState(
        user_input=user_input,
        execution_intent="",
        current_goal="",
        next_action={},
        selected_skill="",
        skill_params={},
        observations=[],
        runtime_state={},
        rag_context=[],
        need_rag=False,
        need_retry=False,
        retry_count=0,
        final_response="",
        finished=False,
        error=None,
    )


def update_state(state: AgentState, updates: Dict[str, Any]) -> AgentState:
    """Update agent state with new values.

    Args:
        state: Current state
        updates: Values to update

    Returns:
        New AgentState with updates.
    """
    return AgentState(**{**state, **updates})