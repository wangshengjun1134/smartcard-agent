"""File service for knowledge base operations."""

import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles.os

from models.file import (
    FileRecord,
    FileNode,
    FileDetail,
    FileType,
    detect_file_type,
    get_mime_type,
)
from utils.database import get_knowledge_db_connection, get_storage_path


class FileService:
    """Service class for file operations."""

    def __init__(self):
        """Initialize file service."""
        self.storage_root = get_storage_path()

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def _generate_id(self) -> str:
        """Generate unique file ID."""
        return str(uuid.uuid4())

    def _build_storage_path(self, parent_id: Optional[str], name: str) -> str:
        """Build storage path based on parent hierarchy.

        Args:
            parent_id: Parent folder ID, None for root.
            name: File/folder name.

        Returns:
            Storage path relative to data/docs.
        """
        if parent_id is None:
            return name

        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT storage_path FROM files WHERE id = ? AND status = 'active'",
            (parent_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            raise ValueError(f"Parent folder {parent_id} not found")

        parent_path = row["storage_path"]
        return f"{parent_path}/{name}"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize file/folder name by removing invalid characters.

        Args:
            name: Original name.

        Returns:
            Sanitized name.
        """
        # Remove invalid characters for Windows/Linux
        invalid_chars = r'[\/\\:*?"<>|]'
        sanitized = re.sub(invalid_chars, '_', name)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip().strip('.')
        return sanitized or "unnamed"

    def _resolve_name_conflict(self, parent_id: Optional[str], name: str) -> str:
        """Resolve name conflict by adding sequence number.

        Args:
            parent_id: Parent folder ID.
            name: Original name.

        Returns:
            Unique name.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        # Check if name exists
        cursor.execute(
            "SELECT name FROM files WHERE parent_id IS ? AND name LIKE ? AND status = 'active'",
            (parent_id, name)
        )
        existing = cursor.fetchall()

        if not existing:
            conn.close()
            return name

        # Extract base name and extension
        if '.' in name:
            base, ext = name.rsplit('.', 1)
            pattern = f"{base} (%d).{ext}"
        else:
            base = name
            ext = ""
            pattern = f"{base} (%d)"

        # Find next available number
        counter = 1
        while True:
            new_name = pattern % counter if ext else f"{base} ({counter})"
            cursor.execute(
                "SELECT name FROM files WHERE parent_id IS ? AND name = ? AND status = 'active'",
                (parent_id, new_name)
            )
            if not cursor.fetchone():
                conn.close()
                return new_name
            counter += 1

    def _get_children(self, parent_id: Optional[str]) -> list[FileNode]:
        """Get children files for a parent folder.

        Args:
            parent_id: Parent folder ID, None for root.

        Returns:
            List of FileNode objects.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        # Handle NULL parent_id for root level
        if parent_id is None:
            cursor.execute(
                "SELECT * FROM files WHERE parent_id IS NULL AND status = 'active' ORDER BY is_folder DESC, name ASC"
            )
        else:
            cursor.execute(
                "SELECT * FROM files WHERE parent_id = ? AND status = 'active' ORDER BY is_folder DESC, name ASC",
                (parent_id,)
            )

        rows = cursor.fetchall()
        conn.close()

        children = []
        for row in rows:
            record = FileRecord(
                id=row["id"],
                name=row["name"],
                parent_id=row["parent_id"],
                is_folder=bool(row["is_folder"]),
                file_type=row["file_type"],
                size=row["size"],
                storage_path=row["storage_path"],
                mime_type=row["mime_type"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
                indexed_at=row["indexed_at"],
                status=row["status"],
            )
            # Recursively get children for folders
            sub_children = None
            if record.is_folder:
                sub_children = self._get_children(record.id)
            children.append(record.to_file_node(sub_children))

        return children

    def get_file_tree(self) -> list[FileNode]:
        """Get complete file tree structure.

        Returns:
            List of FileNode objects representing the tree.
        """
        return self._get_children(None)

    def get_file_detail(self, file_id: str) -> Optional[FileDetail]:
        """Get detailed information for a single file.

        Args:
            file_id: File ID to query.

        Returns:
            FileDetail object or None if not found.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE id = ? AND status = 'active'",
            (file_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = FileRecord(
            id=row["id"],
            name=row["name"],
            parent_id=row["parent_id"],
            is_folder=bool(row["is_folder"]),
            file_type=row["file_type"],
            size=row["size"],
            storage_path=row["storage_path"],
            mime_type=row["mime_type"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            indexed_at=row["indexed_at"],
            status=row["status"],
        )

        # Build detail model
        path = f"/docs/{record.storage_path}" if record.storage_path else f"/docs/{record.name}"
        return FileDetail(
            id=record.id,
            name=record.name,
            type=record.file_type,
            path=path,
            isFolder=record.is_folder,
            size=record.size,
            createdAt=record.created_at,
            modifiedAt=record.modified_at,
            mimeType=record.mime_type,
            storagePath=record.storage_path,
            indexed=record.indexed_at is not None,
            chunkCount=0,
            chunks=[],
        )

    def get_file_record(self, file_id: str) -> Optional[FileRecord]:
        """Get file record from database.

        Args:
            file_id: File ID.

        Returns:
            FileRecord or None.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE id = ? AND status = 'active'",
            (file_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return FileRecord(
            id=row["id"],
            name=row["name"],
            parent_id=row["parent_id"],
            is_folder=bool(row["is_folder"]),
            file_type=row["file_type"],
            size=row["size"],
            storage_path=row["storage_path"],
            mime_type=row["mime_type"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            indexed_at=row["indexed_at"],
            status=row["status"],
        )

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        parent_id: Optional[str] = None,
        custom_name: Optional[str] = None,
    ) -> FileNode:
        """Upload a file to the knowledge base.

        Args:
            file_content: File binary content.
            filename: Original filename.
            parent_id: Target folder ID, None for root.
            custom_name: Custom name for the file.

        Returns:
            FileNode for the uploaded file.
        """
        # Sanitize name
        display_name = custom_name or filename
        display_name = self._sanitize_name(display_name)

        # Resolve name conflict
        display_name = self._resolve_name_conflict(parent_id, display_name)

        # Detect file type
        file_type = detect_file_type(display_name)
        mime_type = get_mime_type(display_name, file_type)

        # Build storage path
        storage_path = self._build_storage_path(parent_id, display_name)

        # Generate ID and timestamp
        file_id = self._generate_id()
        timestamp = self._get_timestamp()

        # Save file to disk
        disk_path = self.storage_root / storage_path
        disk_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(disk_path, 'wb') as f:
            await f.write(file_content)

        # Save to database
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO files (id, name, parent_id, is_folder, file_type, size, storage_path, mime_type, created_at, modified_at, status)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (file_id, display_name, parent_id, file_type.value, len(file_content), storage_path, mime_type, timestamp, timestamp)
        )
        conn.commit()
        conn.close()

        # Build response
        path = f"/docs/{storage_path}"
        return FileNode(
            id=file_id,
            name=display_name,
            type=file_type,
            path=path,
            isFolder=False,
            size=len(file_content),
            createdAt=timestamp,
            modifiedAt=timestamp,
        )

    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> FileNode:
        """Create a new folder.

        Args:
            name: Folder name.
            parent_id: Parent folder ID, None for root.

        Returns:
            FileNode for the created folder.
        """
        # Sanitize name
        folder_name = self._sanitize_name(name)

        # Resolve name conflict
        folder_name = self._resolve_name_conflict(parent_id, folder_name)

        # Build storage path
        storage_path = self._build_storage_path(parent_id, folder_name)

        # Generate ID and timestamp
        folder_id = self._generate_id()
        timestamp = self._get_timestamp()

        # Create folder on disk
        disk_path = self.storage_root / storage_path
        disk_path.mkdir(parents=True, exist_ok=True)

        # Save to database
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO files (id, name, parent_id, is_folder, file_type, size, storage_path, created_at, modified_at, status)
            VALUES (?, ?, ?, 1, 'folder', 0, ?, ?, ?, 'active')
            """,
            (folder_id, folder_name, parent_id, storage_path, timestamp, timestamp)
        )
        conn.commit()
        conn.close()

        # Build response
        path = f"/docs/{storage_path}"
        return FileNode(
            id=folder_id,
            name=folder_name,
            type=FileType.FOLDER,
            path=path,
            isFolder=True,
            createdAt=timestamp,
            modifiedAt=timestamp,
            children=[],
        )

    def _get_all_children_ids(self, folder_id: str) -> list[str]:
        """Get all descendant file IDs recursively.

        Args:
            folder_id: Folder ID.

        Returns:
            List of all descendant IDs.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        # Get direct children
        cursor.execute(
            "SELECT id, is_folder FROM files WHERE parent_id = ? AND status = 'active'",
            (folder_id,)
        )
        children = cursor.fetchall()
        conn.close()

        ids = []
        for child in children:
            ids.append(child["id"])
            if bool(child["is_folder"]):
                ids.extend(self._get_all_children_ids(child["id"]))

        return ids

    async def move_file(
        self,
        file_id: str,
        target_folder_id: Optional[str] = None,
    ) -> Optional[FileNode]:
        """Move a file or folder to a new location.

        Args:
            file_id: File/folder ID to move.
            target_folder_id: Target folder ID, None for root.

        Returns:
            Updated FileNode or None if not found.
        """
        # Get current file record
        file_record = self.get_file_record(file_id)
        if file_record is None:
            return None

        # Validate target folder exists
        if target_folder_id is not None:
            target = self.get_file_record(target_folder_id)
            if target is None or not target.is_folder:
                raise ValueError(f"Target folder {target_folder_id} not found or not a folder")

        # Prevent moving into self or descendant
        if file_record.is_folder:
            if target_folder_id == file_id:
                raise ValueError("Cannot move folder into itself")
            if target_folder_id in self._get_all_children_ids(file_id):
                raise ValueError("Cannot move folder into its descendant")

        # Resolve name conflict at target location
        new_name = self._resolve_name_conflict(target_folder_id, file_record.name)

        # Build new storage path
        old_storage_path = file_record.storage_path
        new_storage_path = self._build_storage_path(target_folder_id, new_name)

        # Move file/folder on disk
        old_disk_path = self.storage_root / old_storage_path
        new_disk_path = self.storage_root / new_storage_path

        # Ensure target directory exists
        new_disk_path.parent.mkdir(parents=True, exist_ok=True)

        if old_disk_path.exists():
            await aiofiles.os.rename(old_disk_path, new_disk_path)

        # Update database
        timestamp = self._get_timestamp()
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        # Update the file itself
        cursor.execute(
            """
            UPDATE files
            SET parent_id = ?, name = ?, storage_path = ?, modified_at = ?
            WHERE id = ?
            """,
            (target_folder_id, new_name, new_storage_path, timestamp, file_id)
        )

        # If folder, update all descendants' storage_path
        if file_record.is_folder:
            children_ids = self._get_all_children_ids(file_id)
            for child_id in children_ids:
                child = self.get_file_record(child_id)
                if child and child.storage_path:
                    # Replace old path prefix with new path prefix
                    new_child_path = child.storage_path.replace(
                        old_storage_path, new_storage_path, 1
                    )
                    cursor.execute(
                        "UPDATE files SET storage_path = ?, modified_at = ? WHERE id = ?",
                        (new_child_path, timestamp, child_id)
                    )

        conn.commit()
        conn.close()

        # Return updated node
        updated_record = self.get_file_record(file_id)
        if updated_record:
            children = self._get_children(file_id) if updated_record.is_folder else None
            return updated_record.to_file_node(children)
        return None