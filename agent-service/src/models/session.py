"""Session models for chat conversation storage.

This module defines Pydantic models for sessions, groups, and messages.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Message(BaseModel):
    """Chat message model."""

    id: str
    role: str  # 'user' | 'assistant'
    content: str
    thinking_process: Optional[str] = None  # JSON with thinking steps and routing
    thinking_content: Optional[str] = None  # Raw thinking text for display
    created_at: int  # Unix timestamp (milliseconds)


class MessageCreate(BaseModel):
    """Message creation request."""

    role: str
    content: str
    thinking_process: Optional[str] = None
    thinking_content: Optional[str] = None


class Session(BaseModel):
    """Chat session model."""

    id: str
    title: str
    created_at: int
    updated_at: int
    messages: List[Message] = []
    group_id: Optional[str] = None
    is_pinned: bool = False


class SessionCreate(BaseModel):
    """Session creation request."""

    title: str = "新会话"
    group_id: Optional[str] = None


class SessionUpdate(BaseModel):
    """Session update request."""

    title: Optional[str] = None
    group_id: Optional[str] = None
    is_pinned: Optional[bool] = None


class Group(BaseModel):
    """Session group model."""

    id: str
    name: str
    icon: str
    created_at: int
    is_pinned: bool = False


class GroupCreate(BaseModel):
    """Group creation request."""

    name: str
    icon: str


class GroupUpdate(BaseModel):
    """Group update request."""

    name: Optional[str] = None
    is_pinned: Optional[bool] = None