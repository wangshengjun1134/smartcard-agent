"""Proactive RAG Node for active knowledge retrieval.

This node performs proactive RAG lookup when knowledge gaps
are detected during execution.
"""

from typing import Dict, Any, List

from agents.graph.state import AgentState
from agents.nodes.logging_utils import log_node_io


@log_node_io("proactive_rag_node")
def proactive_rag_node(state: AgentState) -> Dict[str, Any]:
    """Proactive RAG node function.

    Proactively retrieves knowledge based on current goal
    and detected knowledge gaps.

    Args:
        state: Current agent state

    Returns:
        State updates with rag_query and rag_context.
    """
    current_goal = state["current_goal"]
    runtime_state = state["runtime_state"]
    observations = state["observations"]

    # Build proactive RAG query
    rag_query = build_proactive_rag_query(
        goal=current_goal,
        knowledge_gap=runtime_state.get("knowledge_gap", ""),
        last_observation=observations[-1] if observations else None,
    )

    # Retrieve from RAG
    rag_context = retrieve_proactive_knowledge(rag_query)

    return {
        "rag_query": rag_query,
        "rag_context": rag_context,
        "finished": False,
    }


def build_proactive_rag_query(
    goal: str,
    knowledge_gap: str,
    last_observation: Dict[str, Any] | None,
) -> str:
    """Build proactive RAG query from execution context.

    Args:
        goal: Current goal
        knowledge_gap: Detected knowledge gap
        last_observation: Last execution observation

    Returns:
        RAG query string.
    """
    # Base query from goal
    goal_queries = {
        "establish_secure_channel": "SCP03 SCP80 安全通道建立流程规范",
        "scp03_initialize": "SCP03 初始化命令序列 GlobalPlatform规范",
        "scp80_initialize": "SCP80 初始化命令序列 GlobalPlatform规范",
        "profile_download": "eUICC Profile下载流程 GSPA规范",
        "gp_install_applet": "GlobalPlatform Applet安装命令序列",
    }

    base_query = goal_queries.get(goal, f"{goal} 操作流程")

    # Add knowledge gap context
    if knowledge_gap:
        query = f"{base_query} {knowledge_gap}"
    else:
        query = base_query

    # Add error context if from observation
    if last_observation and not last_observation.get("success"):
        sw = last_observation.get("sw", "")
        skill = last_observation.get("skill_name", "")
        if sw:
            query += f" SW错误码{sw}含义 {skill}"

    return query


def retrieve_proactive_knowledge(query: str) -> List[str]:
    """Retrieve knowledge proactively from RAG.

    Args:
        query: Query string

    Returns:
        List of retrieved documents.
    """
    from config.settings import get_settings

    settings = get_settings()

    if not settings.RAG_ENABLED:
        return []

    try:
        from services.rag_service import RAGService

        rag_service = RAGService()
        docs = rag_service.search(query, top_k=settings.RAG_TOP_K)

        return [doc.get("content", "") for doc in docs]

    except Exception as e:
        print(f"[ProactiveRAG] Retrieval error: {e}")
        return []


@log_node_io("proactive_rag_node_with_llm")
async def proactive_rag_node_with_llm(state: AgentState, llm: Any) -> Dict[str, Any]:
    """Proactive RAG node using LLM for query generation.

    Args:
        state: Current agent state
        llm: LangChain LLM instance

    Returns:
        State updates.
    """
    from langchain_core.prompts import ChatPromptTemplate

    goal = state["current_goal"]
    knowledge_gap = state["runtime_state"].get("knowledge_gap", "")
    observations = state["observations"]

    # Use LLM to generate optimal query
    prompt = ChatPromptTemplate.from_template("""
你是一个智能卡知识检索专家。

根据执行上下文生成最优的知识库检索查询。

当前目标: {goal}
知识缺口: {gap}
最近执行结果: {observations}

生成一个精确的检索查询，用于获取执行下一步所需的知识。
仅返回查询文本：
""")

    chain = prompt | llm
    result = chain.invoke({
        "goal": goal,
        "gap": knowledge_gap or "无",
        "observations": str(observations[-2:]),
    })

    rag_query = result.content.strip()

    # Retrieve from RAG
    rag_context = retrieve_proactive_knowledge(rag_query)

    return {
        "rag_query": rag_query,
        "rag_context": rag_context,
        "finished": False,
    }