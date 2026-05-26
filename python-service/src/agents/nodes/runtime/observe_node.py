"""Runtime Observe Node for analyzing execution results.

This node analyzes the results from skill execution and determines
the execution_status for StateRouter routing.

Returns execution_status:
- SUCCESS_COMPLETE: Goal achieved, done
- SUCCESS_CONTINUE: Success but more steps needed
- NEEDS_KNOWLEDGE: Knowledge gap detected
- RETRYABLE: Can retry (not exceeded limit)
- RETRYABLE_EXCEEDED: Retry limit exceeded
- NEEDS_USER_INPUT: User confirmation needed
- FATAL_ERROR: Critical failure, cannot continue
- NEEDS_REPLAN: Current approach failed, need new plan
"""

from typing import Dict, Any, List

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
from apdu.constants.sw_codes import SW_NORMAL, is_success, decode_sw


# Max retries constant
MAX_RETRIES = 3


@log_node_io("observe_node")
def observe_node(state: AgentState) -> Dict[str, Any]:
    """Runtime observe node function.

    Analyzes the last execution result and determines execution_status.

    Args:
        state: Current agent state

    Returns:
        State updates with execution_status.
    """
    observations = state["observations"]
    goal = state["current_goal"]
    plan_steps = state["plan_steps"]
    current_step_index = state["current_step_index"]
    retry_count = state["retry_count"]
    max_retries = state["max_retries"]
    runtime_state = state["runtime_state"]

    if not observations:
        # No observations yet - continue
        return {
            "execution_status": EXEC_STATUS_SUCCESS_CONTINUE,
            "finished": False,
        }

    last_observation = observations[-1]
    success = last_observation.get("success", False)
    sw = last_observation.get("sw", "")
    skill_name = last_observation.get("skill_name", "")

    # Analyze result and determine status
    execution_status = determine_execution_status(
        success=success,
        sw=sw,
        goal=goal,
        plan_steps=plan_steps,
        current_step_index=current_step_index,
        retry_count=retry_count,
        max_retries=max_retries,
        runtime_state=runtime_state,
        last_observation=last_observation,
    )

    return {
        "execution_status": execution_status,
        "finished": False,  # StateRouter will decide to finalize
    }


def determine_execution_status(
    success: bool,
    sw: str,
    goal: str,
    plan_steps: List[Dict[str, Any]],
    current_step_index: int,
    retry_count: int,
    max_retries: int,
    runtime_state: Dict[str, Any],
    last_observation: Dict[str, Any],
) -> str:
    """Determine execution status from observation.

    Args:
        success: Last skill success
        sw: Status word
        goal: Current goal
        plan_steps: Planned steps
        current_step_index: Current step index
        retry_count: Retry count
        max_retries: Max retries
        runtime_state: Runtime context
        last_observation: Last observation details

    Returns:
        Execution status string.
    """
    # Check for fatal errors first
    if is_fatal_error(sw):
        return EXEC_STATUS_FATAL_ERROR

    # Check if user input needed for sensitive operations
    if needs_user_confirmation(goal, runtime_state):
        return EXEC_STATUS_NEEDS_USER_INPUT

    # Handle success case
    if success:
        # Check if goal is complete
        if is_goal_complete(goal, plan_steps, current_step_index):
            return EXEC_STATUS_SUCCESS_COMPLETE

        # Check if there are more steps
        if plan_steps and current_step_index < len(plan_steps) - 1:
            return EXEC_STATUS_SUCCESS_CONTINUE

        # Check if knowledge is needed for next step
        if runtime_state.get("knowledge_sufficient") == False:
            return EXEC_STATUS_NEEDS_KNOWLEDGE

        # Default: continue
        return EXEC_STATUS_SUCCESS_CONTINUE

    # Handle failure case
    # Check if retryable
    if is_retryable_error(sw):
        if retry_count < max_retries:
            return EXEC_STATUS_RETRYABLE
        else:
            return EXEC_STATUS_RETRYABLE_EXCEEDED

    # Check if needs knowledge to understand error
    if needs_knowledge_for_error(sw):
        return EXEC_STATUS_NEEDS_KNOWLEDGE

    # Check if needs replanning
    if needs_replan(last_observation, retry_count):
        return EXEC_STATUS_NEEDS_REPLAN

    # Default: fatal error for unhandled cases
    return EXEC_STATUS_FATAL_ERROR


def is_fatal_error(sw: str) -> bool:
    """Check if SW indicates fatal error.

    Args:
        sw: Status word

    Returns:
        True if fatal error.
    """
    fatal_sw_codes = [
        "6700",  # Wrong length
        "6D00",  # Instruction not supported
        "6E00",  # Class not supported
        "6F00",  # Technical problem
    ]

    return sw in fatal_sw_codes


def is_retryable_error(sw: str) -> bool:
    """Check if SW indicates retryable error.

    Args:
        sw: Status word

    Returns:
        True if retryable.
    """
    retryable_sw_codes = [
        "6100",  # More data available (need GET RESPONSE)
        "63C0",  # PIN verify with retry count remaining
        "6985",  # Conditions not satisfied (might retry with different params)
        "6A80",  # Wrong parameters (might retry with correct params)
    ]

    # 63CX series (PIN retry count)
    if sw.startswith("63"):
        return True

    return sw in retryable_sw_codes


def needs_user_confirmation(goal: str, runtime_state: Dict[str, Any]) -> bool:
    """Check if user confirmation is needed.

    Args:
        goal: Current goal
        runtime_state: Runtime context

    Returns:
        True if confirmation needed.
    """
    # Goals that always need confirmation
    confirmation_required_goals = [
        "profile_download",
        "gp_install_applet",
    ]

    # Check if this is a sensitive operation
    if goal in confirmation_required_goals:
        # Check if already confirmed in runtime state
        return not runtime_state.get("user_confirmed", False)

    return False


def needs_knowledge_for_error(sw: str) -> bool:
    """Check if RAG lookup needed for error explanation.

    Args:
        sw: Status word

    Returns:
        True if knowledge needed.
    """
    knowledge_beneficial_sw = [
        "6982",  # Security condition not satisfied
        "6983",  # Auth method blocked
        "6984",  # Key expired
        "6A82",  # File not found
        "6A86",  # Invalid P1/P2
    ]

    return sw in knowledge_beneficial_sw


def needs_replan(last_observation: Dict[str, Any], retry_count: int) -> bool:
    """Check if replanning is needed.

    Args:
        last_observation: Last observation
        retry_count: Current retry count

    Returns:
        True if replanning needed.
    """
    # If retries exceeded for same approach, need new plan
    if retry_count >= 2:
        return True

    # If specific errors indicate wrong approach
    sw = last_observation.get("sw", "")
    approach_error_sw = [
        "6A82",  # File not found - wrong path
        "6982",  # Security not satisfied - wrong auth
    ]

    if sw in approach_error_sw and retry_count > 0:
        return True

    return False


def is_goal_complete(
    goal: str,
    plan_steps: List[Dict[str, Any]],
    current_step_index: int,
) -> bool:
    """Check if goal is complete.

    Args:
        goal: Current goal
        plan_steps: Planned steps
        current_step_index: Current step index

    Returns:
        True if goal complete.
    """
    # If no plan, check goal-specific completion
    if not plan_steps:
        # Simple goals complete after one success
        simple_goals = ["read_imsi", "read_iccid", "discover_card"]
        if goal in simple_goals:
            return True
        return False

    # Check if all steps completed
    return current_step_index >= len(plan_steps) - 1


def check_goal_complete_legacy(goal: str, observations: List[Dict[str, Any]]) -> bool:
    """Legacy goal completion check (for compatibility).

    Args:
        goal: Current goal
        observations: Execution history

    Returns:
        True if goal is complete.
    """
    goal_complete_skills = {
        "read_imsi": ["read_imsi"],
        "read_iccid": ["read_iccid"],
        "discover_card": ["discover_card"],
        "knowledge_query": ["rag_lookup"],
    }

    required_skills = goal_complete_skills.get(goal, [])

    if not required_skills:
        for obs in observations:
            if obs.get("success"):
                return True
        return False

    completed_skills = [
        obs.get("skill_name") for obs in observations
        if obs.get("success")
    ]

    return all(skill in completed_skills for skill in required_skills)


def analyze_observation(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single observation for detailed info.

    Args:
        observation: Single execution observation

    Returns:
        Analysis dictionary.
    """
    sw = observation.get("sw", "")

    analysis = {
        "sw": sw,
        "sw_description": decode_sw(sw),
        "success": observation.get("success", False),
        "skill_name": observation.get("skill_name", ""),
        "has_data": observation.get("data") is not None,
        "data_length": len(observation.get("data", [])),
    }

    if sw.startswith("63"):
        analysis["pin_retry_count"] = int(sw[2:4], 16) & 0x0F

    if sw.startswith("61"):
        analysis["data_available"] = int(sw[2:4], 16)

    return analysis


@log_node_io("observe_node_with_llm")
async def observe_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Observe node using LLM for advanced analysis.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates.
    """
    from langchain_core.prompts import ChatPromptTemplate

    observations = state["observations"]
    goal = state["current_goal"]

    if not observations:
        return {
            "execution_status": EXEC_STATUS_SUCCESS_CONTINUE,
            "finished": False,
        }

    last_obs = observations[-1]

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡操作分析专家。

分析最新的执行结果，判断下一步状态。

当前目标: {goal}
最新执行: {observation}
重试次数: {retry}

请判断状态：
- SUCCESS_COMPLETE: 目标达成，完成
- SUCCESS_CONTINUE: 成功但需继续下一步
- NEEDS_KNOWLEDGE: 需要知识检索
- RETRYABLE: 可重试
- RETRYABLE_EXCEEDED: 重试超限
- NEEDS_USER_INPUT: 需用户确认
- FATAL_ERROR: 致命错误
- NEEDS_REPLAN: 需重新规划

仅返回状态名称：
""")

    chain = prompt | llm
    result = chain.invoke({
        "goal": goal,
        "observation": str(last_obs),
        "retry": state["retry_count"],
    })

    # Parse response
    response_text = result.content.strip().upper()

    valid_statuses = [
        EXEC_STATUS_SUCCESS_COMPLETE,
        EXEC_STATUS_SUCCESS_CONTINUE,
        EXEC_STATUS_NEEDS_KNOWLEDGE,
        EXEC_STATUS_RETRYABLE,
        EXEC_STATUS_RETRYABLE_EXCEEDED,
        EXEC_STATUS_NEEDS_USER_INPUT,
        EXEC_STATUS_FATAL_ERROR,
        EXEC_STATUS_NEEDS_REPLAN,
    ]

    for status in valid_statuses:
        if status in response_text:
            return {
                "execution_status": status,
                "finished": False,
            }

    # Fallback
    return {
        "execution_status": EXEC_STATUS_FATAL_ERROR,
        "finished": False,
    }