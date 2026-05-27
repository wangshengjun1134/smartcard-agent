"""Answer From RAG Node for generating response from RAG results.

This node generates the final response based on RAG-retrieved
knowledge.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("answer_from_rag_node")
def answer_from_rag_node(state: AgentState) -> Dict[str, Any]:
    """Answer from RAG node function.

    Queries RAG and generates response.

    Args:
        state: Current agent state

    Returns:
        State updates with rag_context and final_response.
    """
    rag_query = state["rag_query"]

    # Retrieve from RAG
    rag_context = retrieve_from_rag(rag_query)

    # Generate response from context
    final_response = generate_rag_response(rag_query, rag_context)

    return {
        "rag_context": rag_context,
        "final_response": final_response,
        "finished": True,
    }


def retrieve_from_rag(query: str) -> List[str]:
    """Retrieve documents from RAG.

    Args:
        query: Query string

    Returns:
        List of retrieved document contents.
    """
    from config.settings import get_settings

    settings = get_settings()

    if not settings.RAG_ENABLED:
        return []

    try:
        from services.rag_service import RAGService

        rag_service = RAGService()
        docs = rag_service.search(query, k=settings.RAG_TOP_K)

        return [doc.get("content", "") for doc in docs]

    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        return []


def generate_rag_response(query: str, rag_context: List[str]) -> str:
    """Generate response from RAG context.

    Args:
        query: Original query
        rag_context: Retrieved documents

    Returns:
        Response string.
    """
    if not rag_context:
        return f"抱歉，知识库中没有找到关于 '{query}' 的相关信息。请尝试换一种方式描述您的问题。"

    # Combine context
    context_str = "\n\n".join(rag_context[:3])  # Use top 3 documents

    # Simple template-based response
    response = f"""根据知识库信息，为您解答：

{context_str}

如需更详细的说明或有其他问题，请继续提问。"""

    return response


@log_node_io("answer_from_rag_node_with_llm")
async def answer_from_rag_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Answer from RAG node using LLM.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with LLM-synthesized response.
    """
    from langchain_core.prompts import ChatPromptTemplate

    rag_query = state["rag_query"]

    # Retrieve from RAG
    rag_context = retrieve_from_rag(rag_query)

    if not rag_context:
        return {
            "rag_context": [],
            "final_response": f"抱歉，知识库中没有找到关于 '{rag_query}' 的相关信息。",
            "finished": True,
        }

    # Use LLM to synthesize answer
    context_str = "\n\n".join(rag_context)

    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡技术专家。

根据以下知识库内容回答用户问题。

知识库内容:
{context}

用户问题: {query}

请给出专业、准确的回答：
""")

    chain = prompt | llm
    result = chain.invoke({
        "context": context_str,
        "query": rag_query,
    })

    return {
        "rag_context": rag_context,
        "final_response": result.content.strip(),
        "finished": True,
    }