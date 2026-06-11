"""Knowledge base service."""

import uuid
from typing import Optional

from rag_service.utils.database import get_knowledge_db_connection
from rag_service.models.knowledge_base import (
    KnowledgeBaseRecord,
    KnowledgeBaseResponse,
)


class KnowledgeBaseService:
    """Service class for knowledge base operations."""

    def _generate_id(self) -> str:
        """Generate unique ID."""
        return str(uuid.uuid4())

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Optional[KnowledgeBaseResponse]:
        """Create a new knowledge base.

        Args:
            name: Knowledge base name (must be unique).
            description: Optional description.

        Returns:
            KnowledgeBaseResponse or None if creation failed.

        Raises:
            ValueError: If knowledge base name already exists.
        """
        # Check for duplicate name
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM knowledge_bases WHERE name = ?",
            (name,)
        )
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Knowledge base '{name}' already exists")

        kb_id = self._generate_id()
        timestamp = self._get_timestamp()

        cursor.execute(
            """
            INSERT INTO knowledge_bases (id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (kb_id, name, description, timestamp, timestamp)
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM knowledge_bases WHERE id = ?",
            (kb_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = KnowledgeBaseRecord(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

        return KnowledgeBaseResponse(
            id=record.id,
            name=record.name,
            description=record.description,
            createdAt=record.created_at,
            updatedAt=record.updated_at,
        )

    def list_knowledge_bases(self) -> list[KnowledgeBaseResponse]:
        """List all knowledge bases.

        Returns:
            List of KnowledgeBaseResponse objects.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_bases ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            record = KnowledgeBaseRecord(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            result.append(KnowledgeBaseResponse(
                id=record.id,
                name=record.name,
                description=record.description,
                createdAt=record.created_at,
                updatedAt=record.updated_at,
            ))

        return result

    def get_knowledge_base(
        self,
        kb_id: str,
    ) -> Optional[KnowledgeBaseResponse]:
        """Get a knowledge base by ID.

        Args:
            kb_id: Knowledge base ID.

        Returns:
            KnowledgeBaseResponse or None if not found.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_bases WHERE id = ?",
            (kb_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        record = KnowledgeBaseRecord(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

        return KnowledgeBaseResponse(
            id=record.id,
            name=record.name,
            description=record.description,
            createdAt=record.created_at,
            updatedAt=record.updated_at,
        )

    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[KnowledgeBaseResponse]:
        """Update a knowledge base.

        Args:
            kb_id: Knowledge base ID.
            name: New name (optional).
            description: New description (optional).

        Returns:
            Updated KnowledgeBaseResponse or None if not found.

        Raises:
            ValueError: If new name already exists.
        """
        # Check if exists
        existing = self.get_knowledge_base(kb_id)
        if existing is None:
            return None

        # Check name uniqueness if changing
        if name and name != existing.name:
            conn = get_knowledge_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM knowledge_bases WHERE name = ? AND id != ?",
                (name, kb_id)
            )
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"Knowledge base '{name}' already exists")
            conn.close()

        timestamp = self._get_timestamp()
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        if name is not None and description is not None:
            cursor.execute(
                """
                UPDATE knowledge_bases
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, description, timestamp, kb_id)
            )
        elif name is not None:
            cursor.execute(
                """
                UPDATE knowledge_bases
                SET name = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, timestamp, kb_id)
            )
        elif description is not None:
            cursor.execute(
                """
                UPDATE knowledge_bases
                SET description = ?, updated_at = ?
                WHERE id = ?
                """,
                (description, timestamp, kb_id)
            )

        conn.commit()
        conn.close()

        return self.get_knowledge_base(kb_id)

    def delete_knowledge_base(
        self,
        kb_id: str,
    ) -> bool:
        """Delete a knowledge base and all associated data.

        Due to foreign key constraints, this will cascade delete
        all documents, chunks, and processing logs.

        Args:
            kb_id: Knowledge base ID.

        Returns:
            True if deleted, False if not found.
        """
        conn = get_knowledge_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM knowledge_bases WHERE id = ?",
            (kb_id,)
        )
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted
