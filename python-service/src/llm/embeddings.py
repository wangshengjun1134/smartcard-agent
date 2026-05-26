"""Embeddings module for vector generation."""

import os
from typing import Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from .config import LLMConfig
from .local_embeddings import BGEM3Embeddings, get_local_embeddings


# Global embeddings instance cache
_embeddings_cache: Optional[Embeddings] = None


def get_embeddings(config: Optional[LLMConfig] = None) -> Embeddings:
    """Get embeddings model instance (cached).

    根据配置自动选择：
    - 本地模型 (BGE-m3): 当 USE_LOCAL_EMBEDDINGS=true 或无云端 API Key
    - 云端 API (DashScope): 当有标准 DashScope API Key (sk-xxx 格式)

    使用全局单例缓存，避免重复加载模型。

    Args:
        config: LLM configuration. If None, uses default config from env.

    Returns:
        Embeddings instance (OpenAIEmbeddings or BGEM3Embeddings).
    """
    global _embeddings_cache

    # Return cached instance if available
    if _embeddings_cache is not None:
        return _embeddings_cache

    if config is None:
        config = LLMConfig.from_env()

    # 检查是否使用本地 embeddings
    use_local = os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true"

    # 如果明确指定使用本地模型
    if use_local:
        print("Using local embeddings (BGE-m3)")
        device = os.getenv("EMBEDDING_DEVICE", "cpu")
        model_path = os.getenv("LOCAL_EMBEDDING_PATH")
        _embeddings_cache = get_local_embeddings(model_path=model_path, device=device)
        return _embeddings_cache

    # 尝试使用云端 API
    api_key = config.embedding_api_key
    api_base = config.embedding_api_base

    # 如果没有 API Key 或是 Coding Plan Key，回退到本地模型
    if not api_key or api_key.startswith("sk-sp-"):
        print("No valid cloud embeddings API key, using local embeddings (BGE-m3)")
        device = os.getenv("EMBEDDING_DEVICE", "cpu")
        model_path = os.getenv("LOCAL_EMBEDDING_PATH")
        _embeddings_cache = get_local_embeddings(model_path=model_path, device=device)
        return _embeddings_cache

    # 使用云端 API
    print(f"Using cloud embeddings: {config.embedding_model}")
    _embeddings_cache = OpenAIEmbeddings(
        model=config.embedding_model,
        openai_api_key=api_key,
        openai_api_base=api_base,
    )
    return _embeddings_cache


def get_cloud_embeddings(config: Optional[LLMConfig] = None) -> OpenAIEmbeddings:
    """Get cloud embeddings (DashScope/OpenAI) only.

    Args:
        config: LLM configuration.

    Returns:
        OpenAIEmbeddings instance.

    Raises:
        ValueError: If no valid API key provided.
    """
    if config is None:
        config = LLMConfig.from_env()

    api_key = config.embedding_api_key
    api_base = config.embedding_api_base

    if not api_key:
        raise ValueError("Embeddings API key is required. Set DASHSCOPE_API_KEY environment variable.")

    if api_key.startswith("sk-sp-"):
        raise ValueError(
            "Coding Plan API Key (sk-sp-xxx) does not support embeddings API. "
            "Please use standard DashScope API Key (sk-xxx) for embeddings."
        )

    return OpenAIEmbeddings(
        model=config.embedding_model,
        openai_api_key=api_key,
        openai_api_base=api_base,
    )


def get_bge_m3_embeddings(
    model_path: Optional[str] = None,
    device: str = "cpu",
) -> BGEM3Embeddings:
    """Get BGE-m3 local embeddings.

    Args:
        model_path: Local model path (default: data/models/bge-m3).
        device: Device to use (cpu, cuda).

    Returns:
        BGEM3Embeddings instance.
    """
    return get_local_embeddings(model_path=model_path, device=device)