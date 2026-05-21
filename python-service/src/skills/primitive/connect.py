"""Reader/Session Primitive Skills - Card connection management.

This module provides skills for managing smart card reader connections
and session lifecycle according to ISO7816 and ETSI TS 102 221.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class ConnectSkill(BaseSkill):
    """Connect to smart card reader.

    Establishes connection to the first available reader and card.
    Returns ATR (Answer To Reset) on successful connection.

    Parameters:
        reader_index: Optional reader index (default: 0)

    Returns:
        SkillResult with ATR bytes in data field.

    Example:
        result = await skill.run(ctx, {"reader_index": 0})
        atr = result.data  # ATR bytes
    """

    name = "connect"
    description = "Connect to smart card reader and get ATR"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute connect skill."""
        reader_index = params.get("reader_index", 0)

        try:
            atr = ctx.pcsc.connect(reader_index)
            
            ctx.runtime_ctx.connect(ctx.pcsc.reader_name, atr)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"reader_index": reader_index},
                success=True,
            )

            return SkillResult(
                success=True,
                data=atr,
                sw=None,
                metadata={
                    "reader_name": ctx.pcsc.reader_name,
                    "atr_hex": atr.hex().upper(),
                }
            )

        except Exception as e:
            from tools.pcsc.exceptions import ReaderNotFoundError, CardNotFoundError
            
            error_type = type(e).__name__
            error_msg = str(e)
            
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"reader_index": reader_index},
                success=False,
            )

            return SkillResult(
                success=False,
                error=f"{error_type}: {error_msg}",
            )

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate connect parameters."""
        reader_index = params.get("reader_index", 0)
        if not isinstance(reader_index, int) or reader_index < 0:
            return False, f"Invalid reader_index: {reader_index}"
        return True, ""


class DisconnectSkill(BaseSkill):
    """Disconnect from smart card reader.

    Terminates the current card session and releases reader resources.

    Parameters:
        None

    Returns:
        SkillResult indicating disconnect success.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "disconnect"
    description = "Disconnect from smart card reader"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute disconnect skill."""
        try:
            ctx.pcsc.disconnect()
            ctx.runtime_ctx.disconnect()

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={},
                success=True,
            )

            return SkillResult(success=True)

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class ReconnectSkill(BaseSkill):
    """Reconnect to smart card after connection loss.

    Attempts to re-establish connection after transient failures.
    Useful for retry scenarios.

    Parameters:
        max_attempts: Maximum reconnect attempts (default: 3)

    Returns:
        SkillResult with new ATR if successful.

    Example:
        result = await skill.run(ctx, {"max_attempts": 3})
    """

    name = "reconnect"
    description = "Reconnect to smart card after connection loss"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute reconnect skill."""
        max_attempts = params.get("max_attempts", 3)
        
        for attempt in range(max_attempts):
            try:
                atr = ctx.pcsc.reconnect()
                ctx.runtime_ctx.connect(ctx.pcsc.reader_name, atr)
                
                ctx.runtime_ctx.record_execution(
                    skill_name=self.name,
                    params={"attempt": attempt + 1},
                    success=True,
                )

                return SkillResult(
                    success=True,
                    data=atr,
                    metadata={"attempt": attempt + 1}
                )

            except Exception:
                if attempt < max_attempts - 1:
                    continue
                    
        return SkillResult(
            success=False,
            error=f"Reconnect failed after {max_attempts} attempts",
        )


class ResetCardSkill(BaseSkill):
    """Reset smart card (cold or warm reset).

    Performs card reset to clear transient state.
    Cold reset: Full power cycle.
    Warm reset: Keep power, reset logic.

    Parameters:
        cold_reset: Perform cold reset (default: False)

    Returns:
        SkillResult with new ATR after reset.

    Example:
        result = await skill.run(ctx, {"cold_reset": True})
    """

    name = "reset_card"
    description = "Reset smart card (cold or warm reset)"
    dangerous = True  # Can interrupt operations
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute reset card skill."""
        cold_reset = params.get("cold_reset", False)

        try:
            atr = ctx.pcsc.reset_card(cold_reset)
            
            # Clear runtime state after reset
            ctx.runtime_ctx.selected_path = ["3F00"]  # Back to MF
            ctx.runtime_ctx.pin_verified = {}
            ctx.runtime_ctx.current_application = None
            
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"cold_reset": cold_reset},
                success=True,
            )

            return SkillResult(
                success=True,
                data=atr,
                metadata={"cold_reset": cold_reset}
            )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class GetReaderInfoSkill(BaseSkill):
    """Get smart card reader information.

    Lists available readers and current reader details.

    Parameters:
        None

    Returns:
        SkillResult with reader list and current reader info.

    Example:
        result = await skill.run(ctx, {})
        readers = result.metadata["readers"]
    """

    name = "get_reader_info"
    description = "Get smart card reader information"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute get reader info skill."""
        try:
            readers = ctx.pcsc.list_readers()
            current_reader = ctx.pcsc.get_reader_info()
            
            return SkillResult(
                success=True,
                metadata={
                    "readers": [{"name": r.name, "index": r.index} for r in readers],
                    "current_reader": {
                        "name": current_reader.name if current_reader else None,
                        "atr": current_reader.atr.hex().upper() if current_reader and current_reader.atr else None,
                    } if current_reader else None,
                    "connected": ctx.pcsc.is_connected,
                }
            )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class OnCardSkill(BaseSkill):
    """Check if card is present in reader.

    Verifies card presence without full connection.

    Parameters:
        reader_index: Reader index to check (default: 0)

    Returns:
        SkillResult with card_present status.

    Example:
        result = await skill.run(ctx, {"reader_index": 0})
        if result.metadata["card_present"]:
            # Card is inserted
    """

    name = "on_card"
    description = "Check if card is present in reader"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute on card check skill."""
        reader_index = params.get("reader_index", 0)

        try:
            # Try to connect briefly to check presence
            from tools.pcsc.exceptions import CardNotFoundError
            
            try:
                ctx.pcsc.connect(reader_index)
                ctx.pcsc.disconnect()
                return SkillResult(
                    success=True,
                    metadata={"card_present": True, "reader_index": reader_index}
                )
            except CardNotFoundError:
                return SkillResult(
                    success=True,
                    metadata={"card_present": False, "reader_index": reader_index}
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class SessionManagementSkill(BaseSkill):
    """Manage card session state.

    Provides session-level operations:
    - begin_transaction: Start exclusive session
    - end_transaction: End exclusive session
    - suspend: Suspend session
    - resume: Resume suspended session

    Parameters:
        action: Session action (begin_transaction, end_transaction, suspend, resume)

    Returns:
        SkillResult with session status.

    Example:
        result = await skill.run(ctx, {"action": "begin_transaction"})
    """

    name = "session_management"
    description = "Manage card session state"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute session management skill."""
        action = params.get("action", "begin_transaction")

        # Note: These are conceptual - actual implementation depends on reader capabilities
        try:
            if action == "begin_transaction":
                # Begin exclusive access
                return SkillResult(
                    success=True,
                    metadata={"session_state": "transaction"}
                )
            elif action == "end_transaction":
                # End exclusive access
                return SkillResult(
                    success=True,
                    metadata={"session_state": "normal"}
                )
            elif action == "suspend":
                # Suspend session (reader-level)
                return SkillResult(
                    success=True,
                    metadata={"session_state": "suspended"}
                )
            elif action == "resume":
                # Resume session
                return SkillResult(
                    success=True,
                    metadata={"session_state": "normal"}
                )
            else:
                return SkillResult(
                    success=False,
                    error=f"Unknown session action: {action}"
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


# Register all Reader Primitive skills
def register_reader_skills(registry: Any) -> None:
    """Register all Reader Primitive skills."""
    registry.register(ConnectSkill(), "primitive")
    registry.register(DisconnectSkill(), "primitive")
    registry.register(ReconnectSkill(), "primitive")
    registry.register(ResetCardSkill(), "primitive")
    registry.register(GetReaderInfoSkill(), "primitive")
    registry.register(OnCardSkill(), "primitive")
    registry.register(SessionManagementSkill(), "primitive")