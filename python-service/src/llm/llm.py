"""LLM module for language model interaction."""

from typing import Optional

from langchain_openai import ChatOpenAI

from .config import LLMConfig


def get_llm(config: Optional[LLMConfig] = None, temperature: float = 0.7, timeout: float = 60.0) -> ChatOpenAI:
    """Get LLM model instance.

    Args:
        config: LLM configuration. If None, uses config from database (priority) or env.
        temperature: Model temperature for response generation.
        timeout: Request timeout in seconds.

    Returns:
        ChatOpenAI instance.
    """
    if config is None:
        config = LLMConfig.get_config()

    return ChatOpenAI(
        model=config.openai_model,
        temperature=temperature,
        openai_api_key=config.openai_api_key,
        openai_api_base=config.openai_api_base,
        request_timeout=timeout,
        max_retries=2,
    )