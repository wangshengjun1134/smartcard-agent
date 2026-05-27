"""Database utilities for SQLite connection management."""

import sqlite3
from pathlib import Path
from typing import Optional


# Pre-computed database paths (computed once at module load)
_DEFAULT_DB_PATH: Optional[Path] = None
_DEFAULT_SESSION_DB_PATH: Optional[Path] = None
_DEFAULT_STORAGE_PATH: Optional[Path] = None


def _get_db_paths():
    """Lazy compute database paths."""
    global _DEFAULT_DB_PATH, _DEFAULT_SESSION_DB_PATH, _DEFAULT_STORAGE_PATH
    if _DEFAULT_DB_PATH is None:
        # Path: python-service/src/utils/database.py -> smartcard-agent/data
        base_path = Path(__file__).parent.parent.parent.parent / "data"
        _DEFAULT_DB_PATH = base_path / "knowledge.db"
        _DEFAULT_SESSION_DB_PATH = base_path / "message.db"
        _DEFAULT_STORAGE_PATH = base_path / "docs"
    return _DEFAULT_DB_PATH, _DEFAULT_SESSION_DB_PATH, _DEFAULT_STORAGE_PATH


def get_knowledge_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a SQLite database connection for knowledge base.

    Args:
        db_path: Optional custom database path. Defaults to data/knowledge.db.

    Returns:
        SQLite connection object.
    """
    default_db_path, _, _ = _get_db_paths()
    path = db_path or default_db_path

    # Ensure data directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def get_session_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a SQLite database connection for session/message storage.

    Args:
        db_path: Optional custom database path. Defaults to data/message.db.

    Returns:
        SQLite connection object.
    """
    _, default_session_db_path, _ = _get_db_paths()
    path = db_path or default_session_db_path

    # Ensure data directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def init_knowledge_database(db_path: Optional[Path] = None) -> None:
    """Initialize knowledge base database schema if not exists.

    Args:
        db_path: Optional custom database path.
    """
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


def init_session_database(db_path: Optional[Path] = None) -> None:
    """Initialize session/message database schema if not exists.

    Args:
        db_path: Optional custom database path.
    """
    conn = get_session_db_connection(db_path)
    cursor = conn.cursor()

    # Create session groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            is_pinned INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            group_id TEXT,
            is_pinned INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY (group_id) REFERENCES session_groups(id) ON DELETE SET NULL
        )
    """)

    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at INTEGER NOT NULL,

            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    # Create api_config table for storing LLM provider settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_config (
            id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_group_id ON sessions(group_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")

    conn.commit()
    conn.close()


def get_storage_path() -> Path:
    """Get the file storage directory path.

    Returns:
        Path to data/docs directory.
    """
    _, _, storage_path = _get_db_paths()
    # Ensure storage directory exists
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path