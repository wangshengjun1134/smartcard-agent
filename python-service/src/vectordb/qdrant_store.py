"""Qdrant vector store service."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional, Any
from pathlib import Path

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from .config import VectorDBConfig
from llm.embeddings import get_embeddings
from llm.config import LLMConfig


class QdrantStore:
    """Qdrant vector store manager for knowledge base."""

    def __init__(
        self,
        config: Optional[VectorDBConfig] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        """Initialize Qdrant vector store.

        Args:
            config: VectorDB configuration.
            llm_config: LLM configuration for embeddings.
        """
        self.config = config or VectorDBConfig.from_env()
        self.llm_config = llm_config or LLMConfig.from_env()
        self._client: Optional[QdrantClient] = None
        self._vector_store: Optional[QdrantVectorStore] = None

    def _get_client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            if self.config.in_memory:
                self._client = QdrantClient(":memory:")
            elif self.config.local_path:
                path = Path(self.config.local_path)
                path.mkdir(parents=True, exist_ok=True)
                self._client = QdrantClient(path=str(path))
            else:
                self._client = QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                    grpc_port=self.config.grpc_port,
                    prefer_grpc=self.config.prefer_grpc,
                )
        return self._client

    def _ensure_collection(self, vector_size: int = 1024) -> None:
        """Ensure the collection exists, create if not.

        Args:
            vector_size: Size of embedding vectors (default: 1024 for BGE-m3).
        """
        client = self._get_client()
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.config.collection_name not in collection_names:
            client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def get_vector_store(self) -> QdrantVectorStore:
        """Get or create vector store instance."""
        if self._vector_store is None:
            client = self._get_client()
            embeddings = get_embeddings(self.llm_config)

            # Ensure collection exists
            self._ensure_collection()

            self._vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.config.collection_name,
                embedding=embeddings,
            )
        return self._vector_store

    async def add_documents(
        self,
        documents: List[Document],
        metadatas: Optional[List[dict]] = None,
    ) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: List of documents to add.
            metadatas: Optional metadata for each document.

        Returns:
            List of document IDs.
        """
        vector_store = self.get_vector_store()
        ids = await vector_store.aadd_documents(documents)
        return ids

    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> List[str]:
        """Add texts to the vector store.

        Args:
            texts: List of texts to add.
            metadatas: Optional metadata for each text.

        Returns:
            List of document IDs.
        """
        vector_store = self.get_vector_store()
        ids = await vector_store.aadd_texts(texts, metadatas=metadatas)
        return ids

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[Document]:
        """Search for similar documents.

        Args:
            query: Query text.
            k: Number of results to return.
            filter: Optional filter for search.

        Returns:
            List of similar documents.
        """
        vector_store = self.get_vector_store()
        results = await vector_store.asimilarity_search(
            query,
            k=k,
            filter=filter,
        )
        return results

    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[tuple[Document, float]]:
        """Search for similar documents with similarity scores.

        Args:
            query: Query text.
            k: Number of results to return.
            filter: Optional filter for search.

        Returns:
            List of tuples of (document, score).
        """
        vector_store = self.get_vector_store()
        results = await vector_store.asimilarity_search_with_score(
            query,
            k=k,
            filter=filter,
        )
        return results

    def delete_collection(self) -> None:
        """Delete the collection."""
        client = self._get_client()
        client.delete_collection(self.config.collection_name)
        self._vector_store = None

    def get_collection_info(self) -> Any:
        """Get collection information."""
        client = self._get_client()
        return client.get_collection(self.config.collection_name)