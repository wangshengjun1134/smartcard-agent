"""Prompt templates for agent nodes.

This module contains prompt templates used by various agent nodes.
"""

from langchain_core.prompts import ChatPromptTemplate


# Intent classification prompt
INTENT_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个智能卡操作意图分析器。

分析用户请求，确定执行意图类型。

可选意图类型：
- KNOWLEDGE_ONLY: 仅知识库查询，不需要卡片操作
- REQUIRES_CARD: 需要读卡操作
- REQUIRES_APDU: 需要APDU命令执行
- REQUIRES_DYNAMIC_REASONING: 需要动态推理（如探索卡能力）
- REQUIRES_MULTI_STEP: 要多步骤执行（如建立安全通道）"""),
    ("user", "{input}"),
])


# Goal planning prompt
GOAL_PLANNING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个智能卡操作目标规划器。

根据用户请求生成高层目标。

目标示例：
- read_imsi: 读取IMSI
- read_iccid: 读取ICCID
- discover_card: 探测卡片能力
- establish_secure_channel: 建立安全通道

不要生成完整APDU流程，只生成高层目标名称。"""),
    ("user", "用户请求: {input}\n执行意图: {intent}"),
])


# Runtime think prompt
RUNTIME_THINK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个智能卡操作推理节点。

分析当前状态，决定下一步要执行的Skill。

可选Skills：
- select_file: 选择文件 (参数: fid)
- read_binary: 读取二进制数据
- read_imsi: 读取IMSI
- read_iccid: 读取ICCID
- discover_card: 探测卡片
- verify_pin: 验证PIN

请返回下一步Skill和参数。"""),
    ("user", """当前目标: {goal}
Runtime状态: {runtime_state}
历史执行: {observations}"""),
])


# Finalize response prompt
FINALIZE_RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个智能卡操作结果总结节点。

根据执行历史生成用户友好的响应。

如果成功，说明完成了什么。
如果失败，解释原因并给出建议。"""),
    ("user", """用户请求: {user_input}
目标: {goal}
执行历史: {observations}
是否有错误: {has_error}"""),
])


# Error explanation prompt
ERROR_EXPLANATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是智能卡错误分析专家。

解释APDU执行失败的错误码含义，并给出可能的原因和建议。"""),
    ("user", "状态码: {sw}\n描述: {description}\n操作: {operation}"),
])


# SW code lookup prompt
SW_LOOKUP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是智能卡规范查询助手。

查询相关规范文档，解释特定状态码的含义和使用场景。"""),
    ("user", "状态码: {sw}\n需要查询: {query}"),
])


# Card capability analysis prompt
CAPABILITY_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是智能卡能力分析专家。

根据ATR和探测结果分析卡片类型和功能。"""),
    ("user", """ATR: {atr}
发现的应用: {apps}
探测结果: {probe_results}"""),
])


# All prompts collection
ALL_PROMPTS = {
    "intent_classification": INTENT_CLASSIFICATION_PROMPT,
    "goal_planning": GOAL_PLANNING_PROMPT,
    "runtime_think": RUNTIME_THINK_PROMPT,
    "finalize_response": FINALIZE_RESPONSE_PROMPT,
    "error_explanation": ERROR_EXPLANATION_PROMPT,
    "sw_lookup": SW_LOOKUP_PROMPT,
    "capability_analysis": CAPABILITY_ANALYSIS_PROMPT,
}


def get_prompt(name: str) -> ChatPromptTemplate:
    """Get a prompt template by name.

    Args:
        name: Prompt template name

    Returns:
        ChatPromptTemplate instance.

    Raises:
        KeyError: If prompt not found.
    """
    return ALL_PROMPTS[name]