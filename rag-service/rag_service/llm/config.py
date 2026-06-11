"""LLM configuration module."""

import time
from dataclasses import dataclass
from typing import Optional


# Default API base URL
DEFAULT_API_BASE = "https://coding.dashscope.aliyuncs.com/v1"
DEFAULT_MODEL = "qwen3.5-plus"

# Cache for database config
_config_cache: Optional["LLMConfig"] = None
_cache_time: float = 0
CACHE_EXPIRE_SECONDS = 300  # 5 minutes


@dataclass
class LLMConfig:
    """LLM configuration settings loaded from database."""

    # OpenAI API settings
    openai_api_key: Optional[str] = None
    openai_api_base: str = DEFAULT_API_BASE
    openai_model: str = DEFAULT_MODEL

    def is_valid(self) -> bool:
        """Check if configuration is valid for operation."""
        return self.openai_api_key is not None and len(self.openai_api_key.strip()) > 0

    @classmethod
    def from_db(cls) -> Optional["LLMConfig"]:
        """Create configuration from database (api_config table).

        Returns the most recently updated configuration, or None if not found.
        """
        try:
            from rag_service.utils.database import get_session_db_connection

            conn = get_session_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM api_config
                ORDER BY updated_at DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return cls(
                openai_api_key=row["api_key"],
                openai_api_base=row["base_url"] or DEFAULT_API_BASE,
                openai_model=row["model"] or DEFAULT_MODEL,
            )
        except Exception:
            return None

    @classmethod
    def get_config(cls) -> "LLMConfig":
        """Get LLM configuration with caching.

        Always loads from database. Returns default config if not configured.

        Returns:
            LLMConfig instance.
        """
        global _config_cache, _cache_time

        # Check cache
        current_time = time.time()
        if _config_cache and (current_time - _cache_time) < CACHE_EXPIRE_SECONDS:
            return _config_cache

        # Load from database
        db_config = cls.from_db()
        if db_config:
            _config_cache = db_config
            _cache_time = current_time
            return db_config

        # Return default config (not valid, but provides default values)
        default_config = cls()
        _config_cache = default_config
        _cache_time = current_time
        return default_config

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the config cache."""
        global _config_cache, _cache_time
        _config_cache = None
        _cache_time = 0
