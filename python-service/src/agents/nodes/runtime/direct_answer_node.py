"""Direct Answer Node for simple chat responses.

This node handles normal chat queries that don't require
RAG or tool execution.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("direct_answer_node")
async def direct_answer_node(state: AgentState) -> Dict[str, Any]:
    """Direct answer node function.

    Generates a simple direct response for normal chat queries.
    Falls back to LLM if no pattern matches.

    Args:
        state: Current agent state

    Returns:
        State updates with final_response and finished=True.
    """
    user_input = state["user_input"]

    # Generate simple response
    final_response = await generate_direct_response(user_input)

    return {
        "final_response": final_response,
        "finished": True,
    }


async def generate_direct_response(user_input: str) -> str:
    """Generate direct response for user input.

    Args:
        user_input: User request text

    Returns:
        Direct response string.
    """
    input_lower = user_input.lower()

    # Greeting patterns
    if any(word in input_lower for word in ["你好", "hello", "hi", "您好"]):
        return "您好！我是智能卡操作助手，可以帮您进行读卡、APDU命令执行等操作，也可以回答智能卡相关的技术问题。"

    # Help request
    if any(word in input_lower for word in ["帮助", "help", "怎么用", "功能"]):
        return """我可以帮助您完成以下任务：

1. **读取卡片信息**：读取IMSI、ICCID、号码等
2. **执行APDU命令**：发送和执行APDU命令
3. **探测卡片能力**：识别卡片类型和应用
4. **知识查询**：解答智能卡技术问题

请告诉我您需要什么帮助？"""

    # Simple thank you
    if any(word in input_lower for word in ["谢谢", "感谢", "thanks"]):
        return "不客气！如果还有其他问题，随时可以问我。"

    # Fallback to LLM
    try:
        from llm.llm import get_llm
        from langchain_core.prompts import ChatPromptTemplate

        llm = get_llm()
        prompt = ChatPromptTemplate.from_template("""
你是一个智能卡操作助手。

用户提出了一个普通问题，请直接回答。

用户输入: {input}

请给出简洁、友好的回答。
""")
        chain = prompt | llm
        result = await chain.ainvoke({"input": user_input})
        return result.content.strip()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"LLM fallback failed: {e}")
        # Final fallback when LLM is not available
        return f"我收到了您的消息：'{user_input}'。如果您需要进行智能卡操作或查询相关知识，请告诉我具体需求。"