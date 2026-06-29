"""Vector database configuration module."""

from dataclasses import dataclass
from typing import Optional

from rag_service.config.settings import settings


@dataclass
class VectorDBConfig:
    """Qdrant vector database configuration."""

    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    collection_name: str = "knowledge_base"
    prefer_grpc: bool = False

    # Local storage path for embedded Qdrant (not used in service mode)
    local_path: Optional[str] = None

    # Whether to use in-memory Qdrant (for testing/development)
    in_memory: bool = False

    @classmethod
    def from_settings(cls) -> "VectorDBConfig":
        """Create configuration from application settings."""
        return cls(
            host=settings.VECTOR_DB_HOST,
            port=settings.VECTOR_DB_PORT,
            grpc_port=settings.VECTOR_DB_GRPC_PORT,
            collection_name=settings.VECTOR_DB_COLLECTION,
            prefer_grpc=settings.VECTOR_DB_PREFER_GRPC,
        )

    @classmethod
    def default_service(cls) -> "VectorDBConfig":
        """Create a configuration for Qdrant service mode (HTTP)."""
        return cls.from_settings()
