"""Input Prepare Node for organizing inputs and knowledge check.

This node prepares the input context for Think node,
including checking if additional knowledge is needed.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("input_prepare_node")
def input_prepare_node(state: AgentState) -> Dict[str, Any]:
    """Input prepare node function.

    Organizes inputs and performs knowledge check before thinking.

    Args:
        state: Current agent state

    Returns:
        State updates with prepared input context.
    """
    current_goal = state["current_goal"]
    plan_steps = state["plan_steps"]
    current_step_index = state["current_step_index"]
    observations = state["observations"]
    runtime_state = state["runtime_state"]
    injected_knowledge = state["injected_knowledge"]

    # Get current step if plan exists
    current_step = None
    if plan_steps and current_step_index < len(plan_steps):
        current_step = plan_steps[current_step_index]

    # Prepare input context
    input_context = prepare_input_context(
        goal=current_goal,
        current_step=current_step,
        observations=observations,
        runtime_state=runtime_state,
        injected_knowledge=injected_knowledge,
    )

    # Check if knowledge is sufficient
    knowledge_check = check_knowledge_sufficiency(
        goal=current_goal,
        current_step=current_step,
        input_context=input_context,
    )

    return {
        "runtime_state": {
            **runtime_state,
            "input_context": input_context,
            "knowledge_sufficient": knowledge_check["sufficient"],
            "knowledge_gap": knowledge_check["gap"],
        },
        "finished": False,
    }


def prepare_input_context(
    goal: str,
    current_step: Dict[str, Any] | None,
    observations: List[Dict[str, Any]],
    runtime_state: Dict[str, Any],
    injected_knowledge: str,
) -> Dict[str, Any]:
    """Prepare input context for Think node.

    Args:
        goal: Current goal
        current_step: Current planned step
        observations: Execution history
        runtime_state: Runtime context
        injected_knowledge: Injected knowledge from RAG

    Returns:
        Prepared input context dictionary.
    """
    context = {
        "goal": goal,
        "current_step": current_step,
        "recent_observations": observations[-3:] if observations else [],
        "runtime_state_summary": summarize_runtime_state(runtime_state),
        "injected_knowledge": injected_knowledge,
    }

    return context


def summarize_runtime_state(runtime_state: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize runtime state for context.

    Args:
        runtime_state: Full runtime state

    Returns:
        Summary dictionary.
    """
    return {
        "connected": runtime_state.get("connected", False),
        "card_type": runtime_state.get("card_type", "unknown"),
        "selected_path": runtime_state.get("selected_path", []),
        "capabilities": runtime_state.get("capabilities", []),
    }


def check_knowledge_sufficiency(
    goal: str,
    current_step: Dict[str, Any] | None,
    input_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Check if current knowledge is sufficient for execution.

    Args:
        goal: Current goal
        current_step: Current planned step
        input_context: Prepared input context

    Returns:
        Dictionary with sufficient flag and gap description.
    """
    # Goals that require domain knowledge
    knowledge_required_goals = [
        "establish_secure_channel",
        "scp03_initialize",
        "scp80_initialize",
        "profile_download",
        "gp_install_applet",
    ]

    if goal in knowledge_required_goals:
        # Check if we have injected knowledge
        injected_knowledge = input_context.get("injected_knowledge", "")

        if not injected_knowledge:
            return {
                "sufficient": False,
                "gap": f"缺少 {goal} 相关的技术规范知识",
            }

    # For read operations, usually sufficient with basic card context
    if goal in ["read_imsi", "read_iccid", "read_msisdn"]:
        return {
            "sufficient": True,
            "gap": None,
        }

    # For discover operations, check card context
    if goal == "discover_card":
        connected = input_context.get("runtime_state_summary", {}).get("connected", False)
        if not connected:
            return {
                "sufficient": True,  # Can proceed with connection first
                "gap": None,
            }

    # Default: assume sufficient if we have context
    return {
        "sufficient": True,
        "gap": None,
    }


@log_node_io("input_prepare_node_with_llm")
async def input_prepare_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Input prepare node using LLM for knowledge check.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates.
    """
    from langchain_core.prompts import ChatPromptTemplate

    goal = state["current_goal"]
    observations = state["observations"]
    injected_knowledge = state["injected_knowledge"]

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡操作准备节点。

分析当前状态，判断是否需要额外的技术知识才能继续执行。

当前目标: {goal}
已执行操作: {observations}
已有知识: {knowledge}

请判断：
1. 知识是否足够继续执行？
2. 如果不够，缺少什么知识？

格式回答：
sufficient: yes/no
gap: 缺少的知识描述（如果 sufficient=no）
""")

    chain = prompt | llm
    result = chain.invoke({
        "goal": goal,
        "observations": str(observations[-3:]),
        "knowledge": injected_knowledge or "无",
    })

    # Parse response
    response_text = result.content.strip().lower()

    sufficient = "sufficient: yes" in response_text or "sufficient:yes" in response_text

    gap = None
    if not sufficient:
        # Extract gap description
        lines = response_text.split("\n")
        for line in lines:
            if "gap:" in line or "gap：" in line:
                gap = line.split(":", 1)[-1].split("：", 1)[-1].strip()

    return {
        "runtime_state": {
            **state["runtime_state"],
            "knowledge_sufficient": sufficient,
            "knowledge_gap": gap,
        },
        "finished": False,
    }