"""Database utilities for RAG service (knowledge.db only)."""

import sqlite3
from pathlib import Path
from typing import Optional


def get_knowledge_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a SQLite database connection for knowledge base.

    Args:
        db_path: Optional custom database path. Defaults to data/knowledge.db.

    Returns:
        SQLite connection object.
    """
    if db_path is None:
        # Path: rag-service/src/utils/database.py -> rag-service/data
        base_path = Path(__file__).parent.parent.parent.parent / "data"
        db_path = base_path / "knowledge.db"

    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def init_knowledge_database(db_path: Optional[Path] = None) -> None:
    """Initialize knowledge base database schema if not exists."""
    conn = get_knowledge_db_connection(db_path)
    cursor = conn.cursor()

    # Create files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parent_id TEXT,
            is_folder INTEGER NOT NULL DEFAULT 0,
            file_type TEXT,
            size INTEGER DEFAULT 0,
            storage_path TEXT,
            mime_type TEXT,
            created_at TEXT NOT NULL,
            modified_at TEXT NOT NULL,
            indexed_at TEXT,
            status TEXT DEFAULT 'active',

            FOREIGN KEY (parent_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_parent_id ON files(parent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_name ON files(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")

    conn.commit()
    conn.close()


def get_storage_path() -> Path:
    """Get the file storage directory path."""
    base_path = Path(__file__).parent.parent.parent.parent / "data"
    storage_path = base_path / "docs"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path