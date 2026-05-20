"""LLM configuration module."""

import os
from dataclasses import dataclass, field
from typing import Optional


# Coding Plan 支持的模型列表 (来自 qwen-code 项目)
CODING_PLAN_MODELS = [
    "qwen3.5-plus",
    "qwen3.6-plus",
    "qwen3-coder-plus",
    "qwen3-coder-next",
    "glm-5",
    "kimi-k2.5",
    "MiniMax-M2.5",
    "qwen3-max-2026-01-23",
    "glm-4.7",
]


@dataclass
class LLMConfig:
    """LLM configuration settings."""

    # OpenAI API settings
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("BAILIAN_CODING_PLAN_API_KEY") or os.getenv("OPENAI_API_KEY"))
    openai_api_base: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_BASE", "https://coding.dashscope.aliyuncs.com/v1"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "qwen3.5-plus"))

    # Embedding settings (需要标准 DashScope API Key)
    embedding_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"))
    embedding_api_base: Optional[str] = field(default_factory=lambda: os.getenv("EMBEDDING_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-v3"))

    # Qdrant settings
    qdrant_host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    qdrant_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    qdrant_collection: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "knowledge_base"))

    # Local LLM settings (for offline mode)
    local_llm_path: Optional[str] = field(default_factory=lambda: os.getenv("LOCAL_LLM_PATH"))
    use_local_llm: bool = field(default_factory=lambda: os.getenv("USE_LOCAL_LLM", "false").lower() == "true")

    def is_valid(self) -> bool:
        """Check if configuration is valid for operation."""
        if self.use_local_llm:
            return self.local_llm_path is not None
        return self.openai_api_key is not None

    def has_embeddings(self) -> bool:
        """Check if embeddings are available."""
        # Embeddings 需要标准 DashScope API Key (非 Coding Plan)
        return self.embedding_api_key is not None and not self.embedding_api_key.startswith("sk-sp-")

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        return cls()