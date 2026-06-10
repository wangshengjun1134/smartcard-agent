"""Local embeddings module using BGE-m3 model."""

import os
from pathlib import Path
from typing import Optional

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class BGEM3Embeddings(Embeddings):
    """BGE-m3 local embeddings using sentence-transformers.

    BGE-m3 特点：
    - 多语言支持（中文、英文等）
    - 多粒度表示（dense、sparse、colbert）
    - 高性能（1024 维 dense 向量）
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        model_path: Optional[str] = None,
        device: str = "cpu",
        normalize_embeddings: bool = True,
    ):
        """Initialize BGE-m3 embeddings.

        Args:
            model_name: HuggingFace model name (default: BAAI/bge-m3).
            model_path: Local model path. If provided, loads from local path.
            device: Device to use (cpu, cuda, cuda:0, etc).
            normalize_embeddings: Whether to normalize embeddings.
        """
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings

        # 优先从本地路径加载
        if model_path:
            path = Path(model_path)
            if path.exists():
                print(f"Loading BGE-m3 from local path: {path}")
                self.model = SentenceTransformer(str(path), device=device)
            else:
                print(f"Local path not found: {path}, downloading from HuggingFace...")
                self.model = SentenceTransformer(model_name, device=device)
                # 下载后保存到本地
                self._save_model(path)
        else:
            # 使用默认 data/models 目录
            default_path = Path("data/models/bge-m3")
            if default_path.exists():
                print(f"Loading BGE-m3 from default path: {default_path}")
                self.model = SentenceTransformer(str(default_path), device=device)
            else:
                print(f"Downloading BGE-m3 from HuggingFace...")
                self.model = SentenceTransformer(model_name, device=device)
                # 保存到默认路径
                self._save_model(default_path)

    def _save_model(self, path: Path) -> None:
        """Save model to local path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(path))
        print(f"Model saved to: {path}")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query.

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector.
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async embed documents (calls sync version)."""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Async embed query (calls sync version)."""
        return self.embed_query(text)


def get_local_embeddings(
    model_path: Optional[str] = None,
    device: str = "cpu",
) -> BGEM3Embeddings:
    """Get local BGE-m3 embeddings instance.

    Args:
        model_path: Local model path (default: data/models/bge-m3).
        device: Device to use (cpu, cuda).

    Returns:
        BGEM3Embeddings instance.
    """
    # 默认模型路径
    if model_path is None:
        base_dir = Path(__file__).parent.parent.parent.parent  # python-service 目录
        model_path = str(base_dir / "data" / "models" / "bge-m3")

    return BGEM3Embeddings(model_path=model_path, device=device)