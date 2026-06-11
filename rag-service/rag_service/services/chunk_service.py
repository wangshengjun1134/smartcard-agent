"""Chunk service for knowledge base."""

import uuid
import json
from typing import Optional, List

from rag_service.utils.database import get_knowledge_db_connection
from rag_service.models.chunk import (
    ChunkRecord,
    ChunkResponse,
    ChunkListResponse,
)


class ChunkService:
    """Service class for chunk operations."""

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

    def _to_response(self, record: ChunkRecord) -> ChunkResponse:
        """Convert database record to API response."""
        return ChunkResponse(
            id=record.id,
            doc_id=record.doc_id,
            kb_id=record.kb_id,
            chunk_index=record.chunk_index,
            content=record.content,
            char_count=record.char_count,
            token_count=record.token_count,
            meta=self._parse_json_field(record.meta),
            embedding_model=record.embedding_model,
            embedding_status=record.embedding_status,
            createdAt=record.created_at,
        )

    def create_chunk(
        self,
        doc_id: str,
        kb_id: str,
        chunk_index: int,
        content: str,
        char_count: Optional[int] = None,
        token_count: Optional[int] = None,
        meta: Optional[dict] = None,
        embedding_model: Optional[str] = None,
    ) -> Optional[ChunkResponse]:
        """Create a new chunk record.

        Args:
            doc_id: Document ID.
            kb_id: Knowledge base ID.
            chunk_index: Chunk index (0-based).
            content: Chunk text content.
            char_count: Character count.
            token_count: Token count.
            meta: Chunk metadata.
            embedding_model: Embedding model name.

        Returns:
            ChunkResponse or None if creation failed.
        """
        chunk_id = self._generate_id()
        timestamp = self._get_timestamp()

        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chunks (
                id, doc_id, kb_id, chunk_index, content,
                char_count, token_count, meta,
                embedding_model, embedding_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                chunk_id, doc_id, kb_id, chunk_index, content,
                char_count, token_count,
                json.dumps(meta) if meta else None,
                embedding_model, timestamp,
            )
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM chunks WHERE id = ?",
            (chunk_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = ChunkRecord(
            id=row["id"],
            doc_id=row["doc_id"],
            kb_id=row["kb_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            char_count=row["char_count"],
            token_count=row["token_count"],
            meta=row["meta"],
            embedding_model=row["embedding_model"],
            embedding_status=row["embedding_status"],
            created_at=row["created_at"],
        )

        return self._to_response(record)

    def create_chunks(
        self,
        doc_id: str,
        kb_id: str,
        chunks: List[dict],
    ) -> List[ChunkResponse]:
        """Create multiple chunk records in a batch.

        Args:
            doc_id: Document ID.
            kb_id: Knowledge base ID.
            chunks: List of chunk data dicts with keys:
                chunk_index, content, char_count, token_count, meta, embedding_model.

        Returns:
            List of created ChunkResponse objects.
        """
        results = []
        for chunk_data in chunks:
            result = self.create_chunk(
                doc_id=doc_id,
                kb_id=kb_id,
                **chunk_data,
            )
            if result:
                results.append(result)

        return results

    def get_chunks_by_document(
        self,
        doc_id: str,
        embedding_status: Optional[str] = None,
    ) -> ChunkListResponse:
        """Get all chunks for a document.

        Args:
            doc_id: Document ID.
            embedding_status: Optional filter by embedding status.

        Returns:
            ChunkListResponse with chunks and total count.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if embedding_status:
            cursor.execute(
                """
                SELECT * FROM chunks
                WHERE doc_id = ? AND embedding_status = ?
                ORDER BY chunk_index ASC
                """,
                (doc_id, embedding_status)
            )
        else:
            cursor.execute(
                "SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index ASC",
                (doc_id,)
            )

        rows = cursor.fetchall()
        conn.close()

        chunks = []
        for row in rows:
            record = ChunkRecord(
                id=row["id"],
                doc_id=row["doc_id"],
                kb_id=row["kb_id"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                char_count=row["char_count"],
                token_count=row["token_count"],
                meta=row["meta"],
                embedding_model=row["embedding_model"],
                embedding_status=row["embedding_status"],
                created_at=row["created_at"],
            )
            chunks.append(self._to_response(record))

        return ChunkListResponse(chunks=chunks, total=len(chunks))

    def get_chunks_by_knowledge_base(
        self,
        kb_id: str,
        embedding_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> ChunkListResponse:
        """Get chunks for a knowledge base with pagination.

        Args:
            kb_id: Knowledge base ID.
            embedding_status: Optional filter by embedding status.
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            ChunkListResponse with chunks and total count.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        where_sql = "kb_id = ?"
        params: list = [kb_id]

        if embedding_status:
            where_sql += " AND embedding_status = ?"
            params.append(embedding_status)

        # Get total count
        cursor.execute(
            f"SELECT COUNT(*) as cnt FROM chunks WHERE {where_sql}",
            params
        )
        total = cursor.fetchone()["cnt"]

        # Get chunks
        cursor.execute(
            f"""
            SELECT * FROM chunks WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = cursor.fetchall()
        conn.close()

        chunks = []
        for row in rows:
            record = ChunkRecord(
                id=row["id"],
                doc_id=row["doc_id"],
                kb_id=row["kb_id"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                char_count=row["char_count"],
                token_count=row["token_count"],
                meta=row["meta"],
                embedding_model=row["embedding_model"],
                embedding_status=row["embedding_status"],
                created_at=row["created_at"],
            )
            chunks.append(self._to_response(record))

        return ChunkListResponse(chunks=chunks, total=total)

    def update_chunk_status(
        self,
        chunk_id: str,
        embedding_status: str,
        embedding_model: Optional[str] = None,
    ) -> Optional[ChunkResponse]:
        """Update chunk embedding status.

        Args:
            chunk_id: Chunk ID.
            embedding_status: New embedding status.
            embedding_model: Embedding model name (optional).

        Returns:
            Updated ChunkResponse or None if not found.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if embedding_model:
            cursor.execute(
                """
                UPDATE chunks
                SET embedding_status = ?, embedding_model = ?
                WHERE id = ?
                """,
                (embedding_status, embedding_model, chunk_id)
            )
        else:
            cursor.execute(
                """
                UPDATE chunks
                SET embedding_status = ?
                WHERE id = ?
                """,
                (embedding_status, chunk_id)
            )

        conn.commit()

        cursor.execute(
            "SELECT * FROM chunks WHERE id = ?",
            (chunk_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = ChunkRecord(
            id=row["id"],
            doc_id=row["doc_id"],
            kb_id=row["kb_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            char_count=row["char_count"],
            token_count=row["token_count"],
            meta=row["meta"],
            embedding_model=row["embedding_model"],
            embedding_status=row["embedding_status"],
            created_at=row["created_at"],
        )

        return self._to_response(record)

    def delete_chunks_by_document(self, doc_id: str) -> int:
        """Delete all chunks for a document.

        Args:
            doc_id: Document ID.

        Returns:
            Number of chunks deleted.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chunks WHERE doc_id = ?",
            (doc_id,)
        )
        count = cursor.rowcount
        conn.commit()
        conn.close()

        return count

    def get_pending_chunks(
        self,
        kb_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ChunkResponse]:
        """Get chunks pending embedding.

        Args:
            kb_id: Optional filter by knowledge base ID.
            limit: Maximum number of results.

        Returns:
            List of ChunkResponse objects with pending status.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if kb_id:
            cursor.execute(
                """
                SELECT * FROM chunks
                WHERE embedding_status = 'pending' AND kb_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (kb_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM chunks
                WHERE embedding_status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,)
            )

        rows = cursor.fetchall()
        conn.close()

        chunks = []
        for row in rows:
            record = ChunkRecord(
                id=row["id"],
                doc_id=row["doc_id"],
                kb_id=row["kb_id"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                char_count=row["char_count"],
                token_count=row["token_count"],
                meta=row["meta"],
                embedding_model=row["embedding_model"],
                embedding_status=row["embedding_status"],
                created_at=row["created_at"],
            )
            chunks.append(self._to_response(record))

        return chunks
