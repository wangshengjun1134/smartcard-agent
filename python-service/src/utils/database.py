"""Database utilities for SQLite connection management."""

import sqlite3
from pathlib import Path
from typing import Optional


# Default database path relative to project root (smartcard-agent)
# Path: python-service/src/utils/database.py -> smartcard-agent/data
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "knowledge.db"
DEFAULT_STORAGE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "docs"


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a SQLite database connection with WAL mode enabled.

    Args:
        db_path: Optional custom database path. Defaults to data/knowledge.db.

    Returns:
        SQLite connection object.
    """
    path = db_path or DEFAULT_DB_PATH

    # Ensure data directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def init_database(db_path: Optional[Path] = None) -> None:
    """Initialize database schema if not exists.

    Args:
        db_path: Optional custom database path.
    """
    conn = get_db_connection(db_path)
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
    """Get the file storage directory path.

    Returns:
        Path to data/docs directory.
    """
    # Ensure storage directory exists
    DEFAULT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    return DEFAULT_STORAGE_PATH