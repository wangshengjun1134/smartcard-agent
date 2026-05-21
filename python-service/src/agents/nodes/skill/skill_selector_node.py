"""Skill Selector Node for choosing the appropriate skill.

This node selects the skill to execute based on the next_action
from the think node.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from skills.base.registry import get_skill, get_registry


def skill_selector_node(state: AgentState) -> Dict[str, Any]:
    """Skill selector node function.

    Validates and selects the skill from the registry.

    Args:
        state: Current agent state

    Returns:
        State updates with selected_skill and skill_params.
    """
    next_action = state["next_action"]
    skill_name = next_action.get("skill", "")
    params = next_action.get("params", {})

    # Check if skill exists
    registry = get_registry()

    if not registry.has_skill(skill_name):
        # Skill not found - check if it's a special action
        if skill_name in ["connect", "rag_lookup"]:
            # These are handled differently
            return {
                "selected_skill": skill_name,
                "skill_params": params,
                "error": None,
            }

        return {
            "selected_skill": "",
            "skill_params": {},
            "error": f"Skill '{skill_name}' not found in registry",
        }

    # Get skill and validate parameters
    skill = registry.get_skill(skill_name)
    valid, error_msg = skill.validate_params(params)

    if not valid:
        return {
            "selected_skill": skill_name,
            "skill_params": params,
            "error": error_msg,
        }

    # Check if skill can execute in current context
    runtime_state = state["runtime_state"]
    can_execute, reason = registry.validate_skill_for_context(skill_name, runtime_state)

    if not can_execute:
        return {
            "selected_skill": skill_name,
            "skill_params": params,
            "error": reason,
        }

    return {
        "selected_skill": skill_name,
        "skill_params": params,
        "error": None,
    }


def get_available_skills_for_goal(goal: str) -> list:
    """Get list of skills that can help achieve a goal.

    Args:
        goal: Goal name

    Returns:
        List of applicable skill names.
    """
    goal_skill_mapping = {
        "read_imsi": ["read_imsi", "select_file", "read_binary"],
        "read_iccid": ["read_iccid", "select_file", "read_binary"],
        "discover_card": ["discover_card", "select_file"],
        "knowledge_query": ["rag_lookup"],
    }

    return goal_skill_mapping.get(goal, [])


def suggest_next_skill(goal: str, runtime_state: Dict[str, Any]) -> str:
    """Suggest the next skill based on goal and state.

    Args:
        goal: Current goal
        runtime_state: Runtime context

    Returns:
        Suggested skill name.
    """
    # Check connection state
    if not runtime_state.get("connected"):
        return "connect"

    # Goal-based suggestions
    available = get_available_skills_for_goal(goal)

    if available:
        # Use first available skill
        return available[0]

    return "discover_card"