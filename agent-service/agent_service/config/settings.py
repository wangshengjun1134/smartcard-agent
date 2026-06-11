"""Agent Service settings.

Configuration for smart card operation agent.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Agent service settings.

    Attributes:
        LLM_API_KEY: API key for LLM service
        LLM_BASE_URL: Base URL for LLM API endpoint
        LLM_MODEL_NAME: Model name for agent reasoning

        PCSC_READER_INDEX: Default reader index
        PCSC_MAX_RETRIES: Max retry attempts

        CHECKPOINT_PATH: Path for checkpoint storage
        AGENT_MAX_ITERATIONS: Max reasoning iterations
    """

    # LLM Configuration (for agent reasoning)
    LLM_API_KEY: str = "sk-sp-xxx"
    LLM_BASE_URL: str = "https://coding.dashscope.aliyuncs.com/v1"
    LLM_MODEL_NAME: str = "qwen3.5-plus"
    LLM_TEMPERATURE: float = 0.7

    # Alternative local LLM (Ollama)
    LOCAL_LLM_ENABLED: bool = False
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_LLM_MODEL: str = "qwen2.5:7b"

    # Runtime State
    CHECKPOINT_PATH: str = "./data/checkpoints"
    CHECKPOINT_MAX_COUNT: int = 10

    # PCSC Configuration
    PCSC_READER_INDEX: int = 0
    PCSC_MAX_RETRIES: int = 3
    PCSC_RETRY_DELAY: float = 0.5
    PCSC_TIMEOUT: float = 30.0

    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 20
    AGENT_TIMEOUT: float = 120.0
    AGENT_MAX_TURNS: int = 15
    AGENT_MAX_TIME_MINUTES: float = 10.0

    # Session Database
    SESSION_DB_PATH: str = "./data/session.db"

    # Skills Directory
    SKILLS_DIR: str = "./.skills"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


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