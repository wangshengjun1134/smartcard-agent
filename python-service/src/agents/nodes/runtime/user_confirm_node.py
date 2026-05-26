"""User Confirm Node for requesting user confirmation.

This node generates a confirmation request when user input
is needed during execution.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("user_confirm_node")
def user_confirm_node(state: AgentState) -> Dict[str, Any]:
    """User confirm node function.

    Generates a confirmation request message for the user.

    Args:
        state: Current agent state

    Returns:
        State updates with user_confirm_required and user_confirm_message.
    """
    current_goal = state["current_goal"]
    observations = state["observations"]
    runtime_state = state["runtime_state"]

    # Generate confirmation message based on context
    confirm_message = generate_confirm_message(
        goal=current_goal,
        observations=observations,
        runtime_state=runtime_state,
    )

    return {
        "user_confirm_required": True,
        "user_confirm_message": confirm_message,
        "user_response": "",  # Clear for new input
        "finished": False,
    }


def generate_confirm_message(
    goal: str,
    observations: list,
    runtime_state: dict,
) -> str:
    """Generate confirmation message for user.

    Args:
        goal: Current goal
        observations: Execution history
        runtime_state: Runtime context

    Returns:
        Confirmation message string.
    """
    # Context-specific confirmation messages
    confirm_messages = {
        "establish_secure_channel": "即将建立安全通道，这将对卡片执行初始化操作。是否继续？",
        "scp03_initialize": "即将执行SCP03初始化，需要验证卡片密钥。是否继续？",
        "profile_download": "即将下载Profile，此操作将修改卡片内容。请确认是否继续？",
        "gp_install_applet": "即将安装Applet，此操作将写入卡片。是否继续？",
    }

    # Use predefined message if available
    if goal in confirm_messages:
        return confirm_messages[goal]

    # Check if last observation indicates a decision needed
    if observations:
        last_obs = observations[-1]
        if not last_obs.get("success"):
            error = last_obs.get("error", "")
            sw = last_obs.get("sw", "")
            return f"操作遇到问题: {error or sw}。是否尝试其他方式？"

    # Default confirmation for safety
    return f"正在执行 '{goal}' 操作，请确认是否继续？"


@log_node_io("user_confirm_node_with_llm")
async def user_confirm_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """User confirm node using LLM for message generation.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates.
    """
    from langchain_core.prompts import ChatPromptTemplate

    goal = state["current_goal"]
    observations = state["observations"]

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡操作助手。

当前执行需要用户确认。请生成一个简洁、友好的确认请求消息。

当前目标: {goal}
最近执行状态: {observations}

请返回确认消息（不超过100字）：
""")

    chain = prompt | llm
    result = chain.invoke({
        "goal": goal,
        "observations": str(observations[-1:]),
    })

    return {
        "user_confirm_required": True,
        "user_confirm_message": result.content.strip(),
        "user_response": "",
        "finished": False,
    }