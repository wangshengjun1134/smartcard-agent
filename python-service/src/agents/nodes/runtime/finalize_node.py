"""Finalize Node for generating final response.

This node summarizes the execution results and generates
the final response to the user.
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from agents.graph.state import AgentState
from apdu.constants.sw_codes import decode_sw


FINALIZE_PROMPT = ChatPromptTemplate.from_template("""
你是一个智能卡操作结果总结节点。

根据执行历史生成最终响应。

用户原始请求: {user_input}
目标: {goal}
执行历史: {observations}
是否有错误: {has_error}

请生成用户友好的响应，总结执行结果。
如果成功，说明完成了什么。
如果失败，解释失败原因并给出建议。

响应:
""")


def finalize_node(state: AgentState) -> Dict[str, Any]:
    """Finalize node function.

    Generates the final response from execution results.

    Args:
        state: Current agent state

    Returns:
        State updates with final_response and finished.
    """
    user_input = state["user_input"]
    goal = state["current_goal"]
    observations = state["observations"]
    error = state.get("error")

    # Generate response based on goal and observations
    final_response = generate_response(goal, observations, error, user_input)

    return {
        "final_response": final_response,
        "finished": True,
    }


def generate_response(
    goal: str,
    observations: List[Dict[str, Any]],
    error: str,
    user_input: str,
) -> str:
    """Generate final response.

    Args:
        goal: Executed goal
        observations: Execution history
        error: Error message if any
        user_input: Original user input

    Returns:
        Final response string.
    """
    # Goal-specific response generation
    if error:
        return generate_error_response(error, observations)

    if goal == "knowledge_query":
        return generate_knowledge_response(observations)

    if goal == "read_imsi":
        return generate_imsi_response(observations)

    if goal == "read_iccid":
        return generate_iccid_response(observations)

    if goal == "discover_card":
        return generate_discover_response(observations)

    # Generic success response
    return generate_generic_response(goal, observations)


def generate_error_response(error: str, observations: List[Dict[str, Any]]) -> str:
    """Generate error response.

    Args:
        error: Error message
        observations: Execution history

    Returns:
        Error response string.
    """
    last_obs = observations[-1] if observations else {}
    sw = last_obs.get("sw", "")

    if sw:
        sw_desc = decode_sw(sw)
        return f"操作失败: {error}\n状态码 {sw} 含义: {sw_desc}"

    return f"操作失败: {error}"


def generate_knowledge_response(observations: List[Dict[str, Any]]) -> str:
    """Generate knowledge query response.

    Args:
        observations: Execution history

    Returns:
        Knowledge response.
    """
    # Look for RAG results
    for obs in observations:
        if obs.get("skill_name") == "rag_lookup":
            return obs.get("response", "未找到相关信息。")

    return "知识库查询完成。"


def generate_imsi_response(observations: List[Dict[str, Any]]) -> str:
    """Generate IMSI read response.

    Args:
        observations: Execution history

    Returns:
        IMSI response string.
    """
    for obs in observations:
        if obs.get("skill_name") == "read_imsi" and obs.get("success"):
            metadata = obs.get("metadata", {})
            imsi = metadata.get("imsi", "")
            mcc = metadata.get("mcc", "")
            mnc = metadata.get("mnc", "")

            if imsi:
                response = f"IMSI读取成功: {imsi}\n"
                if mcc and mnc:
                    response += f"MCC (国家码): {mcc}\nMNC (网络码): {mnc}"
                return response

    return "IMSI读取失败。"


def generate_iccid_response(observations: List[Dict[str, Any]]) -> str:
    """Generate ICCID read response.

    Args:
        observations: Execution history

    Returns:
        ICCID response string.
    """
    for obs in observations:
        if obs.get("skill_name") == "read_iccid" and obs.get("success"):
            metadata = obs.get("metadata", {})
            iccid = metadata.get("iccid", "")

            if iccid:
                return f"ICCID读取成功: {iccid}"

    return "ICCID读取失败。"


def generate_discover_response(observations: List[Dict[str, Any]]) -> str:
    """Generate discover card response.

    Args:
        observations: Execution history

    Returns:
        Discover response string.
    """
    for obs in observations:
        if obs.get("skill_name") == "discover_card" and obs.get("success"):
            metadata = obs.get("metadata", {})
            card_type = metadata.get("card_type", "Unknown")
            capabilities = metadata.get("capabilities", [])
            apps = metadata.get("discovered_apps", [])

            response = f"卡片类型: {card_type}\n"
            if capabilities:
                response += f"能力: {', '.join(capabilities)}\n"
            if apps:
                response += f"发现的应用: {len(apps)} 个"

            return response

    return "卡片探测失败。"


def generate_generic_response(goal: str, observations: List[Dict[str, Any]]) -> str:
    """Generate generic success response.

    Args:
        goal: Goal name
        observations: Execution history

    Returns:
        Generic response.
    """
    success_count = sum(1 for obs in observations if obs.get("success"))

    return f"操作 '{goal}' 完成，成功执行 {success_count} 个步骤。"


async def finalize_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Finalize node using LLM for response generation.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates.
    """
    chain = FINALIZE_PROMPT | llm

    result = chain.invoke({
        "user_input": state["user_input"],
        "goal": state["current_goal"],
        "observations": str(state["observations"]),
        "has_error": state.get("error") is not None,
    })

    return {
        "final_response": result.content.strip(),
        "finished": True,
    }