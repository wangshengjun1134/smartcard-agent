"""Application settings using pydantic-settings.

This module provides centralized configuration management
for the smart card agent service.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings.

    All settings can be overridden via environment variables
    or .env file.

    Attributes:
        LLM_API_KEY: API key for LLM service
        LLM_BASE_URL: Base URL for LLM API endpoint
        LLM_MODEL_NAME: Model name to use
        LLM_TEMPERATURE: Temperature for LLM responses

        VECTOR_DB_PATH: Path to vector database
        CHECKPOINT_PATH: Path for checkpoint storage

        PCSC_READER_INDEX: Default reader index (0 = first reader)
        PCSC_MAX_RETRIES: Max retry attempts for card operations

        RAG_ENABLED: Whether RAG is enabled
        RAG_TOP_K: Number of documents to retrieve
    """

    # LLM Configuration
    LLM_API_KEY: str = "sk-sp-xxx"  # Coding Plan API key format
    LLM_BASE_URL: str = "https://coding.dashscope.aliyuncs.com/v1"
    LLM_MODEL_NAME: str = "qwen3.5-plus"
    LLM_TEMPERATURE: float = 0.0

    # Alternative local LLM (Ollama)
    LOCAL_LLM_ENABLED: bool = False
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_LLM_MODEL: str = "qwen2.5:7b"

    # Embedding Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-m3"  # Local embedding model
    EMBEDDING_DEVICE: str = "cpu"  # cpu or cuda

    # Vector Database
    VECTOR_DB_PATH: str = "./data/vector_db"
    VECTOR_DB_COLLECTION: str = "smartcard_knowledge"

    # Runtime State
    CHECKPOINT_PATH: str = "./data/checkpoints"
    CHECKPOINT_MAX_COUNT: int = 10

    # PCSC Configuration
    PCSC_READER_INDEX: int = 0
    PCSC_MAX_RETRIES: int = 3
    PCSC_RETRY_DELAY: float = 0.5
    PCSC_TIMEOUT: float = 30.0

    # RAG Configuration
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 5
    RAG_RERANK_ENABLED: bool = False

    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 20
    AGENT_TIMEOUT: float = 120.0

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    class Config:
        """Pydantic settings config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance.
    """
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment/.env.

    Returns:
        New Settings instance.
    """
    global settings
    settings = Settings()
    return settings