"""AgentCore — The core reasoning loop for the smartcard agent.

This module implements the qwen-code style reasoning loop:
    send messages → stream response → collect tool calls → execute tools → repeat

The loop terminates when:
- The model produces a text response without tool calls (normal completion)
- max_turns is reached
- max_time_minutes is exceeded
- The cancel signal fires
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field

from llm.llm import get_llm, LLMConfigError
from agents.core.tool_scheduler import ToolScheduler, ToolCall, ToolResult
from agents.core.message import Message, build_user_message, build_assistant_message, build_tool_result_message
from agents.core.events import emit_thinking, emit_thinking_chunk, emit_content, emit_tool_call, emit_tool_result

logger = logging.getLogger(__name__)


@dataclass
class ReasoningLoopResult:
    """Result of a reasoning loop invocation."""
    text: str = ""
    terminate_mode: Optional[str] = None  # None = normal completion
    turns_used: int = 0


@dataclass
class AgentCoreConfig:
    """Configuration for AgentCore."""
    max_turns: int = 15
    max_time_minutes: float = 10.0
    model_temperature: float = 0.7
    system_prompt: Optional[str] = None
    event_queue: Optional[asyncio.Queue] = None
    on_tool_call: Optional[Callable[[ToolCall], Awaitable[None]]] = None


class AgentCore:
    """Core execution engine for model reasoning and tool scheduling.

    This class encapsulates:
    - The inner reasoning loop (run_reasoning_loop)
    - Tool call scheduling and execution (via ToolScheduler)
    - Event emission for real-time streaming
    """

    def __init__(self, config: AgentCoreConfig):
        self.config = config
        self.scheduler = ToolScheduler(event_queue=config.event_queue)
        self._event_queue = config.event_queue

    async def run_reasoning_loop(
        self,
        initial_messages: List[Message],
        tools: List[Dict[str, Any]],
        cancel_signal: Optional[asyncio.Event] = None,
    ) -> ReasoningLoopResult:
        """Run the inner model reasoning loop.

        This is the core execution cycle:
        send messages → stream response → collect tool calls → execute tools → repeat.

        Args:
            initial_messages: The first messages to send (e.g., user task prompt).
            tools: Available tool declarations (OpenAI function calling format).
            cancel_signal: Optional event to signal cancellation.

        Returns:
            ReasoningLoopResult with final text, terminate mode, and turns used.
        """
        start_time = time.time()
        messages = list(initial_messages)
        turn_counter = 0
        final_text = ""
        terminate_mode = None

        while True:
            # Check cancel signal
            if cancel_signal and cancel_signal.is_set():
                terminate_mode = "CANCELLED"
                break

            # Check termination conditions
            if turn_counter >= self.config.max_turns:
                terminate_mode = "MAX_TURNS"
                break

            elapsed_minutes = (time.time() - start_time) / 60.0
            if elapsed_minutes >= self.config.max_time_minutes:
                terminate_mode = "TIMEOUT"
                break

            turn_counter += 1
            logger.info(f"[AgentCore] Starting turn {turn_counter}")
            await emit_thinking(self._event_queue, f"🔄 第 {turn_counter} 轮推理...")

            try:
                # Call LLM with streaming
                llm = get_llm(temperature=self.config.model_temperature)

                # Build messages for LLM
                llm_messages = self._convert_messages_to_llm_format(messages)

                # Add system prompt if configured
                if self.config.system_prompt:
                    llm_messages = [
                        {"role": "system", "content": self.config.system_prompt}
                    ] + llm_messages

                # Call LLM with tool support
                response_text = ""
                tool_calls = []

                # Use LangChain's streaming with tool support
                llm_with_tools = llm.bind_tools(self._convert_tools_for_langchain(tools))

                accumulated_content = ""
                async for chunk in llm_with_tools.astream(llm_messages):
                    # Handle streaming chunks
                    chunk_content = chunk.content if hasattr(chunk, 'content') and chunk.content else ""
                    if chunk_content:
                        accumulated_content += chunk_content
                        await emit_thinking_chunk(self._event_queue, chunk_content)

                    # Collect tool calls from chunk (if any)
                    if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                        for tc in chunk.tool_calls:
                            tool_calls.append(tc)

                # If no tool calls from streaming, check the final response
                if not tool_calls and accumulated_content:
                    response_text = accumulated_content

                # If we have tool calls, process them
                if tool_calls:
                    logger.info(f"[AgentCore] Turn {turn_counter}: {len(tool_calls)} tool call(s)")

                    # Execute tools
                    tool_result_messages = await self._process_tool_calls(
                        tool_calls, tools, cancel_signal
                    )
                    messages.extend(tool_result_messages)

                    # Continue the loop
                    continue
                else:
                    # No tool calls — treat this as the model's final answer
                    if response_text and response_text.strip():
                        final_text = response_text.strip()
                        await emit_content(self._event_queue, final_text)
                        logger.info(f"[AgentCore] Turn {turn_counter}: Normal completion")
                        break
                    else:
                        # Nudge the model to finalize
                        messages.append(build_user_message(
                            "Please provide the final result now and stop calling tools."
                        ))
                        continue

            except LLMConfigError as e:
                logger.error(f"[AgentCore] LLM not configured: {e}")
                await emit_thinking(self._event_queue, f"⚠ LLM 未配置: {e}")
                final_text = "请先在设置中配置 API Key，然后再开始对话。"
                terminate_mode = "LLM_NOT_CONFIGURED"
                break

            except Exception as e:
                logger.error(f"[AgentCore] Error in turn {turn_counter}: {e}", exc_info=True)
                await emit_thinking(self._event_queue, f"⚠ 错误: {e}")
                # Don't fail immediately — try to continue
                messages.append(build_user_message(
                    f"An error occurred: {e}. Please try to continue or provide a final response."
                ))
                continue

        return ReasoningLoopResult(
            text=final_text,
            terminate_mode=terminate_mode,
            turns_used=turn_counter,
        )

    async def _process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        cancel_signal: Optional[asyncio.Event] = None,
    ) -> List[Message]:
        """Process a list of tool calls.

        Validates each call, executes tools, collects results, and emits events.

        Args:
            tool_calls: Tool calls from the model (LangChain format).
            tools: Available tool declarations.
            cancel_signal: Optional cancel signal.

        Returns:
            List of tool result messages to append to the conversation.
        """
        tool_result_parts = []

        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_id = tc.get("id", tool_name)

            logger.info(f"[AgentCore] Processing tool call: {tool_name}({tool_args})")

            # Emit tool call event
            await emit_tool_call(
                self._event_queue,
                name=tool_name,
                args=tool_args,
            )

            # Check if tool exists
            if not self.scheduler.has_tool(tool_name):
                error_msg = f'Tool "{tool_name}" not found. Available tools: {self.scheduler.list_tool_names()}'
                logger.warning(f"[AgentCore] {error_msg}")

                # Emit tool result event with error
                await emit_tool_result(
                    self._event_queue,
                    name=tool_name,
                    success=False,
                    error=error_msg,
                )

                tool_result_parts.append({
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": error_msg,
                    "status": "error",
                })
                continue

            # Execute the tool
            start_time = time.time()
            try:
                result = await self.scheduler.execute(tool_name, tool_args)
                duration_ms = (time.time() - start_time) * 1000

                # Emit tool result event
                await emit_tool_result(
                    self._event_queue,
                    name=tool_name,
                    success=result.success,
                    result=result.data if result.success else None,
                    error=result.error if not result.success else None,
                    duration_ms=duration_ms,
                )

                tool_result_parts.append({
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": result.to_content(),
                    "status": "success" if result.success else "error",
                })

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = f"Tool execution error: {e}"
                logger.error(f"[AgentCore] {error_msg}", exc_info=True)

                await emit_tool_result(
                    self._event_queue,
                    name=tool_name,
                    success=False,
                    error=error_msg,
                    duration_ms=duration_ms,
                )

                tool_result_parts.append({
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": error_msg,
                    "status": "error",
                })

        # Build tool result message
        return [build_tool_result_message(tool_result_parts)]

    def _convert_messages_to_llm_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Message objects to LLM format."""
        result = []
        for msg in messages:
            if msg.role == "user":
                result.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                assistant_msg = {"role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    assistant_msg["tool_calls"] = msg.tool_calls
                result.append(assistant_msg)
            elif msg.role == "tool":
                result.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content,
                })
        return result

    def _convert_tools_for_langchain(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tool declarations to LangChain tool format.

        Tools are already in OpenAI function calling format, so just pass through.
        """
        return tools
