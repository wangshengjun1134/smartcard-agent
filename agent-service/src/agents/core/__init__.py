"""Agent Core module.

This module provides the core reasoning loop and tool scheduling system
for the smartcard agent, based on qwen-code's AgentCore design.
"""

from agents.core.agent_core import AgentCore, AgentCoreConfig, ReasoningLoopResult
from agents.core.tool_scheduler import ToolScheduler, ToolCall, ToolResult, ToolDefinition
from agents.core.message import Message, build_user_message, build_assistant_message, build_tool_result_message
from agents.core.events import (
    emit_event,
    emit_thinking,
    emit_thinking_chunk,
    emit_content,
    emit_tool_call,
    emit_tool_result,
)

__all__ = [
    "AgentCore",
    "AgentCoreConfig",
    "ReasoningLoopResult",
    "ToolScheduler",
    "ToolCall",
    "ToolResult",
    "ToolDefinition",
    "Message",
    "build_user_message",
    "build_assistant_message",
    "build_tool_result_message",
    "emit_event",
    "emit_thinking",
    "emit_thinking_chunk",
    "emit_content",
    "emit_tool_call",
    "emit_tool_result",
]
