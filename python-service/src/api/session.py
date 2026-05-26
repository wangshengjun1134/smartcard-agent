"""Session API Router for chat session and group management.

This module provides CRUD endpoints for sessions, groups, and messages.
"""

import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.database import get_session_db_connection
from models.session import (
    Session,
    SessionCreate,
    SessionUpdate,
    Group,
    GroupCreate,
    GroupUpdate,
    Message,
    MessageCreate,
)


router = APIRouter(prefix="/session", tags=["session"])


# ========== Helper Functions ==========

def generate_id() -> str:
    """Generate unique ID."""
    return f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:9]}"


def row_to_group(row) -> Group:
    """Convert database row to Group model."""
    return Group(
        id=row["id"],
        name=row["name"],
        icon=row["icon"],
        created_at=row["created_at"],
        is_pinned=bool(row["is_pinned"]),
    )


def row_to_session(row, messages: List[Message] = None) -> Session:
    """Convert database row to Session model."""
    return Session(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        messages=messages or [],
        group_id=row["group_id"],
        is_pinned=bool(row["is_pinned"]),
    )


def row_to_message(row) -> Message:
    """Convert database row to Message model."""
    return Message(
        id=row["id"],
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
    )


def get_session_messages(session_id: str) -> List[Message]:
    """Get all messages for a session."""
    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,)
    )
    messages = [row_to_message(row) for row in cursor.fetchall()]
    conn.close()
    return messages


# ========== Group Endpoints ==========

@router.get("/groups", response_model=List[Group])
async def list_groups() -> List[Group]:
    """List all groups sorted by pinned status and creation time."""
    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM session_groups
        ORDER BY is_pinned DESC, created_at DESC
        """
    )
    groups = [row_to_group(row) for row in cursor.fetchall()]
    conn.close()
    return groups


@router.post("/groups", response_model=Group)
async def create_group(data: GroupCreate) -> Group:
    """Create a new group."""
    group_id = generate_id()
    created_at = int(time.time() * 1000)

    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO session_groups (id, name, icon, created_at, is_pinned)
        VALUES (?, ?, ?, ?, 1)
        """,
        (group_id, data.name, data.icon, created_at)
    )
    conn.commit()
    conn.close()

    return Group(
        id=group_id,
        name=data.name,
        icon=data.icon,
        created_at=created_at,
        is_pinned=True,  # New groups are pinned by default
    )


@router.put("/groups/{group_id}", response_model=Group)
async def update_group(group_id: str, data: GroupUpdate) -> Group:
    """Update a group."""
    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if group exists
    cursor.execute("SELECT * FROM session_groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    # Update fields
    updates = []
    values = []
    if data.name is not None:
        updates.append("name = ?")
        values.append(data.name)
    if data.is_pinned is not None:
        updates.append("is_pinned = ?")
        values.append(int(data.is_pinned))

    if updates:
        values.append(group_id)
        cursor.execute(
            f"UPDATE session_groups SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()

    # Fetch updated row
    cursor.execute("SELECT * FROM session_groups WHERE id = ?", (group_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return row_to_group(updated_row)


@router.delete("/groups/{group_id}")
async def delete_group(group_id: str) -> dict:
    """Delete a group and all its sessions."""
    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if group exists
    cursor.execute("SELECT * FROM session_groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    # Delete all sessions in this group (cascade deletes messages)
    cursor.execute("DELETE FROM sessions WHERE group_id = ?", (group_id,))
    # Delete the group
    cursor.execute("DELETE FROM session_groups WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Group deleted"}


# ========== Session Endpoints ==========

@router.get("/list", response_model=List[Session])
async def list_sessions() -> List[Session]:
    """List all sessions sorted by pinned status and update time."""
    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM sessions
        ORDER BY is_pinned DESC, updated_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    sessions = []
    for row in rows:
        messages = get_session_messages(row["id"])
        sessions.append(row_to_session(row, messages))

    return sessions


@router.post("/create", response_model=Session)
async def create_session(data: SessionCreate) -> Session:
    """Create a new session."""
    session_id = generate_id()
    now = int(time.time() * 1000)

    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (id, title, created_at, updated_at, group_id, is_pinned)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (session_id, data.title, now, now, data.group_id)
    )
    conn.commit()
    conn.close()

    return Session(
        id=session_id,
        title=data.title,
        created_at=now,
        updated_at=now,
        messages=[],
        group_id=data.group_id,
        is_pinned=False,
    )


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str) -> Session:
    """Get a session with all messages."""
    conn = get_session_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = get_session_messages(session_id)
    return row_to_session(row, messages)


@router.put("/{session_id}", response_model=Session)
async def update_session(session_id: str, data: SessionUpdate) -> Session:
    """Update a session."""
    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields
    updates = ["updated_at = ?"]
    values = [int(time.time() * 1000)]

    if data.title is not None:
        updates.append("title = ?")
        values.append(data.title)
    if data.group_id is not None:
        updates.append("group_id = ?")
        values.append(data.group_id)
    if data.is_pinned is not None:
        updates.append("is_pinned = ?")
        values.append(int(data.is_pinned))

    values.append(session_id)
    cursor.execute(
        f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
        values
    )
    conn.commit()

    # Fetch updated row
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    updated_row = cursor.fetchone()
    conn.close()

    messages = get_session_messages(session_id)
    return row_to_session(updated_row, messages)


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a session and all its messages."""
    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete session (cascade deletes messages)
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Session deleted"}


# ========== Message Endpoints ==========

@router.post("/{session_id}/messages", response_model=Message)
async def add_message(session_id: str, data: MessageCreate) -> Message:
    """Add a message to a session."""
    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    # Create message
    message_id = generate_id()
    created_at = int(time.time() * 1000)

    cursor.execute(
        """
        INSERT INTO messages (id, session_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (message_id, session_id, data.role, data.content, created_at)
    )

    # Update session's updated_at and title (if first user message)
    new_title = None
    if data.role == "user":
        # Check if this is the first user message
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ? AND role = 'user'",
            (session_id,)
        )
        count = cursor.fetchone()[0]
        if count == 1:
            # Update title based on first user message
            new_title = data.content[:30] + ("..." if len(data.content) > 30 else "")
            cursor.execute(
                "UPDATE sessions SET updated_at = ?, title = ? WHERE id = ?",
                (created_at, new_title, session_id)
            )
        else:
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (created_at, session_id)
            )
    else:
        cursor.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (created_at, session_id)
        )

    conn.commit()
    conn.close()

    return Message(
        id=message_id,
        role=data.role,
        content=data.content,
        created_at=created_at,
    )


@router.get("/{session_id}/messages", response_model=List[Message])
async def list_messages(session_id: str) -> List[Message]:
    """List all messages in a session."""
    conn = get_session_db_connection()
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    conn.close()
    return get_session_messages(session_id)