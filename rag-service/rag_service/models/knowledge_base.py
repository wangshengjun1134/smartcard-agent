"""Knowledge base data models."""

from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Request model for creating a knowledge base."""

    name: str
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    """Request model for updating a knowledge base."""

    name: Optional[str] = None
    description: Optional[str] = None


class KnowledgeBaseRecord(BaseModel):
    """Database record model for knowledge_bases table."""

    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str


class KnowledgeBaseResponse(BaseModel):
    """API response model for knowledge base."""

    id: str
    name: str
    description: Optional[str] = None
    createdAt: str
    updatedAt: str
