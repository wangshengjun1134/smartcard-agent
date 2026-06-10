"""Message types for the agent conversation.

This module defines the Message dataclass and helper functions for building
different types of messages (user, assistant, tool result).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Message:
    """A message in the agent conversation.

    Attributes:
        role: Message role (user, assistant, tool, system).
        content: Text content of the message.
        tool_calls: Tool calls from assistant (if any).
        tool_call_id: Tool call ID (for tool result messages).
    """
    role: str
    content: str = ""
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


def build_user_message(content: str) -> Message:
    """Build a user message."""
    return Message(role="user", content=content)


def build_assistant_message(content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> Message:
    """Build an assistant message."""
    return Message(role="assistant", content=content, tool_calls=tool_calls)


def build_tool_result_message(tool_results: List[Dict[str, Any]]) -> Message:
    """Build a tool result message.

    Note: OpenAI API requires each tool call to have a separate tool message.
    However, our Message dataclass only supports single tool_call_id.
    The agent_core.py will convert this to multiple tool messages when needed.

    Args:
        tool_results: List of tool result dicts with keys:
            - tool_call_id: The ID of the tool call
            - name: Tool name
            - content: Result content
            - status: "success" or "error"

    Returns:
        Message with combined tool results (single tool_call_id for dataclass).
    """
    # Combine all tool results into content
    combined_content = "\n\n".join([
        f"[Tool: {tr['name']}]\n{tr['content']}"
        for tr in tool_results
    ])

    return Message(
        role="tool",
        content=combined_content,
        tool_call_id=tool_results[0]["tool_call_id"] if tool_results else None,
    )


def build_tool_result_messages(tool_results: List[Dict[str, Any]]) -> List[Message]:
    """Build multiple tool result messages (OpenAI format compliant).

    Each tool call must have its own tool message with matching tool_call_id.

    Args:
        tool_results: List of tool result dicts with keys:
            - tool_call_id: The ID of the tool call
            - name: Tool name
            - content: Result content
            - status: "success" or "error"

    Returns:
        List of Message objects, one per tool result.
    """
    messages = []
    for tr in tool_results:
        messages.append(Message(
            role="tool",
            content=tr["content"],
            tool_call_id=tr["tool_call_id"],
        ))
    return messages


def build_system_message(content: str) -> Message:
    """Build a system message."""
    return Message(role="system", content=content)
