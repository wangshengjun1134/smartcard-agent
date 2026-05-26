"""RePlan Node for re-planning when execution fails.

This node re-generates the plan when the current approach
is not working.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("replan_node")
def replan_node(state: AgentState) -> Dict[str, Any]:
    """RePlan node function.

    Generates a new plan based on current failures and context.

    Args:
        state: Current agent state

    Returns:
        State updates with new plan.
    """
    current_goal = state["current_goal"]
    observations = state["observations"]
    runtime_state = state["runtime_state"]
    user_input = state["user_input"]

    # Analyze failures to inform new plan
    failure_analysis = analyze_failures(observations)

    # Generate new plan based on analysis
    new_plan = generate_new_plan(
        goal=current_goal,
        failure_analysis=failure_analysis,
        runtime_state=runtime_state,
        user_input=user_input,
    )

    return {
        "plan_steps": new_plan,
        "current_step_index": 0,  # Reset step counter
        "retry_count": 0,  # Reset retry count
        "injected_knowledge": "",  # Clear knowledge
        "finished": False,
    }


def analyze_failures(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze failure patterns from observations.

    Args:
        observations: Execution history

    Returns:
        Failure analysis dictionary.
    """
    failures = [obs for obs in observations if not obs.get("success")]

    if not failures:
        return {"has_failures": False}

    # Analyze failure patterns
    failure_skills = [obs.get("skill_name") for obs in failures]
    failure_sws = [obs.get("sw") for obs in failures if obs.get("sw")]
    failure_errors = [obs.get("error") for obs in failures if obs.get("error")]

    return {
        "has_failures": True,
        "failed_skills": failure_skills,
        "failed_sws": failure_sws,
        "failed_errors": failure_errors,
        "failure_count": len(failures),
    }


def generate_new_plan(
    goal: str,
    failure_analysis: Dict[str, Any],
    runtime_state: Dict[str, Any],
    user_input: str,
) -> List[Dict[str, Any]]:
    """Generate new plan based on failure analysis.

    Args:
        goal: Current goal
        failure_analysis: Analysis of failures
        runtime_state: Runtime context
        user_input: Original user input

    Returns:
        New plan steps list.
    """
    # Goal-specific alternative approaches
    alternative_approaches = {
        "read_imsi": [
            {"name": "connect", "skill": "connect", "params": {}},
            {"name": "discover_card", "skill": "discover_card", "params": {}},
            {"name": "read_imsi", "skill": "read_imsi", "params": {}},
        ],
        "establish_secure_channel": [
            {"name": "discover_capabilities", "skill": "discover_card", "params": {}},
            {"name": "check_key_refs", "skill": "get_key_info", "params": {}},
            {"name": "initiate_scp", "skill": "scp_init", "params": {}},
        ],
    }

    # Check for specific failure patterns
    if failure_analysis.get("failed_sws"):
        sws = failure_analysis["failed_sws"]

        # Security-related failures need different approach
        if "6982" in sws or "6983" in sws:
            return [
                {"name": "verify_pin", "skill": "verify_pin", "params": {"pin_ref": "01"}},
                {"name": "retry_goal", "skill": goal, "params": {}},
            ]

        # File not found - need navigation
        if "6A82" in sws:
            return [
                {"name": "discover_structure", "skill": "discover_card", "params": {}},
                {"name": "find_file", "skill": "select_file", "params": {}},
                {"name": "retry_goal", "skill": goal, "params": {}},
            ]

    # Use alternative approach if defined
    if goal in alternative_approaches:
        return alternative_approaches[goal]

    # Default: start with discovery
    return [
        {"name": "discover", "skill": "discover_card", "params": {}},
        {"name": "analyze", "skill": "analyze_card", "params": {}},
        {"name": "retry_goal", "skill": goal, "params": {}},
    ]


@log_node_io("replan_node_with_llm")
async def replan_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """RePlan node using LLM for plan generation.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with LLM-generated plan.
    """
    from langchain_core.prompts import ChatPromptTemplate

    goal = state["current_goal"]
    observations = state["observations"]
    runtime_state = state["runtime_state"]

    # Analyze failures
    failure_analysis = analyze_failures(observations)

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡操作规划专家。

当前计划执行失败，需要重新规划。

原始目标: {goal}
失败分析: {analysis}
Runtime状态: {runtime}

请生成新的执行计划，考虑：
1. 分析失败原因
2. 调整执行策略
3. 避免重复相同的失败

输出格式（JSON列表）：
[
    {"name": "步骤名称", "skill": "skill名", "params": {}},
    ...
]

新计划：
""")

    chain = prompt | llm
    result = chain.invoke({
        "goal": goal,
        "analysis": str(failure_analysis),
        "runtime": str(runtime_state),
    })

    # Parse JSON from response
    import json

    try:
        # Find JSON array in response
        content = result.content.strip()
        # Extract JSON if embedded in text
        if "[" in content and "]" in content:
            start = content.index("[")
            end = content.rindex("]") + 1
            json_str = content[start:end]
            new_plan = json.loads(json_str)
        else:
            new_plan = []
    except json.JSONDecodeError:
        # Fallback to default plan
        new_plan = generate_new_plan(goal, failure_analysis, runtime_state, "")

    return {
        "plan_steps": new_plan,
        "current_step_index": 0,
        "retry_count": 0,
        "injected_knowledge": "",
        "finished": False,
    }