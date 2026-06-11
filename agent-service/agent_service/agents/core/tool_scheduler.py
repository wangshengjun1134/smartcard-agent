"""Tool Scheduler for the agent core.

This module implements the tool scheduling and execution system, similar to
qwen-code's CoreToolScheduler.

Tools are registered with a name, description, parameters schema, and execution function.
The scheduler validates tool calls, executes tools, and returns results.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass

from agent_service.agents.core.events import emit_event

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """A tool call request from the model."""
    id: str
    name: str
    args: Dict[str, Any]


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None

    def to_content(self) -> str:
        """Convert result to string content for the model."""
        if self.success:
            if isinstance(self.data, str):
                return self.data
            elif isinstance(self.data, (dict, list)):
                import json
                return json.dumps(self.data, ensure_ascii=False, indent=2)
            else:
                return str(self.data)
        else:
            return f"Error: {self.error}"


@dataclass
class ToolDefinition:
    """Definition of a tool for the model."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable[..., Awaitable[ToolResult]]


class ToolScheduler:
    """Tool scheduler for managing and executing tool calls.

    Handles:
    - Tool registration
    - Tool call validation
    - Tool execution
    - Result collection
    """

    def __init__(self, event_queue: Optional[asyncio.Queue] = None):
        self._tools: Dict[str, ToolDefinition] = {}
        self._event_queue = event_queue

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool.

        Args:
            tool: Tool definition
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if unregistered, False if not found.
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name

        Returns:
            True if registered.
        """
        return name in self._tools

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition.

        Args:
            name: Tool name

        Returns:
            Tool definition or None.
        """
        return self._tools.get(name)

    def list_tool_names(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """Get all tool declarations in OpenAI function calling format.

        Returns:
            List of tool declarations for the model.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """Execute a tool.

        Args:
            name: Tool name
            args: Tool arguments

        Returns:
            Tool execution result.
        """
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found. Available: {self.list_tool_names()}",
            )

        try:
            logger.info(f"[ToolScheduler] Executing {name} with args: {args}")
            result = await tool.handler(**args)
            return result
        except TypeError as e:
            # Likely a parameter error
            return ToolResult(
                success=False,
                error=f"Invalid parameters for tool '{name}': {e}",
            )
        except Exception as e:
            logger.error(f"[ToolScheduler] Tool {name} failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Tool '{name}' execution failed: {e}",
            )
