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

    # Create files table (folder hierarchy for UI tree only)
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

    # Create indexes for files
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_parent_id ON files(parent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_name ON files(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")

    # Create knowledge_bases table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id              TEXT PRIMARY KEY,
            kb_id           TEXT NOT NULL REFERENCES knowledge_bases(id),
            folder_id       TEXT REFERENCES files(id) ON DELETE SET NULL,
            filename        TEXT NOT NULL,
            file_path       TEXT,
            file_size       INTEGER,
            mime_type       TEXT,
            file_hash       TEXT,
            status          TEXT NOT NULL DEFAULT 'uploaded',
            error_message   TEXT,
            version         INTEGER NOT NULL DEFAULT 1,
            is_active       INTEGER NOT NULL DEFAULT 1,
            title           TEXT,
            source          TEXT,
            language        TEXT DEFAULT 'zh',
            tags            TEXT,
            permissions     TEXT,
            effective_from  TEXT,
            effective_until TEXT,
            custom_meta     TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
            uploaded_by     TEXT
        )
    """)

    # Add folder_id column migration (if table exists but column doesn't)
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN folder_id TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_folder_id ON documents(folder_id)")
    except sqlite3.OperationalError:
        pass

    # Create chunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id              TEXT PRIMARY KEY,
            doc_id          TEXT NOT NULL REFERENCES documents(id),
            kb_id           TEXT NOT NULL REFERENCES knowledge_bases(id),
            chunk_index     INTEGER NOT NULL,
            content         TEXT NOT NULL,
            char_count      INTEGER,
            token_count     INTEGER,
            meta            TEXT,
            embedding_model TEXT,
            embedding_status TEXT NOT NULL DEFAULT 'pending',
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(doc_id, chunk_index)
        )
    """)

    # Create processing_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_logs (
            id          TEXT PRIMARY KEY,
            doc_id      TEXT NOT NULL REFERENCES documents(id),
            action      TEXT NOT NULL,
            status      TEXT NOT NULL,
            details     TEXT,
            started_at  TEXT,
            finished_at TEXT
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_kb_id ON documents(kb_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_is_active ON documents(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_kb_id ON chunks(kb_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_embedding_status ON chunks(embedding_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_doc_id ON processing_logs(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_status ON processing_logs(status)")

    # Seed default knowledge base if not exists
    cursor.execute(
        """
        INSERT OR IGNORE INTO knowledge_bases (id, name, description, created_at, updated_at)
        VALUES (?, 'smartcard spec', 'smartcard spec', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        """,
        ("00000000-0000-0000-0000-000000000001",)
    )

    conn.commit()
    conn.close()


def get_storage_path() -> Path:
    """Get the file storage directory path."""
    base_path = Path(__file__).parent.parent.parent.parent / "data"
    storage_path = base_path / "docs"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path