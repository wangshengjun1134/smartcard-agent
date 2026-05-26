"""Skill Runtime Node for executing skills.

This node executes the selected skill and records the results.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io
from skills.base.base_skill import SkillResult


@log_node_io("skill_runtime_node")
async def skill_runtime_node(state: AgentState) -> Dict[str, Any]:
    """Skill runtime node function.

    Executes the selected skill and records the observation.

    Args:
        state: Current agent state

    Returns:
        State updates with new observation.
    """
    skill_name = state["selected_skill"]
    params = state["skill_params"]
    error = state.get("error")

    # Check for previous error
    if error:
        observation = create_error_observation(skill_name, params, error)
        return {
            "observations": state["observations"] + [observation],
            "finished": False,
        }

    # Handle special actions
    if skill_name == "connect":
        return handle_connect(state)

    if skill_name == "rag_lookup":
        return await handle_rag_lookup(state)

    # Execute skill
    result = await execute_skill(skill_name, params, state)

    # Create observation
    observation = create_observation(skill_name, params, result)

    # Update runtime state
    runtime_state = update_runtime_state(state["runtime_state"], result)

    return {
        "observations": state["observations"] + [observation],
        "runtime_state": runtime_state,
        "finished": False,
    }


def create_observation(
    skill_name: str,
    params: Dict[str, Any],
    result: SkillResult,
) -> Dict[str, Any]:
    """Create observation from skill execution.

    Args:
        skill_name: Skill name
        params: Skill parameters
        result: Skill execution result

    Returns:
        Observation dictionary.
    """
    return {
        "skill_name": skill_name,
        "params": params,
        "success": result.success,
        "data": result.data,
        "sw": result.sw,
        "error": result.error,
        "metadata": result.metadata,
    }


def create_error_observation(
    skill_name: str,
    params: Dict[str, Any],
    error: str,
) -> Dict[str, Any]:
    """Create error observation.

    Args:
        skill_name: Skill name
        params: Parameters
        error: Error message

    Returns:
        Error observation.
    """
    return {
        "skill_name": skill_name,
        "params": params,
        "success": False,
        "error": error,
    }


async def execute_skill(
    skill_name: str,
    params: Dict[str, Any],
    state: AgentState,
) -> SkillResult:
    """Execute a skill.

    Args:
        skill_name: Skill name
        params: Skill parameters
        state: Agent state

    Returns:
        SkillResult from execution.
    """
    from skills.base.registry import get_skill
    from skills.base.base_skill import SkillExecutionContext

    skill = get_skill(skill_name)

    if skill is None:
        return SkillResult(success=False, error=f"Skill {skill_name} not found")

    # Create execution context
    # Note: This would need actual PCSC client and runtime context
    ctx = SkillExecutionContext(
        pcsc_client=None,  # Would be provided by workflow
        runtime_context=None,  # Would be provided by workflow
        skill_registry=None,
    )

    try:
        result = await skill.run(ctx, params)
        return result
    except Exception as e:
        return SkillResult(success=False, error=str(e))


def handle_connect(state: AgentState) -> Dict[str, Any]:
    """Handle connect action.

    Args:
        state: Current state

    Returns:
        State updates.
    """
    # This would connect to the card via PCSC
    # For now, return a mock observation
    observation = {
        "skill_name": "connect",
        "params": {},
        "success": True,
        "metadata": {"reader": "Mock Reader", "atr": "3B9F96801F878031E073FE211B67"},
    }

    runtime_state = state["runtime_state"]
    runtime_state["connected"] = True
    runtime_state["atr"] = observation["metadata"]["atr"]

    return {
        "observations": state["observations"] + [observation],
        "runtime_state": runtime_state,
    }


async def handle_rag_lookup(state: AgentState) -> Dict[str, Any]:
    """Handle RAG lookup action.

    Args:
        state: Current state

    Returns:
        State updates.
    """
    from api.rag import get_rag_service

    try:
        rag_service = get_rag_service()  # 使用全局单例
        answer = await rag_service.query(state["user_input"], k=4)

        observation = {
            "skill_name": "rag_lookup",
            "params": {"query": state["user_input"]},
            "success": True,
            "response": answer,
        }

        return {
            "observations": state["observations"] + [observation],
            "finished": True,  # RAG lookup 完成后标记为 finished
        }
    except Exception as e:
        observation = {
            "skill_name": "rag_lookup",
            "params": {"query": state["user_input"]},
            "success": False,
            "error": str(e),
            "response": f"知识库查询失败: {str(e)}",
        }
        return {
            "observations": state["observations"] + [observation],
            "finished": True,
        }


def update_runtime_state(
    runtime_state: Dict[str, Any],
    result: SkillResult,
) -> Dict[str, Any]:
    """Update runtime state from skill result.

    Args:
        runtime_state: Current runtime state
        result: Skill execution result

    Returns:
        Updated runtime state.
    """
    new_state = runtime_state.copy()

    # Update based on result metadata
    if result.success and result.metadata:
        # Update selected path if file was selected
        if "fid" in result.metadata:
            path = new_state.get("selected_path", [])
            path.append(result.metadata["fid"])
            new_state["selected_path"] = path

        # Update card type if discovered
        if "card_type" in result.metadata:
            new_state["card_type"] = result.metadata["card_type"]

        if "capabilities" in result.metadata:
            new_state["capabilities"] = result.metadata["capabilities"]

    return new_state