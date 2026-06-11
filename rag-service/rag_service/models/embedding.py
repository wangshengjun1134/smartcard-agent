"""Embedding configuration and initialization.

This module provides embedding instances for RAG.
"""

from typing import Optional
from langchain_core.embeddings import Embeddings

from rag_service.config.settings import get_settings


def get_embeddings(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
) -> Embeddings:
    """Get embedding instance.

    Uses local BGE-m3 model as Coding Plan API doesn't support embeddings.

    Args:
        model_name: Model name override
        device: Device override (cpu/cuda)

    Returns:
        Embeddings instance.
    """
    settings = get_settings()

    model = model_name or settings.EMBEDDING_MODEL
    device_str = device or settings.EMBEDDING_DEVICE

    # Use HuggingFace embeddings (sentence-transformers)
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model,
        model_kwargs={"device": device_str},
        encode_kwargs={"normalize_embeddings": True},
    )


# Default embeddings instance
_default_embeddings: Optional[Embeddings] = None


def get_default_embeddings() -> Embeddings:
    """Get the default embeddings instance.

    Returns:
        Default Embeddings instance.
    """
    global _default_embeddings
    if _default_embeddings is None:
        _default_embeddings = get_embeddings()
    return _default_embeddings