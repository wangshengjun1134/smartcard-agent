"""RAG Service settings.

Configuration for knowledge base and retrieval service.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """RAG service settings.

    Attributes:
        LLM_API_KEY: API key for LLM service (for RAG generation)
        LLM_BASE_URL: Base URL for LLM API endpoint
        LLM_MODEL_NAME: Model name for RAG generation

        EMBEDDING_MODEL: Local embedding model name
        EMBEDDING_DEVICE: Device for embedding (cpu or cuda)

        VECTOR_DB_PATH: Path to vector database
        VECTOR_DB_COLLECTION: Collection name for knowledge

        RAG_TOP_K: Number of documents to retrieve
    """

    # LLM Configuration (for RAG generation)
    LLM_API_KEY: str = "sk-sp-xxx"
    LLM_BASE_URL: str = "https://coding.dashscope.aliyuncs.com/v1"
    LLM_MODEL_NAME: str = "qwen3.5-plus"
    LLM_TEMPERATURE: float = 0.0

    # Embedding Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"

    # Vector Database
    VECTOR_DB_HOST: str = "localhost"
    VECTOR_DB_PORT: int = 6333
    VECTOR_DB_GRPC_PORT: int = 6334
    VECTOR_DB_COLLECTION: str = "knowledge_base"
    VECTOR_DB_PREFER_GRPC: bool = False

    # RAG Configuration
    RAG_TOP_K: int = 5
    RAG_RERANK_ENABLED: bool = False

    # File Storage
    STORAGE_PATH: str = "./data/docs"
    KNOWLEDGE_DB_PATH: str = "./data/knowledge.db"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002
    API_DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars not defined in this model


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment/.env."""
    global settings
    settings = Settings()
    return settings