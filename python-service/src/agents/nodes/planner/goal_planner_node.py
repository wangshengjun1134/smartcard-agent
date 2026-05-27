"""Goal Planner Node for determining execution goals.

This node generates high-level goals based on the user request
and execution intent. Goals are like "read_imsi", "discover_card",
not complete APDU sequences.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io
from agents.graph.state import (
    INTENT_NORMAL_CHAT,
    INTENT_RAG_DOMINANT,
    INTENT_TOOL_REASONING,
)


# Goal mapping
GOAL_MAPPING = {
    "读取imsi": "read_imsi",
    "读imsi": "read_imsi",
    "get imsi": "read_imsi",
    "imsi": "read_imsi",

    "读取iccid": "read_iccid",
    "读iccid": "read_iccid",
    "get iccid": "read_iccid",
    "iccid": "read_iccid",

    "读取号码": "read_msisdn",
    "读号码": "read_msisdn",
    "电话号码": "read_msisdn",
    "msisdn": "read_msisdn",

    "探测卡片": "discover_card",
    "探索卡片": "discover_card",
    "识别卡片": "discover_card",
    "卡类型": "discover_card",
    "discover": "discover_card",

    "建立安全通道": "establish_secure_channel",
    "scp03": "scp03_initialize",
    "scp80": "scp80_initialize",

    "下载profile": "profile_download",
    "安装applet": "gp_install_applet",
}


GOAL_PROMPT = ChatPromptTemplate.from_template("""
你是一个智能卡操作目标规划器。

根据用户请求和执行意图，生成高层目标。

目标示例：
- read_imsi: 读取IMSI
- read_iccid: 读取ICCID
- discover_card: 探测卡片能力
- establish_secure_channel: 建立安全通道
- profile_download: 下载Profile

不要生成完整APDU流程，只生成高层目标名称。

用户请求: {input}
执行意图: {intent}

请返回目标名称，仅返回名称，不要解释。

目标:
""")


@log_node_io("goal_planner_node")
def goal_planner_node(state: AgentState) -> Dict[str, Any]:
    """Goal planner node function.

    Determines the high-level goal based on user input and intent.

    Args:
        state: Current agent state

    Returns:
        State updates with current_goal.
    """
    user_input = state["user_input"]
    intent = state["execution_intent"]

    # For RAG dominant intent, goal is "knowledge_query"
    if intent == INTENT_RAG_DOMINANT:
        return {
            "current_goal": "knowledge_query",
            "finished": False,
        }

    # For normal chat, goal is "knowledge_query" (use RAG for general questions)
    if intent == INTENT_NORMAL_CHAT:
        return {
            "current_goal": "knowledge_query",
            "finished": False,
        }

    # For tool reasoning intents, determine specific goal
    goal = determine_goal(user_input)

    return {
        "current_goal": goal,
        "finished": False,
    }


def determine_goal(user_input: str) -> str:
    """Determine goal from user input.

    Args:
        user_input: User request text

    Returns:
        Goal name string.
    """
    input_lower = user_input.lower()

    # Check goal mapping
    for pattern, goal in GOAL_MAPPING.items():
        if pattern in input_lower:
            return goal

    # Default goals based on keywords
    if "imsi" in input_lower:
        return "read_imsi"
    if "iccid" in input_lower:
        return "read_iccid"
    if "探测" in input_lower or "探索" in input_lower:
        return "discover_card"

    # Default: knowledge query
    return "knowledge_query"


@log_node_io("goal_planner_node_with_llm")
async def goal_planner_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Goal planner node using LLM.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with current_goal.
    """
    if state["execution_intent"] in (INTENT_RAG_DOMINANT, INTENT_NORMAL_CHAT):
        return {"current_goal": "knowledge_query"}

    chain = GOAL_PROMPT | llm

    result = chain.invoke({
        "input": state["user_input"],
        "intent": state["execution_intent"],
    })

    goal_text = result.content.strip().lower()

    # Validate goal
    valid_goals = [
        "read_imsi", "read_iccid", "read_msisdn", "read_spn",
        "discover_card", "probe_capabilities", "detect_applications",
        "establish_secure_channel", "scp03_initialize", "scp80_initialize",
        "profile_download", "gp_install_applet",
        "knowledge_query",
    ]

    for valid_goal in valid_goals:
        if valid_goal in goal_text:
            return {"current_goal": valid_goal}

    # Fallback
    return {"current_goal": "discover_card"}