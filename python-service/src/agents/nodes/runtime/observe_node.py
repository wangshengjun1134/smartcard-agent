"""Runtime Observe Node for analyzing execution results.

This node analyzes the results from skill execution and determines
whether to continue, retry, or finish.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from apdu.constants.sw_codes import SW_NORMAL, is_success, decode_sw


def observe_node(state: AgentState) -> Dict[str, Any]:
    """Runtime observe node function.

    Analyzes the last execution result and determines next steps.

    Args:
        state: Current agent state

    Returns:
        State updates with need_retry, need_rag, or finished.
    """
    observations = state["observations"]

    if not observations:
        return {
            "need_retry": False,
            "need_rag": False,
            "finished": False,
        }

    last_observation = observations[-1]
    success = last_observation.get("success", False)
    sw = last_observation.get("sw", "")
    skill_name = last_observation.get("skill_name", "")

    # Check if goal is complete
    goal = state["current_goal"]
    goal_complete = check_goal_complete(goal, observations)

    if goal_complete:
        return {
            "need_retry": False,
            "need_rag": False,
            "finished": True,
        }

    # Check for retryable errors
    if not success:
        need_retry = should_retry(sw, state["retry_count"])

        # Check if we need RAG lookup for error explanation
        need_rag = should_rag_lookup(sw)

        return {
            "need_retry": need_retry,
            "need_rag": need_rag,
            "finished": False,
        }

    # Success but goal not complete - continue
    return {
        "need_retry": False,
        "need_rag": False,
        "finished": False,
    }


def check_goal_complete(goal: str, observations: List[Dict[str, Any]]) -> bool:
    """Check if goal has been achieved.

    Args:
        goal: Current goal
        observations: Execution history

    Returns:
        True if goal is complete.
    """
    # Goal completion criteria
    goal_complete_skills = {
        "read_imsi": ["read_imsi"],
        "read_iccid": ["read_iccid"],
        "discover_card": ["discover_card"],
        "knowledge_query": ["rag_lookup"],
    }

    required_skills = goal_complete_skills.get(goal, [])

    if not required_skills:
        # Unknown goal - check if any skill succeeded
        for obs in observations:
            if obs.get("success"):
                return True
        return False

    # Check if all required skills succeeded
    completed_skills = [
        obs.get("skill_name") for obs in observations
        if obs.get("success")
    ]

    return all(skill in completed_skills for skill in required_skills)


def should_retry(sw: str, retry_count: int) -> bool:
    """Check if operation should be retried.

    Args:
        sw: Status word
        retry_count: Current retry count

    Returns:
        True if should retry.
    """
    # Max retries
    if retry_count >= 3:
        return False

    # Retryable SW codes
    retryable_sw = ["6F00", "6FFF"]

    return sw in retryable_sw


def should_rag_lookup(sw: str) -> bool:
    """Check if RAG lookup is needed for error explanation.

    Args:
        sw: Status word

    Returns:
        True if RAG lookup would help.
    """
    # SW codes that benefit from documentation lookup
    rag_beneficial_sw = [
        "6982",  # Security condition not satisfied
        "6983",  # Auth method blocked
        "6984",  # Key expired
        "6A82",  # File not found
        "6A86",  # Invalid P1/P2
    ]

    return sw in rag_beneficial_sw


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

    # Add specific analysis based on SW
    if sw.startswith("63"):
        # PIN retry count
        analysis["pin_retry_count"] = int(sw[2:4], 16) & 0x0F

    if sw.startswith("61"):
        # Data available
        analysis["data_available"] = int(sw[2:4], 16)

    return analysis