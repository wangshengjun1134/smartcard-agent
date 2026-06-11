"""Vector database configuration module."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VectorDBConfig:
    """Qdrant vector database configuration."""

    host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    grpc_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_GRPC_PORT", "6334")))
    collection_name: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "knowledge_base"))
    prefer_grpc: bool = field(default_factory=lambda: os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true")

    # Local storage path for embedded Qdrant
    local_path: Optional[str] = field(default_factory=lambda: os.getenv("QDRANT_LOCAL_PATH"))

    # Whether to use in-memory Qdrant (for testing/development)
    in_memory: bool = field(default_factory=lambda: os.getenv("QDRANT_IN_MEMORY", "true").lower() == "true")

    @classmethod
    def from_env(cls) -> "VectorDBConfig":
        """Create configuration from environment variables."""
        return cls()