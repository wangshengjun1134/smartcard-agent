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
import time
from typing import Dict, Any, Optional

from agents.core.tool_scheduler import ToolScheduler, ToolDefinition, ToolResult
from agents.core.events import emit_content

# Shared runtime context (set at startup, accessed by skill handlers)
_runtime_context = None

logger = logging.getLogger(__name__)


def set_runtime_context(ctx) -> None:
    """Set the shared runtime context for skill execution.

    Args:
        ctx: RuntimeContext instance with PCSC client attached.
    """
    global _runtime_context
    _runtime_context = ctx


def get_runtime_context():
    """Get the shared runtime context.

    Returns:
        RuntimeContext instance or None if not set.
    """
    return _runtime_context


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

    Returns the shared RuntimeContext which holds:
    - PCSC client for hardware communication
    - Current connection/file/security state
    - Execution history

    Args:
        skill: Skill instance

    Returns:
        RuntimeContext instance (or MockContext if not initialized).
    """
    global _runtime_context
    if _runtime_context is not None:
        return _runtime_context

    # Fallback: MockContext for testing without full setup
    class MockContext:
        def __init__(self):
            self.connected = False
            self.card_type = None
            self.card_capabilities = []
            self.secure_channel_state = type('State', (), {'value': 'none'})()
            self.pcsc_client = None

        def is_pin_verified(self, pin_ref: int) -> bool:
            return False

        def send_apdu(self, apdu, check_sw=True):
            raise RuntimeError("No PCSC client attached — use set_runtime_context() first")

    return MockContext()


def _register_utility_tools(scheduler: ToolScheduler) -> None:
    """Register utility tools."""

    # send_apdu tool — for raw APDU execution (supports single or multiple APDUs)
    scheduler.register(ToolDefinition(
        name="send_apdu",
        description="Send APDU commands to the smart card. Supports single APDU ('apdu' string) or multiple APDUs ('apdus' array). IMPORTANT: Use 'apdus' array ONLY when subsequent APDUs do NOT depend on previous results. For example, SELECT MF → SELECT EF_IMSI → READ BINARY can be sent together because all APDUs are predetermined. But if you need to parse response data before constructing the next APDU, use single 'apdu' calls. Example: {\"apdus\": [\"00A4000C023F00\", \"00A4000C026F07\", \"00B0000009\"]}",
        parameters={
            "type": "object",
            "properties": {
                "apdu": {
                    "type": "string",
                    "description": "Single APDU command as hex string. Use this when next APDU depends on this result.",
                },
                "apdus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of predetermined APDUs to execute sequentially. Use ONLY when all APDUs can be determined upfront without needing previous results.",
                },
            },
            "required": [],
        },
        handler=_send_apdu_handler,
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


async def _send_apdu_handler(**kwargs) -> ToolResult:
    """Send APDU handler - supports single APDU or multiple APDUs."""
    logger.info(f"[Tool:send_apdu] Received kwargs: {kwargs}")

    ctx = get_runtime_context()
    if not ctx:
        return ToolResult(
            success=False,
            error="Runtime context not initialized. This is a system setup issue — please restart the service.",
        )
    if not ctx.connected:
        return ToolResult(
            success=False,
            error="⚠ 未连接到卡片。请先在前端选择读卡器并连接卡片，然后再发送 APDU 命令。这是用户需要操作的问题，AI 无法自动解决连接状态。",
        )

    # Get APDU(s) - support both single string and array
    apdus = []
    if "apdus" in kwargs and isinstance(kwargs["apdus"], list):
        apdus = [a.strip() for a in kwargs["apdus"] if a and a.strip()]
    elif "apdu" in kwargs and kwargs["apdu"]:
        apdus = [kwargs["apdu"].strip()]

    if not apdus:
        return ToolResult(success=False, error="APDU command(s) missing. Provide 'apdu' (string) or 'apdus' (array).")

    logger.info(f"[Tool:send_apdu] Executing {len(apdus)} APDU(s)")

    # Execute all APDUs sequentially
    results = []
    total_start_time = time.time()
    all_success = True

    for i, apdu_hex in enumerate(apdus):
        try:
            start_time = time.time()
            # check_sw=False allows LLM to see the status word even on error
            resp = ctx.send_apdu(apdu_hex, check_sw=False)
            duration_ms = int((time.time() - start_time) * 1000)

            result_entry = {
                "index": i + 1,
                "capdu": apdu_hex,
                "rapdu": resp.data.hex().upper() if resp.data else "",
                "sw": resp.sw,
                "duration_ms": duration_ms,
            }

            # Mark as error if SW is not 9000 (but continue execution)
            if resp.sw != "9000":
                result_entry["error"] = f"Status word: {resp.sw}"
                all_success = False

            results.append(result_entry)
            logger.info(f"[Tool:send_apdu] APDU {i+1}: {apdu_hex} -> SW={resp.sw}")

        except Exception as e:
            results.append({
                "index": i + 1,
                "capdu": apdu_hex,
                "error": str(e),
                "sw": "N/A",
            })
            all_success = False
            logger.error(f"[Tool:send_apdu] APDU {i+1} failed: {e}")

    total_duration_ms = int((time.time() - total_start_time) * 1000)

    # Format result for agent
    if len(results) == 1:
        # Single APDU - return simple format
        r = results[0]
        return ToolResult(
            success=all_success,
            data={
                "capdu": r["capdu"],
                "rapdu": r.get("rapdu", ""),
                "sw": r["sw"],
                "duration_ms": r.get("duration_ms", 0),
                "results": results,
                "total_duration_ms": total_duration_ms,
            },
            error=r.get("error") if not all_success else None,
        )
    else:
        # Multiple APDUs - return array format with summary
        summary = "\n".join([
            f"[{r['index']}] CAPDU: {r['capdu']} → RAPDU: {r.get('rapdu', 'N/A')}, SW: {r['sw']}"
            for r in results
        ])

        return ToolResult(
            success=all_success,
            data={
                "results": results,
                "summary": summary,
                "total_apdus": len(results),
                "total_duration_ms": total_duration_ms,
            },
            error=None if all_success else "Some APDUs failed (see results for details)",
        )


async def _ask_user_handler(**kwargs) -> ToolResult:
    """Ask user tool handler.

    Rejects empty questions to prevent infinite loops.
    """
    question = kwargs.get("question", "").strip()
    if not question:
        return ToolResult(
            success=False,
            error="Empty question — agent should proceed with available tools instead of asking.",
        )
    return ToolResult(
        success=True,
        data=f"[User interaction needed] Question: {question}",
    )
