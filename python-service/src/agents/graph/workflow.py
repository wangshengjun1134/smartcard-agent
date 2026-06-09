"""Simplified Workflow using AgentCore reasoning loop.

This module replaces the LangGraph-based workflow with a qwen-code style
reasoning loop: send messages → stream response → collect tool calls → execute tools → repeat.

The workflow is simpler but more flexible — the model decides what tools to call
and in what order, rather than following a predefined graph.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, AsyncGenerator

from agents.core.agent_core import AgentCore, AgentCoreConfig, ReasoningLoopResult
from agents.core.message import build_user_message, build_assistant_message, build_system_message
from agents.core.tool_scheduler import ToolScheduler
from agents.tools.builtin import register_builtin_tools
from agents.core.events import emit_thinking, emit_content

logger = logging.getLogger(__name__)

# System prompt for the smartcard agent
SYSTEM_PROMPT = """你是智能卡操作助手，可以帮助用户完成以下任务：

1. 读取卡片信息（IMSI、ICCID、号码等）
2. 执行APDU命令
3. 探测卡片能力和应用
4. 回答智能卡相关技术问题

请使用提供的工具来完成用户的请求：
- 对于标准操作（如读取 ICCID），优先使用封装好的 skill 工具（如 `read_iccid`）。
- 对于自定义指令或用户直接输入的十六进制代码，请使用 `send_apdu` 工具。
- 当所有操作完成或无法继续时，直接返回最终文本即可。

注意事项：
- 在执行危险操作前，请提醒用户确认
- 如果操作失败，请尝试分析错误原因并提供建议
- 保持回答简洁明了"""


def create_agent_core(event_queue: asyncio.Queue) -> AgentCore:
    """Create an AgentCore instance with registered tools.

    Args:
        event_queue: asyncio.Queue for real-time event streaming

    Returns:
        Configured AgentCore instance.
    """
    config = AgentCoreConfig(
        max_turns=15,
        max_time_minutes=10.0,
        model_temperature=0.7,
        system_prompt=SYSTEM_PROMPT,
        event_queue=event_queue,
    )

    agent = AgentCore(config)

    # Register built-in tools (including skill wrappers)
    register_builtin_tools(agent.scheduler)

    return agent


async def run_agent_core(
    user_input: str,
    event_queue: asyncio.Queue,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the agent with the reasoning loop.

    Args:
        user_input: User request text
        event_queue: asyncio.Queue for real-time event streaming
        session_id: Optional session ID for saving response

    Returns:
        Final result dictionary.
    """
    logger.info(f"[AgentCore] Starting with input: {user_input}")

    # Create agent with tools
    agent = create_agent_core(event_queue)

    # Load conversation history if session_id is provided
    history_messages = []
    if session_id:
        try:
            from api.session import get_session_messages
            history = get_session_messages(session_id)
            # Take last N messages (exclude system messages, limit to avoid token overflow)
            MAX_HISTORY_MESSAGES = 10
            recent_history = history[-MAX_HISTORY_MESSAGES:] if len(history) > MAX_HISTORY_MESSAGES else history
            for msg in recent_history:
                if msg.role == "user":
                    history_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    # Assistant message: use content (final answer), not thinking
                    history_messages.append({"role": "assistant", "content": msg.content})
            logger.info(f"[AgentCore] Loaded {len(history_messages)} history messages from session {session_id}")
        except Exception as e:
            logger.warning(f"[AgentCore] Failed to load history: {e}")

    # Build card status context
    card_context = ""
    try:
        from agents.tools.builtin import get_runtime_context
        ctx = get_runtime_context()
        if ctx and ctx.connected:
            card_context = f"\n\n当前状态：已连接到读卡器 '{ctx.current_reader}'，ATR: {ctx.atr.hex().upper() if ctx.atr else 'N/A'}"
    except Exception:
        pass

    # Build initial messages: system + history + current user input
    messages = [
        build_system_message(SYSTEM_PROMPT + card_context),
    ]
    # Add conversation history (user/assistant exchanges)
    for hist_msg in history_messages:
        if hist_msg["role"] == "user":
            messages.append(build_user_message(hist_msg["content"]))
        elif hist_msg["role"] == "assistant":
            messages.append(build_assistant_message(hist_msg["content"]))
    # Add current user input
    messages.append(build_user_message(user_input))

    # Get tool declarations
    tools = agent.scheduler.get_tool_declarations()

    # Run reasoning loop
    result = await agent.run_reasoning_loop(
        initial_messages=messages,
        tools=tools,
    )

    logger.info(f"[AgentCore] Completed: turns={result.turns_used}, mode={result.terminate_mode}")

    # Build final response
    final_response = result.text if result.text else "处理完成"

    return {
        "final_response": final_response,
        "execution_intent": "TOOL_REASONING",  # Always tool reasoning in this mode
        "current_goal": "",
        "observations": [],
        "finished": result.terminate_mode is None,  # None = normal completion
        "error": None,
        "turns_used": result.turns_used,
        "terminate_mode": result.terminate_mode,
    }


async def stream_agent_core(
    user_input: str,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream agent execution with SSE format.

    Uses asyncio.Queue to receive real-time events from the reasoning loop,
    providing live thinking/tool/routing updates to the frontend.

    Args:
        user_input: User request text
        session_id: Session ID for saving assistant response

    Yields:
        SSE formatted strings with real-time events.
    """
    logger.info(f"[AgentCore] stream_agent_core called with input: {user_input}")

    # Create event queue for real-time streaming
    event_queue = asyncio.Queue()

    accumulated_response = ""
    thinking_steps = []
    graph_done = False
    final_result = None

    # Start agent execution in background
    async def run_agent():
        """Run the agent and signal completion."""
        nonlocal graph_done, final_result
        try:
            final_result = await run_agent_core(user_input, event_queue, session_id)
        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            await event_queue.put({
                "type": "error",
                "error": str(e),
            })
        finally:
            graph_done = True
            # Signal end of stream
            await event_queue.put({"type": "stream_end"})

    agent_task = asyncio.create_task(run_agent())

    # Main loop: poll queue and yield SSE events
    while True:
        # Check if agent is done and queue is empty
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
        elif event.get("type") == "thinking":
            thinking_steps.append(event.get("data", ""))
        elif event.get("type") == "thinking_chunk":
            chunk = event.get("data", "")
            if thinking_steps:
                thinking_steps[-1] += chunk
            else:
                thinking_steps.append(chunk)

    # Wait for agent task to complete
    await agent_task

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
        thinking_data = {
            "steps": thinking_steps,
        }
        thinking_json = json.dumps(thinking_data, ensure_ascii=False)
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

    elif event_type == "tool_call":
        action_data = {
            'type': 'action',
            'action': event.get('action', ''),
            'status': event.get('status', ''),
            'details': event.get('details', {}),
        }
        return f"data: {json.dumps(action_data)}\n\n"

    elif event_type == "tool_result":
        obs_data = {
            'type': 'observation',
            'skill': event.get('skill', ''),
            'success': event.get('success', False),
            'result': event.get('result'),
            'error': event.get('error'),
        }
        return f"data: {json.dumps(obs_data)}\n\n"

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


def _update_assistant_message(
    session_id: str,
    content: str,
    thinking_process: Optional[str] = None,
    thinking_content: Optional[str] = None,
):
    """Update the last assistant message in database.

    Args:
        session_id: Session ID
        content: Message content to update
        thinking_process: Optional thinking/reasoning process JSON string
        thinking_content: Optional raw thinking text
    """
    try:
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
    except Exception as e:
        logger.error(f"Failed to save assistant message: {e}", exc_info=True)


# Keep backward compatibility with old workflow API
def create_workflow():
    """Create workflow (backward compatibility — returns None, not used)."""
    return None


def compile_workflow():
    """Compile workflow (backward compatibility — returns None, not used)."""
    return None


def get_graph():
    """Get compiled graph (backward compatibility — returns None, not used)."""
    return None


def run_agent(user_input: str) -> Dict[str, Any]:
    """Run agent synchronously (backward compatibility).

    Note: This is a thin wrapper around the new agent core.
    Prefer using run_agent_async or stream_agent_core for new code.
    """
    event_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_agent_core(user_input, event_queue))


async def run_agent_async(user_input: str) -> Dict[str, Any]:
    """Run agent asynchronously (backward compatibility).

    Note: This is a thin wrapper around the new agent core.
    """
    event_queue = asyncio.Queue()
    return await run_agent_core(user_input, event_queue)


# The old stream_agent function is replaced with stream_agent_core
# Keep the same name for API compatibility
stream_agent = stream_agent_core
