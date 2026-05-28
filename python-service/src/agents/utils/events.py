"""Real-time event streaming utilities for LangGraph nodes.

This module provides helper functions for nodes to push real-time
events to the SSE stream during execution.

Event types:
    - thinking: Thinking/reasoning process text
    - thinking_chunk: LLM streaming output chunk
    - routing: Routing decision with target node
    - action: Action/skill execution status
    - observation: Execution observation result
    - node_start: Node execution started
    - node_end: Node execution completed
"""

import asyncio
import time
from typing import Any, Dict, Tuple, Union


async def write_event(state: Dict[str, Any], event: Union[Tuple[str, Any], Dict[str, Any]]) -> None:
    """Push a real-time event to the SSE stream.

    Args:
        state: AgentState containing event_queue
        event: Either a tuple (event_type, data) or a dict with event details

    Usage:
        # Simple tuple format
        await write_event(state, ("thinking", "正在分析用户输入..."))

        # Dict format with more details
        await write_event(state, {
            "type": "routing",
            "from": "intent",
            "to": "planner",
            "reason": "用户请求需要执行卡片操作",
        })
    """
    queue = state.get("event_queue")
    if queue is None:
        return

    # Convert tuple to dict
    if isinstance(event, tuple):
        event_dict = {
            "type": event[0],
            "data": event[1],
            "timestamp": time.time(),
        }
    else:
        event_dict = {
            **event,
            "timestamp": time.time(),
        }

    await queue.put(event_dict)


def write_event_sync(state: Dict[str, Any], event: Union[Tuple[str, Any], Dict[str, Any]]) -> None:
    """Synchronous version of write_event for non-async contexts.

    Args:
        state: AgentState containing event_queue
        event: Either a tuple (event_type, data) or a dict with event details
    """
    queue = state.get("event_queue")
    if queue is None:
        return

    # Convert tuple to dict
    if isinstance(event, tuple):
        event_dict = {
            "type": event[0],
            "data": event[1],
            "timestamp": time.time(),
        }
    else:
        event_dict = {
            **event,
            "timestamp": time.time(),
        }

    # Use put_nowait for sync context
    queue.put_nowait(event_dict)


# ========================================
# Convenience functions for common events
# ========================================

async def emit_thinking(state: Dict[str, Any], content: str) -> None:
    """Emit a thinking/reasoning step.

    Args:
        state: AgentState
        content: Thinking content text
    """
    await write_event(state, ("thinking", content))


async def emit_thinking_chunk(state: Dict[str, Any], chunk: str) -> None:
    """Emit an LLM streaming chunk.

    Args:
        state: AgentState
        chunk: LLM output chunk
    """
    await write_event(state, ("thinking_chunk", chunk))


async def emit_routing(
    state: Dict[str, Any],
    from_node: str,
    to_node: str,
    reason: str = "",
    confidence: float = None,
) -> None:
    """Emit a routing decision.

    Args:
        state: AgentState
        from_node: Current node name
        to_node: Target node name
        reason: Routing reason
        confidence: Confidence score (0-1)
    """
    event = {
        "type": "routing",
        "from": from_node,
        "to": to_node,
        "reason": reason,
    }
    if confidence is not None:
        event["confidence"] = confidence

    await write_event(state, event)


async def emit_action(
    state: Dict[str, Any],
    action: str,
    status: str = "started",
    details: Dict[str, Any] = None,
) -> None:
    """Emit an action/skill execution event.

    Args:
        state: AgentState
        action: Action/skill name
        status: "started", "running", "completed", "failed"
        details: Additional details
    """
    event = {
        "type": "action",
        "action": action,
        "status": status,
    }
    if details:
        event["details"] = details

    await write_event(state, event)


async def emit_observation(
    state: Dict[str, Any],
    skill: str,
    success: bool,
    result: Any = None,
    error: str = None,
) -> None:
    """Emit an observation/result event.

    Args:
        state: AgentState
        skill: Skill name that was executed
        success: Whether execution succeeded
        result: Execution result
        error: Error message if failed
    """
    event = {
        "type": "observation",
        "skill": skill,
        "success": success,
    }
    if result is not None:
        event["result"] = result
    if error:
        event["error"] = error

    await write_event(state, event)


async def emit_node_event(
    state: Dict[str, Any],
    node: str,
    event_type: str = "node_start",
    details: Dict[str, Any] = None,
) -> None:
    """Emit a node lifecycle event.

    Args:
        state: AgentState
        node: Node name
        event_type: "node_start" or "node_end"
        details: Additional details
    """
    event = {
        "type": event_type,
        "node": node,
    }
    if details:
        event["details"] = details

    await write_event(state, event)