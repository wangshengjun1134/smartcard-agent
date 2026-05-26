"""Logging utilities for LangGraph nodes.

Provides decorators and helpers for logging node inputs/outputs.
"""

import asyncio
import functools
import json
from typing import Dict, Any, Callable

from config.logging import get_logger

logger = get_logger(__name__)


def log_node_io(node_name: str):
    """Decorator to log node input and output.

    Logs the state entering and exiting the node, filtering out
    large fields to keep logs readable.

    Args:
        node_name: Name of the node for logging

    Returns:
        Decorator function.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def sync_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            # Log input
            input_summary = _summarize_state(state)
            logger.info(f"[{node_name}] >>> INPUT: {json.dumps(input_summary, ensure_ascii=False)}")

            # Execute node
            result = func(state)

            # Log output
            output_summary = _summarize_output(result)
            logger.info(f"[{node_name}] <<< OUTPUT: {json.dumps(output_summary, ensure_ascii=False)}")

            return result

        @functools.wraps(func)
        async def async_wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
            # Log input
            input_summary = _summarize_state(state)
            logger.info(f"[{node_name}] >>> INPUT: {json.dumps(input_summary, ensure_ascii=False)}")

            # Execute node
            result = await func(state, *args, **kwargs)

            # Log output
            output_summary = _summarize_output(result)
            logger.info(f"[{node_name}] <<< OUTPUT: {json.dumps(output_summary, ensure_ascii=False)}")

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _summarize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary of state for logging.

    Args:
        state: Full agent state

    Returns:
        Summarized state dict.
    """
    summary = {}

    # Include key fields
    if "user_input" in state:
        summary["user_input"] = _truncate(state["user_input"], 100)

    if "execution_intent" in state:
        summary["execution_intent"] = state["execution_intent"]

    if "current_goal" in state:
        summary["current_goal"] = state["current_goal"]

    if "selected_skill" in state:
        summary["selected_skill"] = state["selected_skill"]

    if "skill_params" in state and state["skill_params"]:
        summary["skill_params"] = state["skill_params"]

    if "next_action" in state and state["next_action"]:
        summary["next_action"] = state["next_action"]

    # Summarize observations count
    if "observations" in state:
        count = len(state["observations"])
        summary["observations_count"] = count
        if count > 0:
            # Include last observation summary
            last_obs = state["observations"][-1]
            summary["last_observation"] = _summarize_observation(last_obs)

    # Runtime state summary
    if "runtime_state" in state and state["runtime_state"]:
        summary["runtime_state"] = _summarize_runtime_state(state["runtime_state"])

    # Other flags
    if "need_retry" in state:
        summary["need_retry"] = state["need_retry"]

    if "need_rag" in state:
        summary["need_rag"] = state["need_rag"]

    if "retry_count" in state:
        summary["retry_count"] = state["retry_count"]

    if "finished" in state:
        summary["finished"] = state["finished"]

    if "error" in state and state["error"]:
        summary["error"] = _truncate(state["error"], 200)

    return summary


def _summarize_output(output: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary of node output for logging.

    Args:
        output: Node output dict

    Returns:
        Summarized output dict.
    """
    summary = {}

    for key, value in output.items():
        if key == "observations" and value:
            # Only include summary of new observations
            if isinstance(value, list) and len(value) > 0:
                summary["new_observation"] = _summarize_observation(value[-1])
        elif key == "runtime_state" and value:
            summary["runtime_state"] = _summarize_runtime_state(value)
        elif key == "rag_context" and value:
            summary["rag_context_count"] = len(value)
        elif key == "final_response" and value:
            summary["final_response"] = _truncate(str(value), 200)
        elif key == "error" and value:
            summary["error"] = _truncate(str(value), 200)
        else:
            summary[key] = value

    return summary


def _summarize_observation(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize an observation for logging.

    Args:
        obs: Observation dict

    Returns:
        Summarized observation.
    """
    summary = {
        "skill_name": obs.get("skill_name", ""),
        "success": obs.get("success", False),
    }

    if obs.get("sw"):
        summary["sw"] = obs["sw"]

    if obs.get("error"):
        summary["error"] = _truncate(obs["error"], 100)

    # Summarize metadata if present
    if obs.get("metadata"):
        metadata = obs["metadata"]
        if isinstance(metadata, dict):
            # Only include key metadata fields
            for key in ["imsi", "iccid", "card_type", "atr"]:
                if key in metadata:
                    summary[key] = metadata[key]

    return summary


def _summarize_runtime_state(runtime: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize runtime state for logging.

    Args:
        runtime: Runtime state dict

    Returns:
        Summarized runtime state.
    """
    summary = {}

    if "connected" in runtime:
        summary["connected"] = runtime["connected"]

    if "selected_path" in runtime:
        summary["selected_path"] = runtime["selected_path"]

    if "card_type" in runtime:
        summary["card_type"] = runtime["card_type"]

    if "atr" in runtime:
        summary["atr"] = runtime["atr"]

    return summary


def _truncate(text: str, max_len: int) -> str:
    """Truncate text if too long.

    Args:
        text: Text to truncate
        max_len: Maximum length

    Returns:
        Truncated text with ellipsis if needed.
    """
    if not text:
        return text
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."