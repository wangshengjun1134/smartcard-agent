"""Processing log data models for knowledge base."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ProcessingLogAction(str):
    """Processing log action types."""
    PARSE = "parse"
    CHUNK = "chunk"
    EMBED = "embed"
    DELETE = "delete"


class ProcessingLogStatus(str):
    """Processing log status."""
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"


class ProcessingLogRecord(BaseModel):
    """Database record model for processing_logs table."""

    id: str
    doc_id: str
    action: str
    status: str
    details: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class ProcessingLogResponse(BaseModel):
    """API response model for processing log."""

    id: str
    doc_id: str
    action: str
    status: str
    details: Optional[dict] = None
    startedAt: Optional[str] = None
    finishedAt: Optional[str] = None


class ProcessingLogListResponse(BaseModel):
    """API response model for processing log list."""

    logs: List[ProcessingLogResponse]
    total: int
