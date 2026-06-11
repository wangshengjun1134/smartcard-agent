"""File data models for knowledge base."""

import mimetypes
from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """File type enumeration."""
    FOLDER = "folder"
    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    TEXT = "text"
    IMAGE = "image"
    UNKNOWN = "unknown"


# File extension to type mapping
EXTENSION_TYPE_MAP: dict[str, FileType] = {
    ".pdf": FileType.PDF,
    ".doc": FileType.WORD,
    ".docx": FileType.WORD,
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    ".txt": FileType.TEXT,
    ".png": FileType.IMAGE,
    ".jpg": FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
    ".gif": FileType.IMAGE,
    ".webp": FileType.IMAGE,
}

# File type to MIME type mapping
TYPE_MIME_MAP: dict[FileType, str] = {
    FileType.PDF: "application/pdf",
    FileType.WORD: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    FileType.MARKDOWN: "text/markdown",
    FileType.TEXT: "text/plain",
    FileType.IMAGE: "image/png",  # Default, actual will be detected
    FileType.UNKNOWN: "application/octet-stream",
    FileType.FOLDER: "inode/directory",
}


def detect_file_type(filename: str) -> FileType:
    """Detect file type from filename extension.

    Args:
        filename: The filename to analyze.

    Returns:
        Detected FileType.
    """
    if not filename:
        return FileType.UNKNOWN

    # Get lowercase extension
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    ext = f".{ext}" if ext else ""

    return EXTENSION_TYPE_MAP.get(ext, FileType.UNKNOWN)


def get_mime_type(filename: str, file_type: Optional[FileType] = None) -> str:
    """Get MIME type for a file.

    Args:
        filename: The filename to analyze.
        file_type: Optional known file type.

    Returns:
        MIME type string.
    """
    if file_type == FileType.IMAGE:
        # Use mimetypes for accurate image MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "image/png"

    if file_type:
        return TYPE_MIME_MAP.get(file_type, "application/octet-stream")

    # Fallback to mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


class FileRecord(BaseModel):
    """Database record model for files table."""

    id: str
    name: str
    parent_id: Optional[str] = None
    is_folder: bool = False
    file_type: FileType = FileType.UNKNOWN
    size: int = 0
    storage_path: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: str
    modified_at: str
    indexed_at: Optional[str] = None
    status: str = "active"

    def to_file_node(self, children: Optional[list["FileNode"]] = None) -> "FileNode":
        """Convert to API response FileNode model.

        Args:
            children: Optional children list for folders.

        Returns:
            FileNode instance.
        """
        # Build API path (prepend /docs/)
        path = f"/docs/{self.storage_path}" if self.storage_path else f"/docs/{self.name}"

        return FileNode(
            id=self.id,
            name=self.name,
            type=self.file_type,
            path=path,
            isFolder=self.is_folder,
            size=self.size if not self.is_folder else None,
            createdAt=self.created_at,
            modifiedAt=self.modified_at,
            children=children,
        )


class FileNode(BaseModel):
    """API response model for file tree node."""

    id: str
    name: str
    type: FileType
    path: str
    isFolder: bool
    size: Optional[int] = None
    createdAt: str
    modifiedAt: str
    children: Optional[list["FileNode"]] = None


class FileDetail(FileNode):
    """Extended file detail model for single file lookup."""

    mimeType: Optional[str] = None
    storagePath: Optional[str] = None
    indexed: bool = False
    chunkCount: int = 0
    chunks: list = Field(default_factory=list)


class CreateFolderRequest(BaseModel):
    """Request model for creating a folder."""

    name: str
    parent_id: Optional[str] = None


class MoveFileRequest(BaseModel):
    """Request model for moving a file."""

    file_id: str
    target_folder_id: Optional[str] = None


class UploadResponse(BaseModel):
    """Response model for file upload."""

    id: str
    name: str
    type: FileType
    path: str
    isFolder: bool
    size: int
    createdAt: str
    modifiedAt: str


# Update forward references
FileNode.model_rebuild()
FileRecord.model_rebuild()