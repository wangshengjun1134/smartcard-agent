"""Database utilities for Agent service (message.db only)."""

import sqlite3
from pathlib import Path
from typing import Optional


def get_session_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a SQLite database connection for session/message storage.

    Args:
        db_path: Optional custom database path. Defaults to data/message.db.

    Returns:
        SQLite connection object.
    """
    if db_path is None:
        # Path: agent-service/agent_service/utils/database.py -> project-root/data
        base_path = Path(__file__).parent.parent.parent.parent / "data"
        db_path = base_path / "message.db"

    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Enable WAL mode
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def init_session_database(db_path: Optional[Path] = None) -> None:
    """Initialize session/message database schema."""
    conn = get_session_db_connection(db_path)
    cursor = conn.cursor()

    # Create session_groups table
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
            thinking_process TEXT,
            thinking_content TEXT,
            created_at INTEGER NOT NULL,

            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    # Add thinking columns (migration)
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN thinking_process TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN thinking_content TEXT")
    except sqlite3.OperationalError:
        pass

    # Create api_config table
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