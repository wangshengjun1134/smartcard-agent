"""Agent State definition for LangGraph workflow.

This module defines the AgentState TypedDict that holds
all state during the agent workflow execution.
"""

from typing import TypedDict, List, Dict, Any, Optional


# Execution status constants for StateRouter
EXEC_STATUS_SUCCESS_COMPLETE = "SUCCESS_COMPLETE"       # 成功且完成
EXEC_STATUS_SUCCESS_CONTINUE = "SUCCESS_CONTINUE"       # 成功但有后续步骤
EXEC_STATUS_NEEDS_KNOWLEDGE = "NEEDS_KNOWLEDGE"         # 需要知识检索
EXEC_STATUS_RETRYABLE = "RETRYABLE"                     # 可重试
EXEC_STATUS_RETRYABLE_EXCEEDED = "RETRYABLE_EXCEEDED"   # 重试次数超限
EXEC_STATUS_NEEDS_USER_INPUT = "NEEDS_USER_INPUT"       # 需要用户输入
EXEC_STATUS_FATAL_ERROR = "FATAL_ERROR"                 # 致命错误
EXEC_STATUS_NEEDS_REPLAN = "NEEDS_REPLAN"               # 需要重新规划


# Intent type constants
INTENT_NORMAL_CHAT = "NORMAL_CHAT"           # 普通问答
INTENT_RAG_DOMINANT = "RAG_DOMINANT"         # RAG主导
INTENT_TOOL_REASONING = "TOOL_REASONING"     # 工具/推理主导


class AgentState(TypedDict):
    """State for the LangGraph agent workflow.

    This state is passed through all nodes in the workflow:
    - Intent Analyzer
    - DirectAnswer / RagQuery / Planner
    - InputPrepare
    - Think
    - SkillSelect / SkillExec
    - Observe / StateRouter
    - UpdateState / Retry / ProactiveRAG / UserConfirm / RePlan
    - Finalize

    Attributes:
        user_input: Original user request
        
        # Intent analysis
        execution_intent: Classified intent (NORMAL_CHAT, RAG_DOMINANT, TOOL_REASONING)
        
        # Goal planning
        current_goal: High-level goal (read_imsi, establish_secure_channel, etc.)
        plan_steps: List of planned steps for complex tasks
        current_step_index: Current step index in the plan
        
        # Runtime loop state
        next_action: Next skill/action to execute
        selected_skill: Currently selected skill name
        skill_params: Parameters for selected skill
        observations: List of execution results
        
        # Runtime context
        runtime_state: Runtime context state dictionary
        
        # Execution status (for StateRouter)
        execution_status: Current execution status from observe
        
        # RAG
        rag_context: Retrieved RAG documents for context
        rag_query: Query for RAG lookup
        injected_knowledge: Knowledge injected into context
        
        # Retry
        retry_count: Current retry count
        max_retries: Maximum retry limit
        
        # User input handling
        user_confirm_required: Whether user confirmation is needed
        user_confirm_message: Message to show user for confirmation
        user_response: User's response to confirmation
        
        # Output
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
    plan_steps: List[Dict[str, Any]]
    current_step_index: int

    # Runtime loop state
    next_action: Dict[str, Any]
    selected_skill: str
    skill_params: Dict[str, Any]
    observations: List[Dict[str, Any]]

    # Runtime context
    runtime_state: Dict[str, Any]

    # Execution status
    execution_status: str

    # RAG
    rag_context: List[str]
    rag_query: str
    injected_knowledge: str

    # Retry
    retry_count: int
    max_retries: int

    # User input handling
    user_confirm_required: bool
    user_confirm_message: str
    user_response: str

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
        plan_steps=[],
        current_step_index=0,
        next_action={},
        selected_skill="",
        skill_params={},
        observations=[],
        runtime_state={},
        execution_status="",
        rag_context=[],
        rag_query="",
        injected_knowledge="",
        retry_count=0,
        max_retries=3,
        user_confirm_required=False,
        user_confirm_message="",
        user_response="",
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