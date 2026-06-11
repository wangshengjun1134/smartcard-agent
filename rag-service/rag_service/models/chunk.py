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
    char_count: Optional[int] = None
    token_count: Optional[int] = None
    meta: Optional[str] = None
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
