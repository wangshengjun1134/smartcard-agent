"""Built-in tools for the agent core.

This module registers all available tools that the agent can call,
including:
- Wrappers around existing skills
- Knowledge lookup (RAG)
- General utility tools

TODO: Memory system integration (save/load conversation context)
TODO: User confirmation flow for dangerous operations
TODO: RAG tool integration
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from agents.core.tool_scheduler import ToolScheduler, ToolDefinition, ToolResult
from agents.core.events import emit_content

logger = logging.getLogger(__name__)


def register_builtin_tools(scheduler: ToolScheduler) -> None:
    """Register all built-in tools with the scheduler.

    Args:
        scheduler: ToolScheduler instance to register tools with.
    """
    # Register skill-based tools
    _register_skill_tools(scheduler)

    # Register utility tools
    _register_utility_tools(scheduler)

    # TODO: Register RAG tool
    # _register_rag_tool(scheduler)

    # TODO: Register memory tool
    # _register_memory_tool(scheduler)


def _register_skill_tools(scheduler: ToolScheduler) -> None:
    """Register tools that wrap existing skills."""
    from skills.base.registry import get_registry
    from skills.registry_extension import register_all_skills

    # Auto-register all skills first
    register_all_skills()

    registry = get_registry()

    for skill_name in registry.list_skills():
        skill = registry.get_skill(skill_name)
        if skill is None:
            continue

        # Build tool definition from skill metadata
        tool_def = ToolDefinition(
            name=skill.name,
            description=skill.description,
            parameters={
                "type": "object",
                "properties": _infer_skill_params(skill),
                "required": [],
            },
            handler=_make_skill_handler(skill),
        )
        scheduler.register(tool_def)
        logger.info(f"[ToolRegistry] Registered skill tool: {skill_name}")


def _infer_skill_params(skill) -> Dict[str, Any]:
    """Infer skill parameters from the skill's run method signature.

    This is a simplified approach — in production, skills should declare
    their parameters explicitly.

    Args:
        skill: Skill instance

    Returns:
        JSON Schema for skill parameters.
    """
    # Default: accept any parameters as a flexible dict
    # TODO: Parse skill.run signature or use explicit parameter declarations
    return {
        "params": {
            "type": "object",
            "description": f"Parameters for {skill.name} skill",
        },
    }


def _make_skill_handler(skill) -> callable:
    """Create an async handler for a skill.

    Args:
        skill: Skill instance

    Returns:
        Async function that executes the skill.
    """
    async def handler(params: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        try:
            # Build execution context
            ctx = _build_skill_context(skill)

            # Merge params
            skill_params = params or {}
            if kwargs:
                skill_params.update(kwargs)

            # Execute skill
            result = await skill.run(ctx, skill_params)

            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
            )
        except Exception as e:
            logger.error(f"[Skill:{skill.name}] Execution failed: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))

    return handler


def _build_skill_context(skill) -> Any:
    """Build a skill execution context.

    TODO: Implement proper context with:
    - PCSC client
    - Runtime state
    - Skill registry for nested calls

    Args:
        skill: Skill instance

    Returns:
        Execution context (placeholder for now).
    """
    # Placeholder — need to wire up actual PCSC client and runtime context
    class MockContext:
        def __init__(self):
            self.connected = False
            self.card_type = None
            self.card_capabilities = []
            self.secure_channel_state = type('State', (), {'value': 'none'})()

        def is_pin_verified(self, pin_ref: int) -> bool:
            return False

    return MockContext()


def _register_utility_tools(scheduler: ToolScheduler) -> None:
    """Register utility tools."""

    # finalize tool — let the model indicate it's done
    scheduler.register(ToolDefinition(
        name="finalize",
        description="Call this tool when you have completed the task and want to provide a final response to the user.",
        parameters={
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The final response to show to the user.",
                },
            },
            "required": ["response"],
        },
        handler=_finalize_handler,
    ))

    # ask_user tool — for when the agent needs clarification
    scheduler.register(ToolDefinition(
        name="ask_user",
        description="Ask the user a clarifying question when you need more information to proceed.",
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user.",
                },
            },
            "required": ["question"],
        },
        handler=_ask_user_handler,
    ))


async def _finalize_handler(response: str) -> ToolResult:
    """Finalize tool handler — signals completion.

    In the reasoning loop, this tool's result will be treated as the final answer.
    """
    return ToolResult(success=True, data=response)


async def _ask_user_handler(question: str) -> ToolResult:
    """Ask user tool handler.

    TODO: Implement proper user interaction flow.
    For now, return a placeholder.
    """
    return ToolResult(
        success=True,
        data=f"[User interaction needed] Question: {question}\nNote: User confirmation flow not yet implemented.",
    )
