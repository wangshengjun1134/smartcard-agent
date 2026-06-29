"""Chunk data models for knowledge base."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ChunkStatus(str):
    """Chunk embedding status."""
    PENDING = "pending"
    EMBEDDED = "embedded"
    ERROR = "error"


class ChunkRecord(BaseModel):
    """Database record model for chunks table."""

    id: str
    doc_id: str
    kb_id: str
    chunk_index: int
    content: str

    # 章节信息（Docling 分片）
    heading: str = ""               # 章节标题路径，如 "1 Introduction > 1.1 Audience"
    heading_level: int = 0          # 标题层级（1=一级，2=二级...）
    page_start: int = 0             # 起始页码
    page_end: int = 0               # 结束页码

    char_count: Optional[int] = None
    token_count: Optional[int] = None
    meta: Optional[str] = None      # JSON: overlap/is_subchunk/bbox 等
    embedding_model: Optional[str] = None
    embedding_status: str = "pending"
    created_at: str


class ChunkResponse(BaseModel):
    """API response model for chunk."""

    id: str
    doc_id: str
    kb_id: str
    chunk_index: int
    content: str

    # 章节信息
    heading: str = ""
    heading_level: int = 0
    page_start: int = 0
    page_end: int = 0

    char_count: Optional[int] = None
    token_count: Optional[int] = None
    meta: Optional[dict] = None
    embedding_model: Optional[str] = None
    embedding_status: str
    createdAt: str


class ChunkListResponse(BaseModel):
    """API response model for chunk list."""

    chunks: List[ChunkResponse]
    total: int
