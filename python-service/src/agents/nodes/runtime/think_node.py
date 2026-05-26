"""Runtime Think Node for reasoning about next action.

This node analyzes the current state and determines what skill
to execute next to achieve the current goal.
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from agents.graph.state import AgentState


THINK_PROMPT = ChatPromptTemplate.from_template("""
你是一个智能卡操作推理节点。

分析当前状态，决定下一步要执行的Skill。

当前目标: {goal}
Runtime状态: {runtime_state}
历史执行结果: {observations}

可选Skills：
- select_file: 选择文件 (参数: fid)
- read_binary: 读取二进制数据 (参数: offset, length)
- read_record: 读取记录 (参数: record_number, length)
- verify_pin: 验证PIN (参数: pin, pin_ref)
- get_response: 获取响应 (参数: length)
- read_imsi: 读取IMSI (组合skill)
- read_iccid: 读取ICCID (组合skill)
- discover_card: 探测卡片 (探索skill)

请返回下一步要执行的Skill和参数，格式如下：
skill: <skill_name>
params: {"key": "value"}

下一步:
""")


def think_node(state: AgentState) -> Dict[str, Any]:
    """Runtime think node function.

    Determines the next skill to execute.

    Args:
        state: Current agent state

    Returns:
        State updates with next_action.
    """
    goal = state["current_goal"]
    runtime_state = state["runtime_state"]
    observations = state["observations"]

    # Determine next action based on goal
    next_action = determine_next_action(goal, runtime_state, observations)

    return {
        "next_action": next_action,
        "selected_skill": next_action.get("skill", ""),
        "skill_params": next_action.get("params", {}),
    }


def determine_next_action(
    goal: str,
    runtime_state: Dict[str, Any],
    observations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Determine next action from goal and state.

    Args:
        goal: Current goal
        runtime_state: Runtime context state
        observations: Execution history

    Returns:
        Next action dictionary with skill and params.
    """
    # Goal-specific action mapping
    if goal == "read_imsi":
        # Check if we need to start or continue
        connected = runtime_state.get("connected", False)
        selected_path = runtime_state.get("selected_path", [])

        if not connected:
            return {"skill": "connect", "params": {}}

        # Use composite skill
        return {"skill": "read_imsi", "params": {}}

    elif goal == "read_iccid":
        return {"skill": "read_iccid", "params": {}}

    elif goal == "discover_card":
        connected = runtime_state.get("connected", False)
        if not connected:
            return {"skill": "connect", "params": {}}
        return {"skill": "discover_card", "params": {}}

    elif goal == "knowledge_query":
        # No skill execution, just RAG
        return {"skill": "rag_lookup", "params": {}}

    # Default: start with discover_card if unknown goal
    return {"skill": "discover_card", "params": {}}


async def think_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Think node using LLM for reasoning.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates.
    """
    chain = THINK_PROMPT | llm

    result = chain.invoke({
        "goal": state["current_goal"],
        "runtime_state": str(state["runtime_state"]),
        "observations": str(state["observations"][-3:]),  # Last 3 observations
    })

    # Parse skill and params from response
    response_text = result.content.strip()

    # Simple parsing (can be enhanced)
    skill = ""
    params = {}

    lines = response_text.split("\n")
    for line in lines:
        if line.startswith("skill:"):
            skill = line.split(":", 1)[1].strip()
        if line.startswith("params:"):
            import json
            try:
                params_str = line.split(":", 1)[1].strip()
                params = json.loads(params_str)
            except:
                params = {}

    return {
        "next_action": {"skill": skill, "params": params},
        "selected_skill": skill,
        "skill_params": params,
    }