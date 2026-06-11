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
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from openai import AsyncOpenAI

from agent_service.llm.llm import get_openai_client, LLMConfig, LLMConfigError
from agent_service.agents.core.tool_scheduler import ToolScheduler, ToolCall, ToolResult
from agent_service.agents.core.message import Message, build_user_message, build_assistant_message, build_tool_result_messages
from agent_service.agents.core.events import emit_thinking, emit_thinking_chunk, emit_content, emit_tool_call, emit_tool_result

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
                # Get OpenAI client for streaming (direct access to reasoning_content)
                client = get_openai_client()
                config = LLMConfig.get_config()

                # Build messages for LLM
                llm_messages = self._convert_messages_to_llm_format(messages)

                # Add system prompt if configured
                if self.config.system_prompt:
                    llm_messages = [
                        {"role": "system", "content": self.config.system_prompt}
                    ] + llm_messages

                # Stream response with OpenAI SDK
                # Use streaming to capture reasoning_content for UI display,
                # with timeout protection - if stream takes too long, fallback to non-streaming
                response_text = ""
                has_tool_calls_in_stream = False
                tool_names_seen = set()
                stream_timeout_seconds = 60  # Timeout for streaming response

                try:
                    stream = await client.chat.completions.create(
                        model=config.openai_model,
                        messages=llm_messages,
                        tools=tools,
                        temperature=self.config.model_temperature,
                        stream=True,
                    )

                    async with asyncio.timeout(stream_timeout_seconds):
                        async for chunk in stream:
                            if not chunk.choices:
                                continue

                            delta = chunk.choices[0].delta

                            # Stream reasoning_content (thinking process) to thinking_chunk
                            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                                await emit_thinking_chunk(self._event_queue, delta.reasoning_content)

                            # Stream content (final answer) - accumulate but don't emit yet
                            if delta.content:
                                response_text += delta.content

                            # Detect tool calls presence
                            if delta.tool_calls:
                                has_tool_calls_in_stream = True
                                for tc in delta.tool_calls:
                                    if tc.function and tc.function.name:
                                        tool_names_seen.add(tc.function.name)
                                        logger.info(f"[AgentCore] Tool detected in stream: {tc.function.name}")

                except asyncio.TimeoutError:
                    logger.warning(f"[AgentCore] Turn {turn_counter}: Stream timeout after {stream_timeout_seconds}s, forcing completion")
                    await emit_thinking(self._event_queue, f"⏱ 推理超时，正在获取最终结果...")
                    # Fallback to non-streaming to get the final state
                    has_tool_calls_in_stream = True  # Force non-streaming check

                # If tool calls were detected in stream, use non-streaming to get complete args
                tool_calls = []
                if has_tool_calls_in_stream:
                    logger.info(f"[AgentCore] Tools detected in stream: {tool_names_seen}, fetching complete tool_calls via non-streaming...")

                    # Non-streaming request to get complete tool_calls with arguments
                    complete_response = await client.chat.completions.create(
                        model=config.openai_model,
                        messages=llm_messages,
                        tools=tools,
                        temperature=self.config.model_temperature,
                        stream=False,
                    )

                    if complete_response.choices and complete_response.choices[0].message.tool_calls:
                        for tc in complete_response.choices[0].message.tool_calls:
                            # Parse args JSON
                            args = {}
                            if tc.function.arguments:
                                try:
                                    args = json.loads(tc.function.arguments)
                                    logger.info(f"[AgentCore] Tool call from non-streaming: {tc.function.name}({args})")
                                except json.JSONDecodeError:
                                    logger.warning(f"[AgentCore] Failed to parse tool args: {tc.function.arguments}")
                                    args = {"raw_args": tc.function.arguments}

                            tool_calls.append({
                                "id": tc.id,
                                "name": tc.function.name,
                                "args": args,
                                "type": "function",
                            })

                    # Also capture any final content from non-streaming response
                    if complete_response.choices and complete_response.choices[0].message.content:
                        response_text = complete_response.choices[0].message.content

                    logger.info(f"[AgentCore] Collected {len(tool_calls)} tool call(s) via non-streaming")

                # If we have tool calls, process them
                if tool_calls:
                    logger.info(f"[AgentCore] Turn {turn_counter}: {len(tool_calls)} tool call(s)")

                    # Build OpenAI-format tool_calls for assistant message
                    openai_tool_calls = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"]),
                            }
                        }
                        for tc in tool_calls
                    ]

                    # Add assistant message with tool_calls to conversation history
                    # OpenAI API requires this before tool result messages
                    messages.append(build_assistant_message(
                        content=response_text,
                        tool_calls=openai_tool_calls,
                    ))

                    # Execute tools
                    tool_result_messages, _ = await self._process_tool_calls(
                        tool_calls, tools, cancel_signal
                    )

                    # If no valid tool calls were processed, treat as normal completion
                    if not tool_result_messages:
                        logger.info(f"[AgentCore] Turn {turn_counter}: Empty tool calls, completing")
                        if response_text and response_text.strip():
                            final_text = response_text.strip()
                            await emit_content(self._event_queue, final_text)
                        break

                    messages.extend(tool_result_messages)

                    # Add a hint for the model to generate final answer
                    # This helps reasoning models understand they should output content now
                    messages.append(build_user_message(
                        "根据上述工具执行结果，请生成最终回复给用户。"
                    ))

                    # Continue the loop
                    continue
                else:
                    # No tool calls — treat this as the model's final answer
                    if response_text and response_text.strip():
                        final_text = response_text.strip()
                        logger.info(f"[AgentCore] Turn {turn_counter}: response_text={response_text[:200]}...")
                        await emit_content(self._event_queue, final_text)
                        logger.info(f"[AgentCore] Turn {turn_counter}: Normal completion")
                        break
                    else:
                        # No content and no tool calls — check if we have tool results from previous turns
                        # This means the model analyzed the results but didn't output a final text
                        # In this case, we should end the loop rather than continue forever
                        has_tool_results = any(msg.role == "tool" for msg in messages)
                        if has_tool_results:
                            # Model has processed tool results but didn't generate text
                            # Likely in reasoning mode — end gracefully
                            logger.info(f"[AgentCore] Turn {turn_counter}: No content after tool results, ending")
                            final_text = "处理完成，请查看上方工具执行结果。"
                            await emit_content(self._event_queue, final_text)
                            break
                        else:
                            # First turn with no response — nudge the model
                            messages.append(build_user_message(
                                "Please provide a response."
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
    ) -> tuple[List[Message], Optional[str]]:
        """Process a list of tool calls.

        Args:
            tool_calls: Tool calls from the model.
            tools: Available tool declarations.
            cancel_signal: Optional cancel signal.

        Returns:
            Tuple of (tool result messages, None).
        """
        tool_result_parts = []

        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_id = tc.get("id", tool_name)

            # Skip empty tool names — treat as normal completion
            if not tool_name or not tool_name.strip():
                logger.warning(f"[AgentCore] Received empty tool name, ignoring: {tc}")
                continue

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

        # Build tool result messages (one per tool call)
        if not tool_result_parts:
            return [], None
        return build_tool_result_messages(tool_result_parts), None

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
