"""WebSocket API for real-time APDU events.

Provides a WebSocket endpoint that broadcasts APDU execution events
from agent tool calls to connected frontend clients (APDU Console).
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class APDUEventBroadcaster:
    """Manages WebSocket connections and broadcasts APDU events."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(f"[WS] Client connected, total: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(f"[WS] Client disconnected, total: {len(self._connections)}")

    async def broadcast(self, event: Dict[str, Any]) -> None:
        """Broadcast an event to all connected clients."""
        if not self._connections:
            return

        message = json.dumps(event, ensure_ascii=False)
        async with self._lock:
            dead_connections = []
            for ws in self._connections:
                try:
                    await ws.send_text(message)
                except Exception as e:
                    logger.warning(f"[WS] Failed to send to client: {e}")
                    dead_connections.append(ws)

            # Clean up dead connections
            for ws in dead_connections:
                self._connections.discard(ws)

    def broadcast_sync(self, event: Dict[str, Any]) -> None:
        """Synchronous wrapper for broadcast (called from non-async context).

        This creates a task to broadcast the event in the background.
        """
        asyncio.create_task(self.broadcast(event))


# Global broadcaster instance
_broadcaster: APDUEventBroadcaster = None


def get_broadcaster() -> APDUEventBroadcaster:
    """Get the global APDU event broadcaster."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = APDUEventBroadcaster()
    return _broadcaster


def emit_apdu_event(
    capdu: str,
    rapdu: str,
    sw: str,
    duration_ms: int,
    source: str = "skill",
    error: str = None,
) -> None:
    """Emit an APDU execution event to all connected WebSocket clients.

    This function can be used as an APDU listener for RuntimeContext.

    Args:
        capdu: Command APDU (hex string)
        rapdu: Response APDU (hex string)
        sw: Status word (e.g., "9000")
        duration_ms: Execution duration in milliseconds
        source: Source of the APDU call ("skill", "tool", or "console")
        error: Optional error message
    """
    event = {
        "type": "apdu_event",
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "data": {
            "capdu": capdu,
            "rapdu": rapdu,
            "sw": sw,
            "duration_ms": duration_ms,
            "error": error,
        },
    }

    broadcaster = get_broadcaster()
    broadcaster.broadcast_sync(event)
    logger.debug(f"[APDU Event] {capdu} -> {sw}, broadcasted to {len(broadcaster._connections)} clients")


# FastAPI router
from fastapi import APIRouter

router = APIRouter()


@router.websocket("/ws/apdu")
async def websocket_apdu_events(websocket: WebSocket):
    """WebSocket endpoint for APDU event streaming.

    Frontend APDU Console connects here to receive real-time APDU events
    from agent tool execution.
    """
    broadcaster = get_broadcaster()
    await broadcaster.connect(websocket)

    try:
        # Keep connection alive, client doesn't need to send messages
        while True:
            # Wait for any message (or disconnect)
            # We mainly use this for receiving pings or detecting disconnect
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # No message received, send a ping to check connection
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
    finally:
        await broadcaster.disconnect(websocket)