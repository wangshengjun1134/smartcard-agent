"""Processing log service for knowledge base."""

import uuid
import json
from typing import Optional, List

from rag_service.utils.database import get_knowledge_db_connection
from rag_service.models.processing_log import (
    ProcessingLogRecord,
    ProcessingLogResponse,
    ProcessingLogListResponse,
)


class ProcessingLogService:
    """Service class for processing log operations."""

    def _generate_id(self) -> str:
        """Generate unique ID."""
        return str(uuid.uuid4())

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def _parse_json_field(self, value: Optional[str]) -> Optional[dict]:
        """Parse a JSON string field."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def _to_response(self, record: ProcessingLogRecord) -> ProcessingLogResponse:
        """Convert database record to API response."""
        return ProcessingLogResponse(
            id=record.id,
            doc_id=record.doc_id,
            action=record.action,
            status=record.status,
            details=self._parse_json_field(record.details),
            startedAt=record.started_at,
            finishedAt=record.finished_at,
        )

    def create_log(
        self,
        doc_id: str,
        action: str,
        status: str,
        details: Optional[dict] = None,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> Optional[ProcessingLogResponse]:
        """Create a processing log entry.

        Args:
            doc_id: Document ID.
            action: Action type (parse/chunk/embed/delete).
            status: Log status (started/success/failed).
            details: Action details as dict.
            started_at: Start timestamp.
            finished_at: Finish timestamp.

        Returns:
            ProcessingLogResponse or None if creation failed.
        """
        log_id = self._generate_id()
        timestamp = self._get_timestamp()

        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO processing_logs (
                id, doc_id, action, status, details,
                started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id, doc_id, action, status,
                json.dumps(details) if details else None,
                started_at or timestamp,
                finished_at,
            )
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM processing_logs WHERE id = ?",
            (log_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = ProcessingLogRecord(
            id=row["id"],
            doc_id=row["doc_id"],
            action=row["action"],
            status=row["status"],
            details=row["details"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )

        return self._to_response(record)

    def get_logs_by_document(
        self,
        doc_id: str,
        action: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> ProcessingLogListResponse:
        """Get processing logs for a document.

        Args:
            doc_id: Document ID.
            action: Optional filter by action type.
            status: Optional filter by status.
            limit: Maximum number of results.

        Returns:
            ProcessingLogListResponse with logs and total count.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        where_clauses = ["doc_id = ?"]
        params: list = [doc_id]

        if action:
            where_clauses.append("action = ?")
            params.append(action)
        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = " AND ".join(where_clauses)

        # Get total count
        cursor.execute(
            f"SELECT COUNT(*) as cnt FROM processing_logs WHERE {where_sql}",
            params
        )
        total = cursor.fetchone()["cnt"]

        # Get logs
        cursor.execute(
            f"""
            SELECT * FROM processing_logs WHERE {where_sql}
            ORDER BY started_at DESC
            LIMIT ?
            """,
            params + [limit]
        )
        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            record = ProcessingLogRecord(
                id=row["id"],
                doc_id=row["doc_id"],
                action=row["action"],
                status=row["status"],
                details=row["details"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
            )
            logs.append(self._to_response(record))

        return ProcessingLogListResponse(logs=logs, total=total)

    def get_failed_logs(
        self,
        limit: int = 50,
    ) -> ProcessingLogListResponse:
        """Get failed processing logs for retry.

        Args:
            limit: Maximum number of results.

        Returns:
            ProcessingLogListResponse with failed logs.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM processing_logs
            WHERE status = 'failed'
            ORDER BY finished_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM processing_logs WHERE status = 'failed'"
        )
        total = cursor.fetchone()["cnt"]

        conn.close()

        logs = []
        for row in rows:
            record = ProcessingLogRecord(
                id=row["id"],
                doc_id=row["doc_id"],
                action=row["action"],
                status=row["status"],
                details=row["details"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
            )
            logs.append(self._to_response(record))

        return ProcessingLogListResponse(logs=logs, total=total)

    def update_log(
        self,
        log_id: str,
        status: str,
        details: Optional[dict] = None,
        finished_at: Optional[str] = None,
    ) -> Optional[ProcessingLogResponse]:
        """Update a processing log entry.

        Args:
            log_id: Log ID.
            status: New status.
            details: Optional new details.
            finished_at: Optional finish timestamp.

        Returns:
            ProcessingLogResponse or None if not found.
        """
        timestamp = self._get_timestamp()
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if details is not None:
            cursor.execute(
                "UPDATE processing_logs SET status = ?, details = ?, finished_at = ? WHERE id = ?",
                (status, json.dumps(details), finished_at or timestamp, log_id)
            )
        else:
            cursor.execute(
                "UPDATE processing_logs SET status = ?, finished_at = ? WHERE id = ?",
                (status, finished_at or timestamp, log_id)
            )

        conn.commit()
        cursor.execute("SELECT * FROM processing_logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = ProcessingLogRecord(
            id=row["id"],
            doc_id=row["doc_id"],
            action=row["action"],
            status=row["status"],
            details=row["details"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )

        return self._to_response(record)
