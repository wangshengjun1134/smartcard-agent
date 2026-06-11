"""Checkpoint Manager for runtime state persistence.

This module provides checkpoint management for saving and restoring
runtime context during card operations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from agent_service.runtime.context import RuntimeContext


@dataclass
class Checkpoint:
    """A saved checkpoint of runtime connection state."""

    id: str
    connected: bool
    current_reader: Optional[str]
    atr: Optional[str]  # stored as hex
    timestamp: str
    description: Optional[str] = None


class CheckpointManager:
    """Manager for runtime state checkpoints."""

    def __init__(self, max_checkpoints: int = 10):
        self.max_checkpoints = max_checkpoints
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.checkpoint_order: List[str] = []

    def save_checkpoint(
        self,
        ctx: RuntimeContext,
        description: Optional[str] = None,
    ) -> Checkpoint:
        """Save current runtime context as checkpoint."""
        from datetime import datetime

        checkpoint_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        checkpoint = Checkpoint(
            id=checkpoint_id,
            connected=ctx.connected,
            current_reader=ctx.current_reader,
            atr=ctx.atr.hex() if ctx.atr else None,
            timestamp=datetime.now().isoformat(),
            description=description,
        )

        self.checkpoints[checkpoint_id] = checkpoint
        self.checkpoint_order.append(checkpoint_id)

        while len(self.checkpoint_order) > self.max_checkpoints:
            oldest_id = self.checkpoint_order.pop(0)
            del self.checkpoints[oldest_id]

        return checkpoint

    def restore_checkpoint(
        self,
        ctx: RuntimeContext,
        checkpoint_id: Optional[str] = None,
    ) -> bool:
        """Restore runtime context from checkpoint."""
        if checkpoint_id is None:
            if not self.checkpoint_order:
                return False
            checkpoint_id = self.checkpoint_order[-1]

        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint is None:
            return False

        ctx.connected = checkpoint.connected
        ctx.current_reader = checkpoint.current_reader
        ctx.atr = bytes.fromhex(checkpoint.atr) if checkpoint.atr else None

        return True

    def rollback_state(self, ctx: RuntimeContext, steps: int = 1) -> bool:
        """Rollback state by restoring from latest checkpoint."""
        if steps <= 0:
            return False
        return self.restore_checkpoint(ctx)

    def list_checkpoints(self) -> List[Dict[str, str]]:
        """List all saved checkpoints."""
        return [
            {
                "id": cp.id,
                "timestamp": cp.timestamp,
                "description": cp.description or "",
                "reader": cp.current_reader or "N/A",
            }
            for cp_id in self.checkpoint_order
            if (cp := self.checkpoints.get(cp_id))
        ]

    def clear_checkpoints(self) -> None:
        """Clear all saved checkpoints."""
        self.checkpoints.clear()
        self.checkpoint_order.clear()

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint."""
        if checkpoint_id in self.checkpoints:
            del self.checkpoints[checkpoint_id]
            self.checkpoint_order.remove(checkpoint_id)
            return True
        return False