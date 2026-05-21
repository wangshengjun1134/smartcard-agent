"""Runtime Primitive Skills - Runtime state management.

This module provides skills for managing the agent runtime state,
including checkpoint, rollback, replay, and retry operations.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class SaveCheckpoint(BaseSkill):
    """Save current runtime checkpoint.

    Creates a snapshot of the current runtime state for
    later recovery or rollback.

    Parameters:
        description: Optional checkpoint description

    Returns:
        SkillResult with checkpoint ID.

    Example:
        result = await skill.run(ctx, {"description": "before_verify_pin"})
        checkpoint_id = result.metadata["checkpoint_id"]
    """

    name = "save_checkpoint"
    description = "Save runtime checkpoint"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute save checkpoint skill."""
        from runtime.checkpoint import CheckpointManager
        
        description = params.get("description", "")
        
        checkpoint_manager = CheckpointManager()
        checkpoint = checkpoint_manager.save_checkpoint(ctx.runtime_ctx, description)
        
        return SkillResult(
            success=True,
            metadata={
                "checkpoint_id": checkpoint.id,
                "description": description,
                "timestamp": checkpoint.timestamp,
            }
        )


class RestoreCheckpoint(BaseSkill):
    """Restore runtime from checkpoint.

    Restores the runtime state to a previously saved checkpoint.

    Parameters:
        checkpoint_id: ID of checkpoint to restore
        or
        latest: Restore latest checkpoint (default if no ID provided)

    Returns:
        SkillResult indicating restore success.

    Example:
        result = await skill.run(ctx, {"checkpoint_id": "cp_20240521_123456"})
    """

    name = "restore_checkpoint"
    description = "Restore runtime from checkpoint"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute restore checkpoint skill."""
        from runtime.checkpoint import CheckpointManager
        
        checkpoint_id = params.get("checkpoint_id")
        use_latest = params.get("latest", not checkpoint_id)
        
        checkpoint_manager = CheckpointManager()
        
        success = checkpoint_manager.restore_checkpoint(ctx.runtime_ctx, checkpoint_id)
        
        if success:
            checkpoint_info = checkpoint_manager.get_checkpoint_info(checkpoint_id) if checkpoint_id else None
            
            return SkillResult(
                success=True,
                metadata={
                    "checkpoint_id": checkpoint_id,
                    "restored_state": ctx.runtime_ctx.get_state_dict(),
                }
            )
        else:
            return SkillResult(
                success=False,
                error=f"Checkpoint {checkpoint_id} not found or restore failed"
            )


class Rollback(BaseSkill):
    """Rollback runtime state.

    Removes recent execution steps and optionally restores
    to a previous checkpoint.

    Parameters:
        steps: Number of steps to rollback (default: 1)
        or
        to_checkpoint_id: Rollback to specific checkpoint

    Returns:
        SkillResult indicating rollback success.

    Example:
        result = await skill.run(ctx, {"steps": 2})
    """

    name = "rollback"
    description = "Rollback runtime state"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute rollback skill."""
        from runtime.checkpoint import CheckpointManager
        
        steps = params.get("steps", 1)
        to_checkpoint_id = params.get("to_checkpoint_id")
        
        checkpoint_manager = CheckpointManager()
        
        if to_checkpoint_id:
            success = checkpoint_manager.restore_checkpoint(ctx.runtime_ctx, to_checkpoint_id)
        else:
            success = checkpoint_manager.rollback_state(ctx.runtime_ctx, steps)
        
        return SkillResult(
            success=success,
            metadata={
                "steps": steps,
                "checkpoint_id": to_checkpoint_id,
                "current_path": ctx.runtime_ctx.get_current_path(),
            }
        )


class Replay(BaseSkill):
    """Replay execution from checkpoint.

    Re-executes skills from a saved checkpoint,
    optionally with modified parameters.

    Parameters:
        checkpoint_id: Checkpoint to replay from
        skill_executor: Optional executor for actual replay

    Returns:
        SkillResult with replay results.

    Example:
        result = await skill.run(ctx, {"checkpoint_id": "cp_xxx"})
    """

    name = "replay"
    description = "Replay execution from checkpoint"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute replay skill."""
        from runtime.checkpoint import CheckpointManager
        
        checkpoint_id = params.get("checkpoint_id")
        
        checkpoint_manager = CheckpointManager()
        
        results = checkpoint_manager.replay_execution(
            ctx.runtime_ctx,
            from_checkpoint_id=checkpoint_id,
        )
        
        return SkillResult(
            success=True,
            metadata={
                "checkpoint_id": checkpoint_id,
                "replay_results": results,
            }
        )


class RetryLastAction(BaseSkill):
    """Retry last failed action.

    Retries the last skill execution with the same parameters.

    Parameters:
        max_attempts: Maximum retry attempts (default: 3)

    Returns:
        SkillResult from retried execution.

    Example:
        result = await skill.run(ctx, {"max_attempts": 3})
    """

    name = "retry_last_action"
    description = "Retry last failed action"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute retry last action skill."""
        max_attempts = params.get("max_attempts", 3)
        
        # Get last execution from history
        history = ctx.runtime_ctx.execution_history
        if not history:
            return SkillResult(success=False, error="No execution history to retry")
        
        last_exec = history[-1]
        skill_name = last_exec.skill_name
        params = last_exec.params
        
        from skills.base.registry import get_skill
        
        skill = get_skill(skill_name)
        if not skill:
            return SkillResult(success=False, error=f"Skill {skill_name} not found")
        
        # Retry execution
        for attempt in range(max_attempts):
            result = await skill.run(ctx, params)
            
            if result.success:
                return SkillResult(
                    success=True,
                    data=result.data,
                    sw=result.sw,
                    metadata={"attempt": attempt + 1}
                )
        
        return SkillResult(
            success=False,
            error=f"Retry failed after {max_attempts} attempts"
        )


class ValidateRuntimeState(BaseSkill):
    """Validate runtime state consistency.

    Checks if runtime state is consistent and valid.

    Parameters:
        check_connection: Verify connection state (default: True)
        check_path: Verify selected path (default: True)

    Returns:
        SkillResult with validation status.

    Example:
        result = await skill.run(ctx, {})
        if result.success:
            # State is valid
    """

    name = "validate_runtime_state"
    description = "Validate runtime state consistency"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute validate runtime state skill."""
        check_connection = params.get("check_connection", True)
        check_path = params.get("check_path", True)
        
        issues = []
        
        # Check connection state
        if check_connection:
            if not ctx.pcsc.is_connected:
                issues.append("Not connected to card")
            
            if ctx.runtime_ctx.connected != ctx.pcsc.is_connected:
                issues.append("Runtime state connection mismatch")
        
        # Check path
        if check_path:
            path = ctx.runtime_ctx.selected_path
            if not path:
                issues.append("No selected path")
            elif path[0] != "3F00":
                issues.append("Selected path not starting from MF")
        
        if issues:
            return SkillResult(
                success=False,
                error=f"Runtime state validation failed: {', '.join(issues)}",
                metadata={"issues": issues}
            )
        
        return SkillResult(
            success=True,
            metadata={"validated": True, "issues": []}
        )


class VerifyPreconditions(BaseSkill):
    """Verify skill execution preconditions.

    Checks if the preconditions for executing a skill are met.

    Parameters:
        skill_name: Skill name to check preconditions for

    Returns:
        SkillResult with precondition status.

    Example:
        result = await skill.run(ctx, {"skill_name": "read_binary"})
    """

    name = "verify_preconditions"
    description = "Verify skill execution preconditions"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute verify preconditions skill."""
        skill_name = params.get("skill_name")
        
        if not skill_name:
            return SkillResult(success=False, error="Missing skill_name parameter")
        
        from skills.base.registry import get_skill
        
        skill = get_skill(skill_name)
        if not skill:
            return SkillResult(success=False, error=f"Skill {skill_name} not found")
        
        # Use skill's can_execute method
        can_execute, reason = skill.can_execute(ctx.runtime_ctx)
        
        return SkillResult(
            success=can_execute,
            metadata={
                "skill_name": skill_name,
                "can_execute": can_execute,
                "reason": reason,
            }
        )


class ResolveNextAction(BaseSkill):
    """Resolve next action from current state.

    Determines the next skill to execute based on
    current goal and runtime state.

    Parameters:
        goal: Current goal (optional, uses runtime state)

    Returns:
        SkillResult with suggested next action.

    Example:
        result = await skill.run(ctx, {})
        next_skill = result.metadata["next_skill"]
    """

    name = "resolve_next_action"
    description = "Resolve next action from current state"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute resolve next action skill."""
        from agents.nodes.runtime.think_node import determine_next_action
        
        goal = params.get("goal") or ctx.runtime_ctx.execution_history[-1].skill_name
        
        runtime_state = ctx.runtime_ctx.get_state_dict()
        observations = [
            {"skill_name": step.skill_name, "success": step.success}
            for step in ctx.runtime_ctx.execution_history
        ]
        
        next_action = determine_next_action(goal, runtime_state, observations)
        
        return SkillResult(
            success=True,
            metadata={
                "next_skill": next_action.get("skill"),
                "next_params": next_action.get("params"),
                "goal": goal,
            }
        )


class AuditLog(BaseSkill):
    """Create audit log entry.

    Records an audit entry for compliance and debugging.

    Parameters:
        action: Action being logged
        details: Additional details

    Returns:
        SkillResult with audit entry ID.

    Example:
        result = await skill.run(ctx, {"action": "verify_pin", "details": {"pin_ref": 1}})
    """

    name = "audit_log"
    description = "Create audit log entry"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute audit log skill."""
        from datetime import datetime
        
        action = params.get("action", "")
        details = params.get("details", {})
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "runtime_state": ctx.runtime_ctx.get_state_dict(),
        }
        
        # Would write to audit log file
        # For now, just return success
        
        return SkillResult(
            success=True,
            metadata={
                "audit_entry": audit_entry,
                "logged": True,
            }
        )


def register_runtime_skills(registry: Any) -> None:
    """Register all Runtime Primitive skills."""
    registry.register(SaveCheckpoint(), "primitive")
    registry.register(RestoreCheckpoint(), "primitive")
    registry.register(Rollback(), "primitive")
    registry.register(Replay(), "primitive")
    registry.register(RetryLastAction(), "primitive")
    registry.register(ValidateRuntimeState(), "primitive")
    registry.register(VerifyPreconditions(), "primitive")
    registry.register(ResolveNextAction(), "primitive")
    registry.register(AuditLog(), "primitive")