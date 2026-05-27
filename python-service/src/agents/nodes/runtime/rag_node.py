"""Runtime RAG Node for querying knowledge base during execution.

This node queries the RAG knowledge base when SW errors occur,
providing context for error explanation and recovery strategies.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io
from apdu.constants.sw_codes import decode_sw


@log_node_io("runtime_rag_node")
def runtime_rag_node(state: AgentState) -> Dict[str, Any]:
    """Runtime RAG node function.

    Queries the knowledge base for SW error explanation
    and recovery strategies.

    Args:
        state: Current agent state

    Returns:
        State updates with rag_context and need_rag=False.
    """
    observations = state["observations"]

    if not observations:
        return {
            "need_rag": False,
            "rag_context": [],
        }

    # Get last observation
    last_obs = observations[-1]
    sw = last_obs.get("sw", "")
    skill_name = last_obs.get("skill_name", "")

    if not sw:
        return {
            "need_rag": False,
            "rag_context": [],
        }

    # Build query for RAG lookup
    sw_description = decode_sw(sw)

    # Query patterns for different scenarios
    queries = []

    # 1. SW code explanation
    queries.append(f"Status Word {sw} meaning in smart card specification")

    # 2. Error recovery for specific skill
    if skill_name and not last_obs.get("success"):
        queries.append(f"{skill_name} skill failure recovery {sw}")

    # 3. Security condition errors
    if sw in ["6982", "6983", "6984"]:
        queries.append("Security condition not satisfied PIN verification")

    # 4. File errors
    if sw in ["6A82", "6A83"]:
        queries.append("File not found card structure navigation")

    # Retrieve documents
    rag_context = retrieve_from_rag(queries)

    return {
        "rag_context": rag_context,
        "need_rag": False,
    }


def retrieve_from_rag(queries: List[str]) -> List[str]:
    """Retrieve documents from RAG for multiple queries.

    Args:
        queries: List of query strings

    Returns:
        List of retrieved document contents.
    """
    from config.settings import get_settings

    settings = get_settings()

    if not settings.RAG_ENABLED:
        return []

    # Import RAG service
    try:
        from services.rag_service import RAGService

        rag_service = RAGService()

        results = []
        for query in queries:
            docs = rag_service.search(query, k=settings.RAG_TOP_K)
            for doc in docs:
                results.append(doc.get("content", ""))

        return results

    except Exception:
        # Fallback: return SW description as context
        return [
            f"SW code explanation from knowledge base: {decode_sw(queries[0].split()[2])}"
        ]


def build_rag_prompt(sw: str, skill_name: str, rag_context: List[str]) -> str:
    """Build prompt with RAG context for error recovery.

    Args:
        sw: Status word
        skill_name: Failed skill name
        rag_context: Retrieved RAG documents

    Returns:
        Prompt string for LLM.
    """
    sw_desc = decode_sw(sw)

    context_str = "\n".join(rag_context) if rag_context else "No context available."

    prompt = f"""
A smart card operation failed with the following error:

Skill: {skill_name}
Status Word: {sw}
Description: {sw_desc}

Knowledge Base Context:
{context_str}

Based on this context, please:
1. Explain why the operation failed
2. Suggest recovery strategies
3. Recommend next steps

Response:
"""

    return prompt


@log_node_io("runtime_rag_node_with_llm")
async def runtime_rag_node_with_llm(
    state: AgentState,
    llm: Any,
) -> Dict[str, Any]:
    """Runtime RAG node using LLM for analysis.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates with analyzed RAG context.
    """
    from langchain_core.prompts import ChatPromptTemplate

    observations = state["observations"]

    if not observations:
        return {"need_rag": False, "rag_context": []}

    last_obs = observations[-1]
    sw = last_obs.get("sw", "")
    skill_name = last_obs.get("skill_name", "")

    if not sw:
        return {"need_rag": False, "rag_context": []}

    # Retrieve from RAG
    queries = [
        f"Status Word {sw} meaning",
        f"{skill_name} failure recovery",
    ]
    rag_context = retrieve_from_rag(queries)

    # Use LLM to analyze
    prompt = build_rag_prompt(sw, skill_name, rag_context)

    result = llm.invoke(prompt)

    # Add LLM analysis to context
    enhanced_context = rag_context + [f"LLM Analysis: {result.content}"]

    return {
        "rag_context": enhanced_context,
        "need_rag": False,
    }