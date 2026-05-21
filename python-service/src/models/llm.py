"""LLM configuration and initialization.

This module provides LLM instances for the agent.
"""

from typing import Optional
from langchain_openai import ChatOpenAI

from config.settings import get_settings


def get_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    use_local: bool = False,
) -> ChatOpenAI:
    """Get LLM instance.

    Args:
        model_name: Model name override
        temperature: Temperature override
        use_local: Whether to use local LLM (Ollama)

    Returns:
        ChatOpenAI instance.
    """
    settings = get_settings()

    if use_local and settings.LOCAL_LLM_ENABLED:
        # Use local Ollama
        return ChatOpenAI(
            model=model_name or settings.LOCAL_LLM_MODEL,
            temperature=temperature or 0.0,
            api_key="ollama",  # Dummy key for Ollama
            base_url=settings.LOCAL_LLM_BASE_URL,
        )

    # Use Coding Plan API
    return ChatOpenAI(
        model=model_name or settings.LLM_MODEL_NAME,
        temperature=temperature or settings.LLM_TEMPERATURE,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
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