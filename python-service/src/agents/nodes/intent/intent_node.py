"""Intent Analyzer Node for classifying user requests.

This node analyzes the user input and determines the execution intent:
- NORMAL_CHAT: Simple chat, direct response
- RAG_DOMINANT: Knowledge query, RAG lookup needed
- TOOL_REASONING: Tool execution and reasoning needed

For greetings/fixed patterns, returns predefined response immediately.
For other inputs, uses LLM to classify intent.

Emits real-time thinking/routing events via event_queue.
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
from agents.utils.events import (
    emit_thinking,
    emit_thinking_chunk,
    emit_routing,
)


# Fixed responses for common greetings
FIXED_RESPONSES = {
    "你好": "您好！我是智能卡操作助手，可以帮您进行读卡、APDU命令执行等操作，也可以回答智能卡相关的技术问题。",
    "您好": "您好！我是智能卡操作助手，可以帮您进行读卡、APDU命令执行等操作，也可以回答智能卡相关的技术问题。",
    "hello": "您好！我是智能卡操作助手，可以帮您进行读卡、APDU命令执行等操作，也可以回答智能卡相关的技术问题。",
    "hi": "您好！我是智能卡操作助手，可以帮您进行读卡、APDU命令执行等操作，也可以回答智能卡相关的技术问题。",
    "帮助": """我可以帮助您完成以下任务：

1. **读取卡片信息**：读取IMSI、ICCID、号码等
2. **执行APDU命令**：发送和执行APDU命令
3. **探测卡片能力**：识别卡片类型和应用
4. **知识查询**：解答智能卡技术问题

请告诉我您需要什么帮助？""",
    "help": """我可以帮助您完成以下任务：

1. **读取卡片信息**：读取IMSI、ICCID、号码等
2. **执行APDU命令**：发送和执行APDU命令
3. **探测卡片能力**：识别卡片类型和应用
4. **知识查询**：解答智能卡技术问题

请告诉我您需要什么帮助？""",
    "怎么用": """我可以帮助您完成以下任务：

1. **读取卡片信息**：读取IMSI、ICCID、号码等
2. **执行APDU命令**：发送和执行APDU命令
3. **探测卡片能力**：识别卡片类型和应用
4. **知识查询**：解答智能卡技术问题

请告诉我您需要什么帮助？""",
    "功能": """我可以帮助您完成以下任务：

1. **读取卡片信息**：读取IMSI、ICCID、号码等
2. **执行APDU命令**：发送和执行APDU命令
3. **探测卡片能力**：识别卡片类型和应用
4. **知识查询**：解答智能卡技术问题

请告诉我您需要什么帮助？""",
    "谢谢": "不客气！如果还有其他问题，随时可以问我。",
    "感谢": "不客气！如果还有其他问题，随时可以问我。",
    "thanks": "不客气！如果还有其他问题，随时可以问我。",
}

# Greeting patterns that trigger fixed responses
GREETING_PATTERNS = [
    "你好", "您好", "hello", "hi", "早上好", "晚上好",
    "帮助", "help", "怎么用", "功能", "介绍",
    "谢谢", "感谢", "thanks", "不客气",
]


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


def _check_fixed_response(user_input: str) -> Dict[str, Any] | None:
    """Check if user input matches a fixed response pattern.

    Args:
        user_input: User request text

    Returns:
        State updates with fixed response, or None if no match.
    """
    input_lower = user_input.lower().strip()

    # Check for exact matches first
    if input_lower in FIXED_RESPONSES:
        return {
            "execution_intent": INTENT_NORMAL_CHAT,
            "final_response": FIXED_RESPONSES[input_lower],
            "finished": True,
        }

    # Check for greeting patterns (partial match)
    for pattern in GREETING_PATTERNS:
        if pattern == input_lower:
            # Use the pattern's response if available
            if pattern in FIXED_RESPONSES:
                return {
                    "execution_intent": INTENT_NORMAL_CHAT,
                    "final_response": FIXED_RESPONSES[pattern],
                    "finished": True,
                }

    return None


def _get_routing_reason(intent: str, user_input: str) -> str:
    """Get human-readable routing reason.

    Args:
        intent: Classified intent
        user_input: Original user input

    Returns:
        Routing reason text.
    """
    reasons = {
        INTENT_NORMAL_CHAT: "用户发起普通对话或问候，直接回复即可",
        INTENT_RAG_DOMINANT: "用户查询智能卡相关知识，需要知识库检索",
        INTENT_TOOL_REASONING: "用户请求执行卡片操作，需要工具调用和推理",
    }
    return reasons.get(intent, "未知意图类型")


def _get_routing_target(intent: str) -> str:
    """Get target node for routing.

    Args:
        intent: Classified intent

    Returns:
        Target node name.
    """
    targets = {
        INTENT_NORMAL_CHAT: "direct_answer",
        INTENT_RAG_DOMINANT: "rag_query",
        INTENT_TOOL_REASONING: "planner",
    }
    return targets.get(intent, "direct_answer")


@log_node_io("intent_node")
async def intent_node(state: AgentState) -> Dict[str, Any]:
    """Intent analyzer node function (async version).

    Analyzes the user input to determine execution intent.
    For greetings, returns fixed response immediately.
    For other inputs, uses LLM to classify intent.

    Emits real-time thinking/routing events via event_queue.

    Args:
        state: Current agent state

    Returns:
        State updates with execution_intent and optionally final_response.
    """
    import logging
    from llm.llm import get_llm, LLMConfigError

    logger = logging.getLogger(__name__)

    user_input = state["user_input"]

    # Step 1: 分析用户输入
    await emit_thinking(state, "正在分析用户输入...")
    await emit_thinking(state, f"用户输入: '{user_input}'")

    # Step 2: 检查固定回复模式
    await emit_thinking(state, "检查是否匹配固定回复模式...")
    fixed_result = _check_fixed_response(user_input)

    if fixed_result:
        await emit_thinking(state, "✓ 匹配固定回复模式")
        await emit_routing(
            state,
            from_node="intent",
            to_node="direct_answer",
            reason="匹配问候语/帮助请求等固定模式",
        )
        logger.info(f"[DEBUG] intent_node: matched fixed response for '{user_input}'")
        return fixed_result

    await emit_thinking(state, "✗ 未匹配固定回复模式")

    # Step 3: LLM 意图分类
    await emit_thinking(state, "调用 LLM 进行意图分类...")

    try:
        llm = get_llm()
        chain = INTENT_PROMPT | llm

        # 使用流式接口获取 LLM 输出
        accumulated_response = ""
        async for chunk in chain.astream({"input": user_input}):
            chunk_content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            accumulated_response += chunk_content
            # 推送 LLM 输出片段
            await emit_thinking_chunk(state, chunk_content)

        # 解析意图
        intent_text = accumulated_response.strip().upper()

        await emit_thinking(state, f"LLM 输出: '{intent_text}'")

        # Normalize to valid intent
        valid_intents = [
            INTENT_NORMAL_CHAT,
            INTENT_RAG_DOMINANT,
            INTENT_TOOL_REASONING,
        ]

        intent = INTENT_NORMAL_CHAT  # Default
        for valid_intent in valid_intents:
            if valid_intent in intent_text or valid_intent.replace("_", " ") in intent_text:
                intent = valid_intent
                break

        await emit_thinking(state, f"意图分类结果: {intent}")

        # Step 4: 路由决策
        routing_target = _get_routing_target(intent)
        routing_reason = _get_routing_reason(intent, user_input)

        await emit_routing(
            state,
            from_node="intent",
            to_node=routing_target,
            reason=routing_reason,
        )

        logger.info(f"[DEBUG] intent_node: LLM classified intent={intent}")

        return {
            "execution_intent": intent,
        }

    except LLMConfigError as e:
        await emit_thinking(state, f"⚠ LLM 未配置: {e}")
        await emit_routing(
            state,
            from_node="intent",
            to_node="direct_answer",
            reason="LLM 未配置，降级为普通对话",
        )
        logger.warning(f"LLM not configured: {e}")
        return {
            "execution_intent": INTENT_NORMAL_CHAT,
            "final_response": "请先在设置中配置 API Key，然后再开始对话。",
            "finished": True,
        }

    except Exception as e:
        await emit_thinking(state, f"⚠ LLM 调用失败: {e}")
        await emit_routing(
            state,
            from_node="intent",
            to_node="direct_answer",
            reason="LLM 调用失败，降级为普通对话",
        )
        logger.error(f"LLM call failed: {e}")
        return {
            "execution_intent": INTENT_NORMAL_CHAT,
            "final_response": f"处理过程中发生错误，请稍后重试。",
            "finished": True,
        }


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

    # 流式输出
    accumulated_response = ""
    async for chunk in chain.astream({"input": state["user_input"]}):
        chunk_content = chunk.content if hasattr(chunk, 'content') else str(chunk)
        accumulated_response += chunk_content
        await emit_thinking_chunk(state, chunk_content)

    # Parse intent from LLM response
    intent_text = accumulated_response.strip().upper()

    # Normalize to valid intent
    valid_intents = [
        INTENT_NORMAL_CHAT,
        INTENT_RAG_DOMINANT,
        INTENT_TOOL_REASONING,
    ]

    for valid_intent in valid_intents:
        if valid_intent in intent_text or valid_intent.replace("_", " ") in intent_text:
            await emit_routing(
                state,
                from_node="intent",
                to_node=_get_routing_target(valid_intent),
                reason=_get_routing_reason(valid_intent, state["user_input"]),
            )
            return {"execution_intent": valid_intent}

    # Default fallback
    await emit_routing(
        state,
        from_node="intent",
        to_node="rag_query",
        reason="无法明确分类，默认走知识查询路径",
    )
    return {"execution_intent": INTENT_RAG_DOMINANT}