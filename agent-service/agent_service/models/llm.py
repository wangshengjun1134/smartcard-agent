"""LLM configuration and initialization.

This module provides LLM instances for the agent.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

from agent_service.config.settings import get_settings
from agent_service.config.logging import get_logger

logger = get_logger(__name__)


class LLMLoggingCallback(BaseCallbackHandler):
    """Callback handler for logging LLM requests and responses."""

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM request starts."""
        model = kwargs.get("invocation_params", {}).get("model", "unknown")
        logger.info(f"[LLM] >>> REQUEST: model={model}")
        for i, prompt in enumerate(prompts):
            # Print full prompt for debugging
            logger.info(f"[LLM] Prompt {i+1}: {prompt}")

    def on_llm_end(self, response, **kwargs):
        """Log when LLM response completes."""
        model = kwargs.get("invocation_params", {}).get("model", "unknown")
        output = response.generations[0][0].text if response.generations else ""
        logger.info(f"[LLM] <<< RESPONSE: model={model}, len={len(output)}")
        # Print full response for debugging
        logger.info(f"[LLM] Response: {output}")

    def on_llm_error(self, error, **kwargs):
        """Log when LLM request fails."""
        logger.error(f"[LLM] ERROR: {error}")


def get_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    use_local: bool = False,
    verbose: bool = True,
) -> ChatOpenAI:
    """Get LLM instance.

    Args:
        model_name: Model name override
        temperature: Temperature override
        use_local: Whether to use local LLM (Ollama)
        verbose: Enable LLM request/response logging

    Returns:
        ChatOpenAI instance.
    """
    settings = get_settings()
    callbacks = [LLMLoggingCallback()] if verbose else None

    if use_local and settings.LOCAL_LLM_ENABLED:
        # Use local Ollama
        return ChatOpenAI(
            model=model_name or settings.LOCAL_LLM_MODEL,
            temperature=temperature or 0.0,
            api_key="ollama",  # Dummy key for Ollama
            base_url=settings.LOCAL_LLM_BASE_URL,
            callbacks=callbacks,
        )

    # Use Coding Plan API
    return ChatOpenAI(
        model=model_name or settings.LLM_MODEL_NAME,
        temperature=temperature or settings.LLM_TEMPERATURE,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        callbacks=callbacks,
    )


# Default LLM instance
_default_llm: Optional[ChatOpenAI] = None


def get_default_llm() -> ChatOpenAI:
    """Get the default LLM instance.

    Returns:
        Default ChatOpenAI instance.
    """
    global _default_llm
    if _default_llm is None:
        _default_llm = get_llm()
    return _default_llm