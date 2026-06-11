"""Document data models for knowledge base."""

from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentStatus(str):
    """Document processing status."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    ERROR = "error"


class DocumentCreate(BaseModel):
    """Request model for creating a document."""

    kb_id: str
    title: Optional[str] = None
    source: Optional[str] = None
    language: str = "zh"
    tags: Optional[List[str]] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    custom_meta: Optional[dict] = None


class DocumentUpdate(BaseModel):
    """Request model for updating a document."""

    title: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    custom_meta: Optional[dict] = None
    permissions: Optional[dict] = None


class DocumentRecord(BaseModel):
    """Database record model for documents table."""

    id: str
    kb_id: str
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    status: str = "uploaded"
    error_message: Optional[str] = None
    version: int = 1
    is_active: int = 1
    title: Optional[str] = None
    source: Optional[str] = None
    language: str = "zh"
    tags: Optional[str] = None
    permissions: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    custom_meta: Optional[str] = None
    created_at: str
    updated_at: str
    uploaded_by: Optional[str] = None


class DocumentResponse(BaseModel):
    """API response model for document."""

    id: str
    kb_id: str
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    version: int
    title: Optional[str] = None
    source: Optional[str] = None
    language: str = "zh"
    tags: Optional[List[str]] = None
    permissions: Optional[dict] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    custom_meta: Optional[dict] = None
    createdAt: str
    updatedAt: str
    uploadedBy: Optional[str] = None


class DocumentListResponse(BaseModel):
    """API response model for document list."""

    documents: List[DocumentResponse]
    total: int
