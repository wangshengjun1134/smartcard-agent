"""LangGraph Workflow for the Runtime Agent - UPDATED.

This module defines the StateGraph workflow that orchestrates
the agent nodes according to the specified flowchart:

Flow:
    Start → Intent
    Intent →|NORMAL_CHAT| DirectAnswer → Finalize
    Intent →|RAG_DOMINANT| RagQuery → AnswerFromRag → Finalize
    Intent →|TOOL_REASONING| Planner

    [ComplexTask subgraph]
    Planner → InputPrepare → Think → SkillSelect → SkillExec → Observe
    Observe → StateRouter
    StateRouter →|SUCCESS_COMPLETE| Finalize
    StateRouter →|SUCCESS_CONTINUE| UpdateState → InputPrepare
    StateRouter →|NEEDS_KNOWLEDGE| ProactiveRAG → InjectKnowledge → InputPrepare
    StateRouter →|RETRYABLE (not exceeded)| Retry → UpdateRetryCount → InputPrepare
    StateRouter →|RETRYABLE_EXCEEDED| Finalize
    StateRouter →|NEEDS_USER_INPUT| UserConfirm → WaitUserResponse → InputPrepare
    StateRouter →|FATAL_ERROR| Finalize
    StateRouter →|NEEDS_REPLAN| RePlan → Planner

    Finalize → End
"""

from typing import Literal, Any, Dict
import json
import asyncio
from langgraph.graph import StateGraph, END

from agents.graph.state import AgentState, create_initial_state
from agents.graph.state import (
    INTENT_NORMAL_CHAT,
    INTENT_RAG_DOMINANT,
    INTENT_TOOL_REASONING,
    EXEC_STATUS_SUCCESS_COMPLETE,
    EXEC_STATUS_SUCCESS_CONTINUE,
    EXEC_STATUS_NEEDS_KNOWLEDGE,
    EXEC_STATUS_RETRYABLE,
    EXEC_STATUS_RETRYABLE_EXCEEDED,
    EXEC_STATUS_NEEDS_USER_INPUT,
    EXEC_STATUS_FATAL_ERROR,
    EXEC_STATUS_NEEDS_REPLAN,
)

# Import all nodes
from agents.nodes.intent.intent_node import intent_node
from agents.nodes.runtime.direct_answer_node import direct_answer_node
from agents.nodes.runtime.rag_query_node import rag_query_node
from agents.nodes.runtime.answer_from_rag_node import answer_from_rag_node
from agents.nodes.planner.goal_planner_node import goal_planner_node
from agents.nodes.runtime.input_prepare_node import input_prepare_node
from agents.nodes.runtime.think_node import think_node
from agents.nodes.skill.skill_selector_node import skill_selector_node
from agents.nodes.skill.skill_runtime_node import skill_runtime_node
from agents.nodes.runtime.observe_node import observe_node
from agents.nodes.runtime.state_router_node import state_router_node, get_routing_decision
from agents.nodes.runtime.update_state_node import update_state_node
from agents.nodes.runtime.retry_node import retry_node
from agents.nodes.runtime.update_retry_count_node import update_retry_count_node
from agents.nodes.runtime.proactive_rag_node import proactive_rag_node
from agents.nodes.runtime.inject_knowledge_node import inject_knowledge_node
from agents.nodes.runtime.user_confirm_node import user_confirm_node
from agents.nodes.runtime.wait_user_response_node import wait_user_response_node
from agents.nodes.planner.replan_node import replan_node
from agents.nodes.runtime.finalize_node import finalize_node


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow.

    Returns:
        StateGraph instance.
    """
    workflow = StateGraph(AgentState)

    # ========================================
    # Add all nodes
    # ========================================

    # Entry node
    workflow.add_node("intent", intent_node)

    # Intent branch nodes
    workflow.add_node("direct_answer", direct_answer_node)
    workflow.add_node("rag_query", rag_query_node)
    workflow.add_node("answer_from_rag", answer_from_rag_node)

    # Complex task nodes
    workflow.add_node("planner", goal_planner_node)
    workflow.add_node("input_prepare", input_prepare_node)
    workflow.add_node("think", think_node)
    workflow.add_node("skill_selector", skill_selector_node)
    workflow.add_node("skill_runtime", skill_runtime_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("state_router", state_router_node)

    # State router branch nodes
    workflow.add_node("update_state", update_state_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("update_retry_count", update_retry_count_node)
    workflow.add_node("proactive_rag", proactive_rag_node)
    workflow.add_node("inject_knowledge", inject_knowledge_node)
    workflow.add_node("user_confirm", user_confirm_node)
    workflow.add_node("wait_user_response", wait_user_response_node)
    workflow.add_node("replan", replan_node)

    # Exit node
    workflow.add_node("finalize", finalize_node)

    # ========================================
    # Set entry point
    # ========================================
    workflow.set_entry_point("intent")

    # ========================================
    # Intent routing (3 branches)
    # ========================================
    def route_after_intent(state: AgentState) -> Literal["direct_answer", "rag_query", "planner"]:
        """Route based on execution_intent.

        Routes:
        - NORMAL_CHAT → direct_answer
        - RAG_DOMINANT → rag_query
        - TOOL_REASONING → planner
        """
        intent = state["execution_intent"]
        print(f"[DEBUG] route_after_intent: intent={intent}")

        if intent == INTENT_NORMAL_CHAT:
            print(f"[DEBUG] Routing to direct_answer")
            return "direct_answer"
        elif intent == INTENT_RAG_DOMINANT:
            print(f"[DEBUG] Routing to rag_query")
            return "rag_query"
        else:  # TOOL_REASONING
            print(f"[DEBUG] Routing to planner")
            return "planner"

    workflow.add_conditional_edges(
        "intent",
        route_after_intent,
        {
            "direct_answer": "direct_answer",
            "rag_query": "rag_query",
            "planner": "planner",
        }
    )

    # Direct answer branch
    workflow.add_edge("direct_answer", "finalize")

    # RAG branch
    workflow.add_edge("rag_query", "answer_from_rag")
    workflow.add_edge("answer_from_rag", "finalize")

    # ========================================
    # Complex task flow
    # ========================================
    # Planner → InputPrepare → Think → SkillSelect → SkillExec → Observe
    workflow.add_edge("planner", "input_prepare")
    workflow.add_edge("input_prepare", "think")
    workflow.add_edge("think", "skill_selector")
    workflow.add_edge("skill_selector", "skill_runtime")
    workflow.add_edge("skill_runtime", "observe")

    # Observe → StateRouter (pass-through node for routing)
    workflow.add_edge("observe", "state_router")

    # ========================================
    # State router routing (8 branches)
    # ========================================
    def route_after_state_router(state: AgentState) -> Literal[
        "finalize",
        "update_state",
        "proactive_rag",
        "retry",
        "user_confirm",
        "replan",
    ]:
        """Route based on execution_status.

        Routes:
        - SUCCESS_COMPLETE → finalize
        - SUCCESS_CONTINUE → update_state
        - NEEDS_KNOWLEDGE → proactive_rag
        - RETRYABLE → retry (if not exceeded)
        - RETRYABLE_EXCEEDED → finalize
        - NEEDS_USER_INPUT → user_confirm
        - FATAL_ERROR → finalize
        - NEEDS_REPLAN → replan
        """
        return get_routing_decision(state)

    workflow.add_conditional_edges(
        "state_router",
        route_after_state_router,
        {
            "finalize": "finalize",
            "update_state": "update_state",
            "proactive_rag": "proactive_rag",
            "retry": "retry",
            "user_confirm": "user_confirm",
            "replan": "replan",
        }
    )

    # ========================================
    # State router branch paths
    # ========================================

    # SUCCESS_CONTINUE: UpdateState → InputPrepare (loop back)
    workflow.add_edge("update_state", "input_prepare")

    # NEEDS_KNOWLEDGE: ProactiveRAG → InjectKnowledge → InputPrepare
    workflow.add_edge("proactive_rag", "inject_knowledge")
    workflow.add_edge("inject_knowledge", "input_prepare")

    # RETRYABLE: Retry → UpdateRetryCount → InputPrepare
    workflow.add_edge("retry", "update_retry_count")
    workflow.add_edge("update_retry_count", "input_prepare")

    # NEEDS_USER_INPUT: UserConfirm → WaitUserResponse → InputPrepare
    workflow.add_edge("user_confirm", "wait_user_response")
    workflow.add_edge("wait_user_response", "input_prepare")

    # NEEDS_REPLAN: RePlan → Planner (loop back to start of complex task)
    workflow.add_edge("replan", "planner")

    # ========================================
    # Finalize → END
    # ========================================
    workflow.add_edge("finalize", END)

    return workflow


def compile_workflow() -> Any:
    """Compile the workflow into an executable graph.

    Returns:
        Compiled LangGraph.
    """
    workflow = create_workflow()
    return workflow.compile()


# Global compiled graph (cleared on module reload)
_graph = None


def get_graph() -> Any:
    """Get the compiled workflow graph.

    Returns:
        Compiled LangGraph instance.
    """
    global _graph
    # Always recompile to pick up latest changes (for development)
    _graph = compile_workflow()
    return _graph


def run_agent(user_input: str) -> Dict[str, Any]:
    """Run the agent with user input.

    Args:
        user_input: User request text

    Returns:
        Final agent state with response.
    """
    graph = get_graph()
    initial_state = create_initial_state(user_input)

    result = graph.invoke(initial_state)

    return result


async def run_agent_async(user_input: str) -> Dict[str, Any]:
    """Run the agent asynchronously.

    Args:
        user_input: User request text

    Returns:
        Final agent state.
    """
    print(f"[DEBUG] run_agent_async called with input: {user_input}")

    graph = get_graph()
    initial_state = create_initial_state(user_input)

    print(f"[DEBUG] Initial state created, invoking graph...")

    result = await graph.ainvoke(initial_state)

    print(f"[DEBUG] Graph execution completed")

    return result


async def stream_agent(user_input: str, session_id: str = None):
    """Stream agent execution with SSE format.

    Uses asyncio.Queue to receive real-time events from nodes,
    providing live thinking/routing updates to the frontend.

    Args:
        user_input: User request text
        session_id: Session ID for saving assistant response

    Yields:
        SSE formatted strings with real-time events.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[DEBUG] stream_agent called with input: {user_input}, session_id: {session_id}")

    # Create event queue for real-time streaming
    event_queue = asyncio.Queue()

    # Create initial state with event_queue
    initial_state = create_initial_state(user_input, event_queue)

    accumulated_response = ""
    thinking_steps = []  # 收集思考过程
    routing_decision = None  # 收集路由决策
    graph_done = False
    final_result = None

    # Start graph execution in background
    async def run_graph():
        """Run the graph and signal completion."""
        nonlocal graph_done, final_result
        graph = get_graph()
        try:
            final_result = await graph.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            await event_queue.put({
                "type": "error",
                "error": str(e),
            })
        finally:
            graph_done = True
            # Signal end of stream
            await event_queue.put({"type": "stream_end"})

    graph_task = asyncio.create_task(run_graph())

    # Main loop: poll queue and yield SSE events
    while True:
        # Check if graph is done and queue is empty
        if graph_done and event_queue.empty():
            break

        # Try to get event from queue (with timeout)
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=0.05)
        except asyncio.TimeoutError:
            # No event available, continue polling
            continue

        # Format and yield SSE event
        yield _format_event_sse(event)

        # Track content for final response
        if event.get("type") == "content":
            accumulated_response += event.get("data", "")
        elif event.get("type") == "done":
            accumulated_response = event.get("response", accumulated_response)
        # 收集思考过程
        elif event.get("type") == "thinking":
            thinking_steps.append(event.get("data", ""))
        elif event.get("type") == "thinking_chunk":
            # thinking_chunk 追加到最后一步
            chunk = event.get("data", "")
            if thinking_steps:
                thinking_steps[-1] += chunk
            else:
                thinking_steps.append(chunk)
        # 收集路由决策
        elif event.get("type") == "routing":
            routing_decision = {
                "from": event.get("from", ""),
                "to": event.get("to", ""),
                "reason": event.get("reason", ""),
                "confidence": event.get("confidence"),
            }

    # Wait for graph task to complete
    await graph_task

    # If we have a final result, ensure we yield done event
    if final_result and final_result.get("final_response"):
        final_response = final_result.get("final_response")
        if final_response != accumulated_response:
            yield f"data: {json.dumps({'type': 'content', 'content': final_response})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'response': final_response})}\n\n"
        accumulated_response = final_response

    # Fallback if no response
    if not accumulated_response:
        yield f"data: {json.dumps({'type': 'done', 'response': '处理完成'})}\n\n"
        accumulated_response = "处理完成"

    # Save assistant response to database with thinking process
    if session_id and accumulated_response:
        # 将思考过程保存为 JSON 格式
        thinking_data = {
            "steps": thinking_steps,
            "routing": routing_decision,
        }
        thinking_json = json.dumps(thinking_data, ensure_ascii=False)
        # 将思考过程也保存为纯文本用于显示
        thinking_text = '\n\n'.join(thinking_steps) if thinking_steps else None
        _update_assistant_message(session_id, accumulated_response, thinking_json, thinking_text)


def _format_event_sse(event: Dict[str, Any]) -> str:
    """Format an event dict as SSE string.

    Args:
        event: Event dictionary with type and data

    Returns:
        SSE formatted string.
    """
    event_type = event.get("type", "unknown")

    # Format based on event type
    if event_type == "thinking":
        return f"data: {json.dumps({'type': 'thinking', 'content': event.get('data', '')})}\n\n"

    elif event_type == "thinking_chunk":
        return f"data: {json.dumps({'type': 'thinking_chunk', 'content': event.get('data', '')})}\n\n"

    elif event_type == "routing":
        routing_data = {
            "type": "routing",
            "from": event.get("from", ""),
            "to": event.get("to", ""),
            "reason": event.get("reason", ""),
        }
        if event.get("confidence"):
            routing_data["confidence"] = event.get("confidence")
        return f"data: {json.dumps(routing_data)}\n\n"

    elif event_type == "action":
        action_data = {
            'type': 'action',
            'action': event.get('action', ''),
            'status': event.get('status', ''),
            'details': event.get('details', {}),
        }
        return f"data: {json.dumps(action_data)}\n\n"

    elif event_type == "observation":
        obs_data = {
            'type': 'observation',
            'skill': event.get('skill', ''),
            'success': event.get('success', False),
            'result': event.get('result'),
            'error': event.get('error'),
        }
        return f"data: {json.dumps(obs_data)}\n\n"

    elif event_type == "node_start":
        return f"data: {json.dumps({'type': 'node', 'node': event.get('node', ''), 'status': 'start'})}\n\n"

    elif event_type == "node_end":
        return f"data: {json.dumps({'type': 'node', 'node': event.get('node', ''), 'status': 'end'})}\n\n"

    elif event_type == "content":
        return f"data: {json.dumps({'type': 'content', 'content': event.get('data', '')})}\n\n"

    elif event_type == "done":
        return f"data: {json.dumps({'type': 'done', 'response': event.get('response', '')})}\n\n"

    elif event_type == "error":
        return f"data: {json.dumps({'type': 'error', 'error': event.get('error', '')})}\n\n"

    elif event_type == "stream_end":
        # Internal signal, don't emit to SSE
        return ""

    else:
        # Unknown event type, just pass through
        return f"data: {json.dumps(event)}\n\n"


def _update_assistant_message(session_id: str, content: str, thinking_process: str = None, thinking_content: str = None):
    """Update the last assistant message in database.

    Args:
        session_id: Session ID
        content: Message content to update
        thinking_process: Optional thinking/reasoning process JSON string
        thinking_content: Optional raw thinking text
    """
    from utils.database import get_session_db_connection

    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Find the last assistant message in this session
    cursor.execute(
        """
        SELECT id FROM messages
        WHERE session_id = ? AND role = 'assistant'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (session_id,)
    )
    row = cursor.fetchone()

    if row:
        message_id = row["id"]
        cursor.execute(
            "UPDATE messages SET content = ?, thinking_process = ?, thinking_content = ? WHERE id = ?",
            (content, thinking_process, thinking_content, message_id)
        )
        conn.commit()
        conn.close()
    else:
        # No assistant message found, create one
        import time
        import uuid
        message_id = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:9]}"
        created_at = int(time.time() * 1000)
        cursor.execute(
            """
            INSERT INTO messages (id, session_id, role, content, thinking_process, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, session_id, "assistant", content, thinking_process, created_at)
        )
        # Update session's updated_at
        cursor.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (created_at, session_id)
        )
        conn.commit()
        conn.close()


class AgentRunner:
    """Runner for executing the agent workflow.

    Provides methods to run the agent with various configurations.
    """

    def __init__(self):
        """Initialize agent runner."""
        self.graph = compile_workflow()

    def run(self, user_input: str) -> Dict[str, Any]:
        """Run agent synchronously.

        Args:
            user_input: User input

        Returns:
            Result dictionary.
        """
        initial_state = create_initial_state(user_input)
        return self.graph.invoke(initial_state)

    async def run_async(self, user_input: str) -> Dict[str, Any]:
        """Run agent asynchronously.

        Args:
            user_input: User input

        Returns:
            Result dictionary.
        """
        initial_state = create_initial_state(user_input)
        return await self.graph.ainvoke(initial_state)

    def stream(self, user_input: str) -> Any:
        """Stream agent execution.

        Args:
            user_input: User input

        Returns:
            Stream of state updates.
        """
        initial_state = create_initial_state(user_input)
        return self.graph.stream(initial_state)


# ========================================
# Helper functions for testing and debugging
# ========================================

def get_workflow_graph_visualization() -> str:
    """Get ASCII visualization of the workflow.

    Returns:
        ASCII diagram of the workflow.
    """
    return """
Workflow Graph:

    Start → Intent
           ↓
    ┌──────┼──────────────────┐
    │      │                  │
    │      │                  │
 NORMAL  RAG             TOOL/
  CHAT  DOMINANT        REASONING
    │      │                  │
    ↓      ↓                  ↓
 Direct  RagQuery         Planner
 Answer      ↓               ↓
    │   AnswerFromRag   InputPrepare
    │      ↓               ↓
    │   Finalize         Think
    │                     ↓
    │                SkillSelect
    │                     ↓
    │                 SkillExec
    │                     ↓
    │                   Observe
    │                     ↓
    │                 StateRouter
    │         ┌───────────┼───────────┐
    │         │           │           │
    │    SUCCESS      NEEDS_      RETRYABLE
    │    COMPLETE    KNOWLEDGE     (ok)
    │         │           │           │
    │         ↓           ↓           ↓
    │     Finalize    ProactiveRAG   Retry
    │                     ↓           ↓
    │                InjectKnowledge UpdateRetry
    │                     ↓           ↓
    │                 InputPrepare InputPrepare
    │                     
    │    SUCCESS      RETRYABLE    NEEDS_
    │    CONTINUE    EXCEEDED     USER_INPUT
    │         │           │           │
    │         ↓           ↓           ↓
    │    UpdateState  Finalize    UserConfirm
    │         ↓                     ↓
    │    InputPrepare         WaitUserResp
    │                             ↓
    │                        InputPrepare
    │
    │    FATAL_      NEEDS_
    │    ERROR       REPLAN
    │         │           │
    │         ↓           ↓
    │     Finalize      RePlan
    │                     ↓
    │                  Planner
    ↓
 Finalize → END
"""