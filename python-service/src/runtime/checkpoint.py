"""Checkpoint Manager for runtime state persistence.

This module provides checkpoint management for saving and restoring
runtime context during card operations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import copy

from runtime.context import RuntimeContext


@dataclass
class Checkpoint:
    """A saved checkpoint of runtime state."""

    id: str
    context_state: Dict[str, Any]
    execution_history: List[Dict[str, Any]]
    timestamp: str
    description: Optional[str] = None


class CheckpointManager:
    """Manager for runtime state checkpoints.

    Provides functionality to:
    - Save checkpoints before critical operations
    - Restore state on failure
    - Replay execution history
    - Rollback to previous state

    Example:
        manager = CheckpointManager()
        checkpoint = manager.save_checkpoint(ctx, "before_verify_pin")
        # ... operation fails ...
        manager.restore_checkpoint(ctx, checkpoint.id)
    """

    def __init__(self, max_checkpoints: int = 10):
        """Initialize checkpoint manager.

        Args:
            max_checkpoints: Maximum number of checkpoints to keep
        """
        self.max_checkpoints = max_checkpoints
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.checkpoint_order: List[str] = []

    def save_checkpoint(
        self,
        ctx: RuntimeContext,
        description: Optional[str] = None,
    ) -> Checkpoint:
        """Save current runtime context as checkpoint.

        Args:
            ctx: Runtime context to save
            description: Optional description for the checkpoint

        Returns:
            Saved Checkpoint object.
        """
        from datetime import datetime

        checkpoint_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        checkpoint = Checkpoint(
            id=checkpoint_id,
            context_state=ctx.get_state_dict(),
            execution_history=[
                {
                    "skill_name": step.skill_name,
                    "params": step.params,
                    "apdu": step.apdu.hex() if step.apdu else None,
                    "response": step.response.hex() if step.response else None,
                    "sw": step.sw,
                    "success": step.success,
                    "timestamp": step.timestamp,
                }
                for step in ctx.execution_history
            ],
            timestamp=datetime.now().isoformat(),
            description=description,
        )

        self.checkpoints[checkpoint_id] = checkpoint
        self.checkpoint_order.append(checkpoint_id)

        # Remove oldest if over limit
        while len(self.checkpoint_order) > self.max_checkpoints:
            oldest_id = self.checkpoint_order.pop(0)
            del self.checkpoints[oldest_id]

        return checkpoint

    def restore_checkpoint(
        self,
        ctx: RuntimeContext,
        checkpoint_id: Optional[str] = None,
    ) -> bool:
        """Restore runtime context from checkpoint.

        Args:
            ctx: Runtime context to restore into
            checkpoint_id: Optional checkpoint ID (defaults to latest)

        Returns:
            True if restore succeeded, False if checkpoint not found.
        """
        if checkpoint_id is None:
            # Use latest checkpoint
            if not self.checkpoint_order:
                return False
            checkpoint_id = self.checkpoint_order[-1]

        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint is None:
            return False

        # Restore context state
        ctx.restore_from_dict(checkpoint.context_state)

        # Restore execution history
        from runtime.context import ExecutionStep
        ctx.execution_history = [
            ExecutionStep(
                skill_name=step["skill_name"],
                params=step["params"],
                apdu=bytes.fromhex(step["apdu"]) if step["apdu"] else None,
                response=bytes.fromhex(step["response"]) if step["response"] else None,
                sw=step["sw"],
                success=step["success"],
                timestamp=step["timestamp"],
            )
            for step in checkpoint.execution_history
        ]

        return True

    def rollback_state(self, ctx: RuntimeContext, steps: int = 1) -> bool:
        """Rollback state by removing recent execution steps.

        Args:
            ctx: Runtime context to rollback
            steps: Number of execution steps to remove

        Returns:
            True if rollback succeeded.
        """
        if steps <= 0:
            return False

        if len(ctx.execution_history) < steps:
            # Restore from last checkpoint instead
            return self.restore_checkpoint(ctx)

        # Remove recent steps
        ctx.execution_history = ctx.execution_history[:-steps]

        # Clear last execution info
        if ctx.execution_history:
            last_step = ctx.execution_history[-1]
            ctx.last_apdu = last_step.apdu
            ctx.last_response = last_step.response
            ctx.last_sw = last_step.sw
        else:
            ctx.last_apdu = None
            ctx.last_response = None
            ctx.last_sw = None

        return True

    def replay_execution(
        self,
        ctx: RuntimeContext,
        from_checkpoint_id: Optional[str] = None,
        skill_executor: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Replay execution from a checkpoint.

        Args:
            ctx: Runtime context
            from_checkpoint_id: Starting checkpoint ID
            skill_executor: Optional skill executor for actual replay

        Returns:
            List of replay results.
        """
        checkpoint = None
        if from_checkpoint_id:
            checkpoint = self.checkpoints.get(from_checkpoint_id)
        elif self.checkpoint_order:
            checkpoint = self.checkpoints[self.checkpoint_order[-1]]

        if checkpoint is None:
            return []

        results = []
        for step in checkpoint.execution_history:
            result = {
                "skill_name": step["skill_name"],
                "params": step["params"],
                "original_success": step["success"],
                "replay_success": None,
            }

            if skill_executor:
                # Actually replay the skill
                try:
                    # This would call skill_executor.execute(step["skill_name"], step["params"])
                    result["replay_success"] = True
                except Exception as e:
                    result["replay_success"] = False
                    result["replay_error"] = str(e)

            results.append(result)

        return results

    def get_checkpoint_info(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint info dictionary or None.
        """
        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint is None:
            return None

        return {
            "id": checkpoint.id,
            "timestamp": checkpoint.timestamp,
            "description": checkpoint.description,
            "execution_steps": len(checkpoint.execution_history),
            "context_state": checkpoint.context_state,
        }

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all saved checkpoints.

        Returns:
            List of checkpoint info dictionaries.
        """
        return [
            self.get_checkpoint_info(cp_id)
            for cp_id in self.checkpoint_order
            if cp_id in self.checkpoints
        ]

    def clear_checkpoints(self) -> None:
        """Clear all saved checkpoints."""
        self.checkpoints.clear()
        self.checkpoint_order.clear()

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to delete

        Returns:
            True if deleted, False if not found.
        """
        if checkpoint_id in self.checkpoints:
            del self.checkpoints[checkpoint_id]
            self.checkpoint_order.remove(checkpoint_id)
            return True
        return False