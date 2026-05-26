"""Intent Analyzer Node for classifying user requests.

This node analyzes the user input and determines the execution intent:
- NORMAL_CHAT: Simple chat, direct response
- RAG_DOMINANT: Knowledge query, RAG lookup needed
- TOOL_REASONING: Tool execution and reasoning needed
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


# Intent classification prompt
INTENT_PROMPT = ChatPromptTemplate.from_template("""
你是一个智能卡操作意图分析器。

分析用户请求，确定执行意图类型。

可选意图类型：
- NORMAL_CHAT: 普通问答，如问候、帮助请求，直接回复即可
- RAG_DOMINANT: RAG主导，主要是知识查询，如"什么是IMSI"、"解释SCP03"
- TOOL_REASONING: 工具/推理主导，需要执行卡片操作，如"读取IMSI"、"建立安全通道"

用户请求: {input}

请返回意图类型，仅返回类型名称，不要解释。

意图类型:
""")


@log_node_io("intent_node")
def intent_node(state: AgentState) -> Dict[str, Any]:
    """Intent analyzer node function.

    Analyzes the user input to determine execution intent.

    Args:
        state: Current agent state

    Returns:
        State updates with execution_intent.
    """
    user_input = state["user_input"]

    # Classify intent
    intent = classify_intent(user_input)

    return {
        "execution_intent": intent,
    }


def classify_intent(user_input: str) -> str:
    """Classify intent from user input.

    Args:
        user_input: User request text

    Returns:
        Intent type string.
    """
    input_lower = user_input.lower()

    # Normal chat patterns (greetings, help, simple interaction)
    normal_chat_patterns = [
        "你好", "hello", "hi", "您好", "早上好", "晚上好",
        "帮助", "help", "怎么用", "功能", "介绍",
        "谢谢", "感谢", "thanks", "不客气",
    ]

    # RAG dominant patterns (knowledge queries, explanations)
    rag_patterns = [
        "什么是", "解释", "说明", "介绍", "定义",
        "how to", "如何", "怎样", "方法",
        "规范", "标准", "协议", "文档",
        "原理", "流程", "步骤说明",
        "区别", "比较", "对比",
        "为什么", "原因", "why",
    ]

    # Tool/reasoning patterns (card operations)
    tool_patterns = [
        "读取", "读卡", "获取", "读出", "read",
        "imsi", "iccid", "号码", "msisdn",
        "apdu", "发送", "执行", "命令",
        "select", "read binary", "verify",
        "探测", "探索", "发现", "分析",
        "识别", "检测", "discover", "probe",
        "建立安全通道", "scp03", "scp80",
        "下载profile", "安装applet",
        "初始化", "configure",
    ]

    # Check patterns in order
    # First check for tool/reasoning (most specific)
    for pattern in tool_patterns:
        if pattern in input_lower:
            return INTENT_TOOL_REASONING

    # Check for RAG dominant
    for pattern in rag_patterns:
        if pattern in input_lower:
            return INTENT_RAG_DOMINANT

    # Check for normal chat
    for pattern in normal_chat_patterns:
        if pattern in input_lower:
            return INTENT_NORMAL_CHAT

    # Check if it looks like a question (RAG dominant)
    if "?" in user_input or "？" in user_input:
        return INTENT_RAG_DOMINANT

    # Default: treat as RAG query for general conversation
    return INTENT_RAG_DOMINANT


@log_node_io("intent_node_with_llm")
async def intent_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Intent analyzer node using LLM.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with execution_intent.
    """
    chain = INTENT_PROMPT | llm

    result = chain.invoke({"input": state["user_input"]})

    # Parse intent from LLM response
    intent_text = result.content.strip().upper()

    # Normalize to valid intent
    valid_intents = [
        INTENT_NORMAL_CHAT,
        INTENT_RAG_DOMINANT,
        INTENT_TOOL_REASONING,
    ]

    for valid_intent in valid_intents:
        if valid_intent in intent_text or valid_intent.replace("_", " ") in intent_text:
            return {"execution_intent": valid_intent}

    # Default fallback: RAG dominant
    return {"execution_intent": INTENT_RAG_DOMINANT}