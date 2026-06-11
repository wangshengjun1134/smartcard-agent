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

    默认使用本地模型 (BGE-m3)。

    使用全局单例缓存，避免重复加载模型。

    Args:
        config: LLM configuration. If None, uses config from database.

    Returns:
        Embeddings instance (OpenAIEmbeddings or BGEM3Embeddings).
    """
    global _embeddings_cache

    # Return cached instance if available
    if _embeddings_cache is not None:
        return _embeddings_cache

    if config is None:
        config = LLMConfig.get_config()

    # 默认使用本地 embeddings (BGE-m3)
    print("Using local embeddings (BGE-m3)")
    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    model_path = os.getenv("LOCAL_EMBEDDING_PATH")
    _embeddings_cache = get_local_embeddings(model_path=model_path, device=device)
    return _embeddings_cache


def get_cloud_embeddings(
    api_key: str,
    api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    model: str = "text-embedding-v3",
) -> OpenAIEmbeddings:
    """Get cloud embeddings (DashScope/OpenAI) only.

    Args:
        api_key: API key for embeddings service.
        api_base: API base URL.
        model: Embedding model name.

    Returns:
        OpenAIEmbeddings instance.

    Raises:
        ValueError: If no valid API key provided.
    """
    if not api_key:
        raise ValueError("Embeddings API key is required.")

    if api_key.startswith("sk-sp-"):
        raise ValueError(
            "Coding Plan API Key (sk-sp-xxx) does not support embeddings API. "
            "Please use standard DashScope API Key (sk-xxx) for embeddings."
        )

    return OpenAIEmbeddings(
        model=model,
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