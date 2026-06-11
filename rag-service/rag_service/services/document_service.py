"""Document service for knowledge base."""

import uuid
import json
from typing import Optional, List

from rag_service.utils.database import get_knowledge_db_connection
from rag_service.models.document import (
    DocumentRecord,
    DocumentResponse,
    DocumentListResponse,
)


class DocumentService:
    """Service class for document operations."""

    def _generate_id(self) -> str:
        """Generate unique ID."""
        return str(uuid.uuid4())

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def _parse_json_field(self, value: Optional[str]) -> Optional[dict | list]:
        """Parse a JSON string field."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def _to_response(self, record: DocumentRecord) -> DocumentResponse:
        """Convert database record to API response."""
        return DocumentResponse(
            id=record.id,
            kb_id=record.kb_id,
            folder_id=record.folder_id,
            filename=record.filename,
            file_path=record.file_path,
            file_size=record.file_size,
            mime_type=record.mime_type,
            status=record.status,
            error_message=record.error_message,
            version=record.version,
            title=record.title,
            source=record.source,
            language=record.language,
            tags=self._parse_json_field(record.tags),
            permissions=self._parse_json_field(record.permissions),
            effective_from=record.effective_from,
            effective_until=record.effective_until,
            custom_meta=self._parse_json_field(record.custom_meta),
            createdAt=record.created_at,
            updatedAt=record.updated_at,
            uploadedBy=record.uploaded_by,
        )

    def create_document(
        self,
        kb_id: str,
        filename: str,
        folder_id: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None,
        file_hash: Optional[str] = None,
        title: Optional[str] = None,
        source: Optional[str] = None,
        language: str = "zh",
        tags: Optional[List[str]] = None,
        effective_from: Optional[str] = None,
        effective_until: Optional[str] = None,
        custom_meta: Optional[dict] = None,
        uploaded_by: Optional[str] = None,
    ) -> Optional[DocumentResponse]:
        """Create a new document record.

        Args:
            kb_id: Knowledge base ID.
            filename: Original filename.
            file_path: Storage path.
            file_size: File size in bytes.
            mime_type: MIME type.
            file_hash: SHA256 hash for deduplication.
            title: Custom title.
            source: Source description.
            language: Document language (default 'zh').
            tags: List of tags.
            effective_from: Effective start date.
            effective_until: Effective end date.
            custom_meta: Custom metadata.
            uploaded_by: User who uploaded.

        Returns:
            DocumentResponse or None if creation failed.
        """
        doc_id = self._generate_id()
        timestamp = self._get_timestamp()

        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (
                id, kb_id, folder_id, filename, file_path, file_size, mime_type,
                file_hash, status, version, is_active, title, source,
                language, tags, permissions, effective_from, effective_until,
                custom_meta, created_at, updated_at, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'uploaded', 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id, kb_id, folder_id, filename, file_path, file_size, mime_type,
                file_hash, title, source, language,
                json.dumps(tags) if tags else None,
                None,  # permissions
                effective_from, effective_until,
                json.dumps(custom_meta) if custom_meta else None,
                timestamp, timestamp, uploaded_by,
            )
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = DocumentRecord(
            id=row["id"],
            kb_id=row["kb_id"],
            folder_id=row["folder_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            file_hash=row["file_hash"],
            status=row["status"],
            error_message=row["error_message"],
            version=row["version"],
            is_active=row["is_active"],
            title=row["title"],
            source=row["source"],
            language=row["language"],
            tags=row["tags"],
            permissions=row["permissions"],
            effective_from=row["effective_from"],
            effective_until=row["effective_until"],
            custom_meta=row["custom_meta"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            uploaded_by=row["uploaded_by"],
        )

        return self._to_response(record)

    def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        """Get a document by ID.

        Args:
            doc_id: Document ID.

        Returns:
            DocumentResponse or None if not found.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE id = ? AND is_active = 1",
            (doc_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = DocumentRecord(
            id=row["id"],
            kb_id=row["kb_id"],
            folder_id=row["folder_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            file_hash=row["file_hash"],
            status=row["status"],
            error_message=row["error_message"],
            version=row["version"],
            is_active=row["is_active"],
            title=row["title"],
            source=row["source"],
            language=row["language"],
            tags=row["tags"],
            permissions=row["permissions"],
            effective_from=row["effective_from"],
            effective_until=row["effective_until"],
            custom_meta=row["custom_meta"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            uploaded_by=row["uploaded_by"],
        )

        return self._to_response(record)

    def list_documents(
        self,
        kb_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DocumentListResponse:
        """List documents with optional filters.

        Args:
            kb_id: Filter by knowledge base ID.
            status: Filter by document status.
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            DocumentListResponse with documents and total count.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        # Build query with filters
        where_clauses = ["is_active = 1"]
        params: list = []

        if kb_id:
            where_clauses.append("kb_id = ?")
            params.append(kb_id)
        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = " AND ".join(where_clauses)

        # Get total count
        cursor.execute(
            f"SELECT COUNT(*) as cnt FROM documents WHERE {where_sql}",
            params
        )
        total = cursor.fetchone()["cnt"]

        # Get documents
        cursor.execute(
            f"""
            SELECT * FROM documents WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = cursor.fetchall()
        conn.close()

        documents = []
        for row in rows:
            record = DocumentRecord(
                id=row["id"],
                kb_id=row["kb_id"],
                folder_id=row["folder_id"],
                filename=row["filename"],
                file_path=row["file_path"],
                file_size=row["file_size"],
                mime_type=row["mime_type"],
                file_hash=row["file_hash"],
                status=row["status"],
                error_message=row["error_message"],
                version=row["version"],
                is_active=row["is_active"],
                title=row["title"],
                source=row["source"],
                language=row["language"],
                tags=row["tags"],
                permissions=row["permissions"],
                effective_from=row["effective_from"],
                effective_until=row["effective_until"],
                custom_meta=row["custom_meta"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                uploaded_by=row["uploaded_by"],
            )
            documents.append(self._to_response(record))

        return DocumentListResponse(documents=documents, total=total)

    def update_document(
        self,
        doc_id: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        permissions: Optional[dict] = None,
        effective_from: Optional[str] = None,
        effective_until: Optional[str] = None,
        custom_meta: Optional[dict] = None,
    ) -> Optional[DocumentResponse]:
        """Update document metadata.

        Args:
            doc_id: Document ID.
            title: New title.
            source: New source.
            language: New language.
            tags: New tags.
            permissions: New permissions.
            effective_from: New effective start date.
            effective_until: New effective end date.
            custom_meta: New custom metadata.

        Returns:
            Updated DocumentResponse or None if not found.
        """
        existing = self.get_document(doc_id)
        if existing is None:
            return None

        timestamp = self._get_timestamp()
        updates: list[tuple[str, any]] = []

        if title is not None:
            updates.append(("title", title))
        if source is not None:
            updates.append(("source", source))
        if language is not None:
            updates.append(("language", language))
        if tags is not None:
            updates.append(("tags", json.dumps(tags)))
        if permissions is not None:
            updates.append(("permissions", json.dumps(permissions)))
        if effective_from is not None:
            updates.append(("effective_from", effective_from))
        if effective_until is not None:
            updates.append(("effective_until", effective_until))
        if custom_meta is not None:
            updates.append(("custom_meta", json.dumps(custom_meta)))

        if not updates:
            return existing

        updates.append(("updated_at", timestamp))

        set_clause = ", ".join(f"{k} = ?" for k, _ in updates)
        values = [v for _, v in updates] + [doc_id]

        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE documents SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()
        conn.close()

        return self.get_document(doc_id)

    def update_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[DocumentResponse]:
        """Update document processing status.

        Args:
            doc_id: Document ID.
            status: New status (uploaded/parsing/chunking/embedding/ready/error).
            error_message: Error message if status is 'error'.

        Returns:
            Updated DocumentResponse or None if not found.
        """
        timestamp = self._get_timestamp()
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE documents
            SET status = ?, error_message = ?, updated_at = ?
            WHERE id = ? AND is_active = 1
            """,
            (status, error_message, timestamp, doc_id)
        )
        conn.commit()
        conn.close()

        return self.get_document(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Soft delete a document (set is_active = 0).

        Args:
            doc_id: Document ID.

        Returns:
            True if deleted, False if not found.
        """
        timestamp = self._get_timestamp()
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE documents
            SET is_active = 0, updated_at = ?
            WHERE id = ? AND is_active = 1
            """,
            (timestamp, doc_id)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted
