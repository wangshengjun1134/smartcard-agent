"""LLM module for language model interaction."""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

from .config import LLMConfig
from config.logging import get_logger

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

    def on_llm_new_token(self, token, **kwargs):
        """Log streaming tokens (optional, can be noisy)."""
        # Uncomment to log each token (verbose)
        # logger.debug(f"[LLM] Token: {token}")


def get_llm(
    config: Optional[LLMConfig] = None,
    temperature: float = 0.7,
    timeout: float = 60.0,
    verbose: bool = True,
) -> ChatOpenAI:
    """Get LLM model instance.

    Args:
        config: LLM configuration. If None, uses config from database (priority) or env.
        temperature: Model temperature for response generation.
        timeout: Request timeout in seconds.
        verbose: Enable LLM request/response logging.

    Returns:
        ChatOpenAI instance.
    """
    if config is None:
        config = LLMConfig.get_config()

    callbacks = [LLMLoggingCallback()] if verbose else None

    return ChatOpenAI(
        model=config.openai_model,
        temperature=temperature,
        openai_api_key=config.openai_api_key,
        openai_api_base=config.openai_api_base,
        request_timeout=timeout,
        max_retries=2,
        callbacks=callbacks,
    )