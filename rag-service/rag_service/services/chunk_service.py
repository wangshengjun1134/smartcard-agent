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
        return str(uuid.uuid4())

    def _get_timestamp(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def _parse_json_field(self, value: Optional[str]) -> Optional[dict]:
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def _to_response(self, record: ChunkRecord) -> ChunkResponse:
        return ChunkResponse(
            id=record.id,
            doc_id=record.doc_id,
            kb_id=record.kb_id,
            chunk_index=record.chunk_index,
            content=record.content,
            heading=record.heading,
            heading_level=record.heading_level,
            page_start=record.page_start,
            page_end=record.page_end,
            char_count=record.char_count,
            token_count=record.token_count,
            meta=self._parse_json_field(record.meta),
            embedding_model=record.embedding_model,
            embedding_status=record.embedding_status,
            createdAt=record.created_at,
        )

    def _row_to_record(self, row) -> ChunkRecord:
        """Convert a database row to ChunkRecord."""
        keys = set(row.keys()) if hasattr(row, 'keys') else set()
        return ChunkRecord(
            id=row["id"],
            doc_id=row["doc_id"],
            kb_id=row["kb_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            heading=row["heading"] if "heading" in keys else "",
            heading_level=row["heading_level"] if "heading_level" in keys else 0,
            page_start=row["page_start"] if "page_start" in keys else 0,
            page_end=row["page_end"] if "page_end" in keys else 0,
            char_count=row["char_count"] if "char_count" in keys else None,
            token_count=row["token_count"] if "token_count" in keys else None,
            meta=row["meta"] if "meta" in keys else None,
            embedding_model=row["embedding_model"] if "embedding_model" in keys else None,
            embedding_status=row["embedding_status"],
            created_at=row["created_at"],
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
        heading: str = "",
        heading_level: int = 0,
        page_start: int = 0,
        page_end: int = 0,
    ) -> Optional[ChunkResponse]:
        chunk_id = self._generate_id()
        timestamp = self._get_timestamp()

        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chunks (
                id, doc_id, kb_id, chunk_index, content,
                heading, heading_level, page_start, page_end,
                char_count, token_count, meta,
                embedding_model, embedding_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                chunk_id, doc_id, kb_id, chunk_index, content,
                heading, heading_level, page_start, page_end,
                char_count, token_count,
                json.dumps(meta) if meta else None,
                embedding_model, timestamp,
            )
        )
        conn.commit()

        cursor.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return self._to_response(self._row_to_record(row))

    def create_chunks(self, doc_id: str, kb_id: str, chunks: List[dict]) -> List[ChunkResponse]:
        results = []
        for chunk_data in chunks:
            result = self.create_chunk(doc_id=doc_id, kb_id=kb_id, **chunk_data)
            if result:
                results.append(result)
        return results

    def get_chunks_by_document(self, doc_id: str, embedding_status: Optional[str] = None) -> ChunkListResponse:
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if embedding_status:
            cursor.execute(
                "SELECT * FROM chunks WHERE doc_id = ? AND embedding_status = ? ORDER BY chunk_index ASC",
                (doc_id, embedding_status)
            )
        else:
            cursor.execute("SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index ASC", (doc_id,))

        rows = cursor.fetchall()
        conn.close()

        chunks = [self._to_response(self._row_to_record(row)) for row in rows]
        return ChunkListResponse(chunks=chunks, total=len(chunks))

    def get_chunks_by_knowledge_base(self, kb_id: str, embedding_status: Optional[str] = None, limit: int = 100, offset: int = 0) -> ChunkListResponse:
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        where_sql = "kb_id = ?"
        params: list = [kb_id]

        if embedding_status:
            where_sql += " AND embedding_status = ?"
            params.append(embedding_status)

        cursor.execute(f"SELECT COUNT(*) as cnt FROM chunks WHERE {where_sql}", params)
        total = cursor.fetchone()["cnt"]

        cursor.execute(
            f"SELECT * FROM chunks WHERE {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        )
        rows = cursor.fetchall()
        conn.close()

        chunks = [self._to_response(self._row_to_record(row)) for row in rows]
        return ChunkListResponse(chunks=chunks, total=total)

    def update_chunk_status(self, chunk_id: str, embedding_status: str, embedding_model: Optional[str] = None) -> Optional[ChunkResponse]:
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if embedding_model:
            cursor.execute("UPDATE chunks SET embedding_status = ?, embedding_model = ? WHERE id = ?", (embedding_status, embedding_model, chunk_id))
        else:
            cursor.execute("UPDATE chunks SET embedding_status = ? WHERE id = ?", (embedding_status, chunk_id))

        conn.commit()
        cursor.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return self._to_response(self._row_to_record(row))

    def delete_chunks_by_document(self, doc_id: str) -> int:
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def get_pending_chunks(self, kb_id: Optional[str] = None, limit: int = 50) -> List[ChunkResponse]:
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if kb_id:
            cursor.execute(
                "SELECT * FROM chunks WHERE embedding_status = 'pending' AND kb_id = ? ORDER BY created_at ASC LIMIT ?",
                (kb_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM chunks WHERE embedding_status = 'pending' ORDER BY created_at ASC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        conn.close()

        return [self._to_response(self._row_to_record(row)) for row in rows]
