"""RAG Query Node for knowledge-dominant queries.

This node handles queries that primarily need RAG lookup
for knowledge retrieval.
"""

from typing import Dict, Any

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("rag_query_node")
def rag_query_node(state: AgentState) -> Dict[str, Any]:
    """RAG query node function.

    Prepares the RAG query from user input.

    Args:
        state: Current agent state

    Returns:
        State updates with rag_query.
    """
    user_input = state["user_input"]

    # Prepare RAG query
    rag_query = prepare_rag_query(user_input)

    return {
        "rag_query": rag_query,
        "finished": False,
    }


def prepare_rag_query(user_input: str) -> str:
    """Prepare optimized RAG query from user input.

    Args:
        user_input: User request text

    Returns:
        Optimized query string for RAG lookup.
    """
    # Extract key terms and context
    # This could be enhanced with query expansion

    # For smart card domain, add context keywords
    domain_keywords = [
        "智能卡", "SIM卡", "USIM", "APDU", 
        "ISO 7816", "GlobalPlatform", "SCP",
        "PIN", "PUK", "IMSI", "ICCID",
    ]

    # Check if query already contains domain keywords
    has_domain_context = any(kw in user_input for kw in domain_keywords)

    if has_domain_context:
        # Query is already domain-specific
        return user_input

    # Add context for generic queries
    return f"智能卡 {user_input}"


@log_node_io("rag_query_node_with_llm")
async def rag_query_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """RAG query node using LLM for query optimization.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with optimized rag_query.
    """
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡知识查询优化器。

优化用户查询，使其更适合知识库检索。
保留核心问题，添加必要的智能卡领域上下文。

用户原始输入: {input}

请返回优化后的查询，仅返回查询文本：
""")

    chain = prompt | llm
    result = chain.invoke({"input": state["user_input"]})

    return {
        "rag_query": result.content.strip(),
        "finished": False,
    }