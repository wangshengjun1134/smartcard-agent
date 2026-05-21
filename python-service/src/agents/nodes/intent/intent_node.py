"""Intent Analyzer Node for classifying user requests.

This node analyzes the user input and determines the execution intent:
- KNOWLEDGE_ONLY: Just RAG lookup, no card operations
- REQUIRES_CARD: Card operations needed
- REQUIRES_APDU: APDU operations needed
- REQUIRES_DYNAMIC_REASONING: Complex dynamic reasoning needed
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from agents.graph.state import AgentState


# Intent types
INTENT_KNOWLEDGE_ONLY = "KNOWLEDGE_ONLY"
INTENT_REQUIRES_CARD = "REQUIRES_CARD"
INTENT_REQUIRES_APDU = "REQUIRES_APDU"
INTENT_REQUIRES_DYNAMIC_REASONING = "REQUIRES_DYNAMIC_REASONING"
INTENT_REQUIRES_MULTI_STEP = "REQUIRES_MULTI_STEP_EXECUTION"


# Intent classification prompt
INTENT_PROMPT = ChatPromptTemplate.from_template("""
你是一个智能卡操作意图分析器。

分析用户请求，确定执行意图类型。

可选意图类型：
- KNOWLEDGE_ONLY: 仅知识库查询，不需要卡片操作
- REQUIRES_CARD: 需要读卡操作
- REQUIRES_APDU: 需要APDU命令执行
- REQUIRES_DYNAMIC_REASONING: 需要动态推理（如探索卡能力、处理未知响应）
- REQUIRES_MULTI_STEP_EXECUTION: 要多步骤执行（如建立安全通道、下载Profile）

用户请求: {input}

请返回意图类型，仅返回类型名称，不要解释。

意图类型:
""")


def intent_node(state: AgentState) -> Dict[str, Any]:
    """Intent analyzer node function.

    Analyzes the user input to determine execution intent.

    Args:
        state: Current agent state

    Returns:
        State updates with execution_intent.
    """
    user_input = state["user_input"]

    # Simple rule-based intent classification (can be enhanced with LLM)
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

    # Knowledge-only patterns
    knowledge_patterns = [
        "什么是", "解释", "说明", "介绍", "定义",
        "查询", "搜索", "查找", "how to", "什么是",
        "规范", "标准", "协议", "文档",
    ]

    # Card operation patterns
    card_patterns = [
        "读取", "读卡", "获取", "读出", "read",
        "imsi", "iccid", "号码",
    ]

    # APDU patterns
    apdu_patterns = [
        "apdu", "发送", "执行", "命令",
        "select", "read binary", "verify",
    ]

    # Dynamic reasoning patterns
    dynamic_patterns = [
        "探索", "探测", "发现", "分析",
        "识别", "检测", "discover", "probe",
        "调试", "debug", "问题", "错误",
    ]

    # Multi-step patterns
    multi_step_patterns = [
        "建立安全通道", "scp03", "scp80",
        "下载profile", "安装applet",
        "初始化", "configure",
    ]

    # Check patterns in order of specificity
    for pattern in multi_step_patterns:
        if pattern in input_lower:
            return INTENT_REQUIRES_MULTI_STEP

    for pattern in dynamic_patterns:
        if pattern in input_lower:
            return INTENT_REQUIRES_DYNAMIC_REASONING

    for pattern in apdu_patterns:
        if pattern in input_lower:
            return INTENT_REQUIRES_APDU

    for pattern in card_patterns:
        if pattern in input_lower:
            return INTENT_REQUIRES_CARD

    for pattern in knowledge_patterns:
        if pattern in input_lower:
            return INTENT_KNOWLEDGE_ONLY

    # Default: check if it looks like a question
    if "?" in user_input or "？" in user_input:
        return INTENT_KNOWLEDGE_ONLY

    # Default: requires card (most user requests involve cards)
    return INTENT_REQUIRES_CARD


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
    intent_text = result.content.strip()

    # Normalize to valid intent
    valid_intents = [
        INTENT_KNOWLEDGE_ONLY,
        INTENT_REQUIRES_CARD,
        INTENT_REQUIRES_APDU,
        INTENT_REQUIRES_DYNAMIC_REASONING,
        INTENT_REQUIRES_MULTI_STEP,
    ]

    for valid_intent in valid_intents:
        if valid_intent in intent_text.upper():
            return {"execution_intent": valid_intent}

    # Default fallback
    return {"execution_intent": INTENT_KNOWLEDGE_ONLY}