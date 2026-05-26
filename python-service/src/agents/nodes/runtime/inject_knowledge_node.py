"""Inject Knowledge Node for injecting RAG results into context.

This node processes RAG results and injects knowledge
into the execution context.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("inject_knowledge_node")
def inject_knowledge_node(state: AgentState) -> Dict[str, Any]:
    """Inject knowledge node function.

    Processes and injects RAG context into execution context.

    Args:
        state: Current agent state

    Returns:
        State updates with injected_knowledge.
    """
    rag_context = state["rag_context"]
    current_goal = state["current_goal"]

    # Process RAG context into injectable knowledge
    injected_knowledge = process_knowledge_for_injection(
        rag_context=rag_context,
        goal=current_goal,
    )

    return {
        "injected_knowledge": injected_knowledge,
        "finished": False,
    }


def process_knowledge_for_injection(
    rag_context: List[str],
    goal: str,
) -> str:
    """Process RAG context for injection.

    Args:
        rag_context: Raw RAG documents
        goal: Current goal for context

    Returns:
        Processed knowledge string for injection.
    """
    if not rag_context:
        return ""

    # Combine and format context
    combined = "\n\n".join(rag_context[:3])  # Use top 3 documents

    # Format as injectable knowledge
    injected = f"""
[知识库参考 - {goal}]

{combined}

[执行提示: 请参考以上知识进行下一步操作]
"""

    return injected.strip()


@log_node_io("inject_knowledge_node_with_llm")
async def inject_knowledge_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Inject knowledge node using LLM for knowledge extraction.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with processed injected_knowledge.
    """
    from langchain_core.prompts import ChatPromptTemplate

    rag_context = state["rag_context"]
    goal = state["current_goal"]

    if not rag_context:
        return {
            "injected_knowledge": "",
            "finished": False,
        }

    # Use LLM to extract and summarize relevant knowledge
    context_str = "\n".join(rag_context)

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡知识提取专家。

从以下知识库内容中提取与目标 "{goal}" 最相关的操作要点。

知识库内容:
{context}

请提取关键信息，格式如下：
1. 命令序列要点
2. 参数要求
3. 注意事项

提取结果：
""")

    chain = prompt | llm
    result = chain.invoke({
        "goal": goal,
        "context": context_str,
    })

    injected_knowledge = f"""
[知识库参考 - {goal}]
{result.content.strip()}
"""

    return {
        "injected_knowledge": injected_knowledge.strip(),
        "finished": False,
    }