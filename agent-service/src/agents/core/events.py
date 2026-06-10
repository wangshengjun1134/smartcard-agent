"""Event emission utilities for the agent core.

This module provides functions for emitting real-time events to the SSE stream
during agent execution.
"""

import asyncio
import time
import json
from typing import Any, Dict, Optional


async def emit_event(event_queue: asyncio.Queue, event: Dict[str, Any]) -> None:
    """Push a real-time event to the SSE stream.

    Args:
        event_queue: asyncio.Queue for real-time event streaming
        event: Event dictionary with type and data
    """
    if event_queue is None:
        return

    event["timestamp"] = time.time()
    await event_queue.put(event)


async def emit_thinking(event_queue: asyncio.Queue, content: str) -> None:
    """Emit a thinking/reasoning step.

    Args:
        event_queue: asyncio.Queue for real-time event streaming
        content: Thinking content text
    """
    await emit_event(event_queue, {
        "type": "thinking",
        "data": content,
    })


async def emit_thinking_chunk(event_queue: asyncio.Queue, chunk: str) -> None:
    """Emit an LLM streaming chunk.

    Args:
        event_queue: asyncio.Queue for real-time event streaming
        chunk: LLM output chunk
    """
    await emit_event(event_queue, {
        "type": "thinking_chunk",
        "data": chunk,
    })


async def emit_content(event_queue: asyncio.Queue, chunk: str) -> None:
    """Emit a content chunk for streaming response.

    Args:
        event_queue: asyncio.Queue for real-time event streaming
        chunk: Content text chunk
    """
    await emit_event(event_queue, {
        "type": "content",
        "data": chunk,
    })


async def emit_tool_call(
    event_queue: asyncio.Queue,
    name: str,
    args: Dict[str, Any],
) -> None:
    """Emit a tool call event.

    Args:
        event_queue: asyncio.Queue for real-time event streaming
        name: Tool name
        args: Tool arguments
    """
    await emit_event(event_queue, {
        "type": "tool_call",
        "action": name,
        "status": "started",
        "details": args,
    })


async def emit_tool_result(
    event_queue: asyncio.Queue,
    name: str,
    success: bool,
    result: Any = None,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """Emit a tool result event.

    Args:
        event_queue: asyncio.Queue for real-time event streaming
        name: Tool name
        success: Whether execution succeeded
        result: Execution result
        error: Error message if failed
        duration_ms: Execution duration in milliseconds
    """
    event = {
        "type": "tool_result",
        "skill": name,
        "success": success,
    }
    if result is not None:
        event["result"] = result
    if error:
        event["error"] = error
    if duration_ms is not None:
        event["duration_ms"] = duration_ms

    await emit_event(event_queue, event)
