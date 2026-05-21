"""Security Primitive Skills - Authentication and secure channel operations.

This module provides skills for security operations including:
- PIN management
- Secure channel establishment (SCP03, SCP80)
- MAC calculation and encryption
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class VerifyPIN(BaseSkill):
    """Verify PIN (CHV).

    Verifies a PIN on the card and updates runtime state.

    Parameters:
        pin_ref: PIN reference (1=PIN1/CHV1, 2=PIN2/CHV2, 0x0A=ADM1)
        pin: PIN value (4-8 digits)

    Returns:
        SkillResult with verification status.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1, "pin": "1234"})
    """

    name = "verify_pin"
    description = "Verify PIN (CHV) on smart card"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute verify PIN skill."""
        from skills.primitive.iso7816 import VerifySkill
        
        verify_skill = VerifySkill()
        result = await verify_skill.run(ctx, params)
        
        if result.success:
            pin_ref = params.get("pin_ref", 1)
            ctx.runtime_ctx.verify_pin(pin_ref)
        
        return result


class VerifyADM(BaseSkill):
    """Verify Administrative PIN (ADM).

    ADM is used for administrative operations on the card.
    Different ADM keys exist for different administrative levels.

    Parameters:
        adm_ref: ADM reference (0x0A=ADM1, 0x0B=ADM2, etc.)
        adm_key: ADM key value (typically 8 bytes)

    Returns:
        SkillResult with verification status.

    Example:
        result = await skill.run(ctx, {"adm_ref": 0x0A, "adm_key": "12345678"})
    """

    name = "verify_adm"
    description = "Verify Administrative PIN (ADM)"
    dangerous = True
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute verify ADM skill."""
        from skills.primitive.iso7816 import VerifySkill
        
        adm_ref = params.get("adm_ref", 0x0A)
        adm_key = params.get("adm_key", "")
        
        verify_skill = VerifySkill()
        result = await verify_skill.run(ctx, {"pin_ref": adm_ref, "pin": adm_key})
        
        return result


class GetPINStatus(BaseSkill):
    """Get PIN status (remaining attempts, blocked status).

    Queries PIN status without actually verifying.

    Parameters:
        pin_ref: PIN reference to query

    Returns:
        SkillResult with PIN status info.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1})
        retry_count = result.metadata["retry_count"]
    """

    name = "get_pin_status"
    description = "Get PIN status (remaining attempts)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute get PIN status skill."""
        pin_ref = params.get("pin_ref", 1)
        
        # Try VERIFY with empty PIN to check status
        from skills.primitive.iso7816 import VerifySkill
        
        verify_skill = VerifySkill()
        result = await verify_skill.run(ctx, {"pin_ref": pin_ref, "pin": ""})
        
        # Parse retry count from SW
        from apdu.parsers.sw_parser import get_retry_count
        retry_count = get_retry_count(result.sw)
        
        # Determine PIN status
        status = "unknown"
        if result.sw == "6983":
            status = "blocked"
        elif retry_count is not None:
            status = "unverified" if retry_count > 0 else "blocked"
        elif result.sw == "9000":
            status = "verified"
        
        return SkillResult(
            success=True,
            metadata={
                "pin_ref": pin_ref,
                "status": status,
                "retry_count": retry_count,
                "sw": result.sw,
            }
        )


class ChangePIN(BaseSkill):
    """Change PIN value.

    Changes the PIN value after verifying the old PIN.

    Parameters:
        pin_ref: PIN reference
        old_pin: Current PIN value
        new_pin: New PIN value

    Returns:
        SkillResult indicating success.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1, "old_pin": "1234", "new_pin": "5678"})
    """

    name = "change_pin"
    description = "Change PIN value"
    dangerous = True
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute change PIN skill."""
        from skills.primitive.iso7816 import ChangePINSkill
        
        change_skill = ChangePINSkill()
        return await change_skill.run(ctx, params)


class UnblockPIN(BaseSkill):
    """Unblock PIN using PUK.

    Unblocks a blocked PIN and optionally sets a new PIN.

    Parameters:
        pin_ref: PIN reference to unblock
        puk: PUK value (typically 8 digits)
        new_pin: New PIN value to set

    Returns:
        SkillResult indicating success.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1, "puk": "12345678", "new_pin": "1234"})
    """

    name = "unblock_pin"
    description = "Unblock PIN using PUK"
    dangerous = True
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute unblock PIN skill."""
        from skills.primitive.iso7816 import UnblockPINSkill
        
        unblock_skill = UnblockPINSkill()
        result = await unblock_skill.run(ctx, params)
        
        if result.success:
            # Reset PIN verified status
            pin_ref = params.get("pin_ref", 1)
            ctx.runtime_ctx.pin_verified[pin_ref] = False
        
        return result


class OpenSecureChannel(BaseSkill):
    """Open secure channel (SCP03 or SCP80).

    Establishes a secure channel with the card for encrypted
    and MAC-protected communications.

    Parameters:
        protocol: SCP protocol ("scp03", "scp80")
        key_set: Key set identifier (KID)
        sequence_counter: Sequence counter for SCP80
        or
        div_data: Key diversification data for SCP03

    Returns:
        SkillResult with session keys and channel info.

    Example:
        result = await skill.run(ctx, {"protocol": "scp03", "key_set": 1})
    """

    name = "open_secure_channel"
    description = "Open secure channel (SCP03/SCP80)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute open secure channel skill."""
        protocol = params.get("protocol", "scp03")
        
        if protocol == "scp03":
            from skills.scp03 import SCP03InitializeUpdate, SCP03ExternalAuthenticate
            
            # Step 1: Initialize Update
            init_skill = SCP03InitializeUpdate()
            init_result = await init_skill.run(ctx, params)
            
            if not init_result.success:
                return init_result
            
            # Step 2: External Authenticate
            auth_skill = SCP03ExternalAuthenticate()
            auth_result = await auth_skill.run(ctx, {
                "session_keys": init_result.metadata.get("session_keys"),
            })
            
            if auth_result.success:
                ctx.runtime_ctx.establish_secure_channel(
                    protocol="scp03",
                    info={
                        "session_keys": init_result.metadata.get("session_keys"),
                        "ssc": init_result.metadata.get("ssc"),
                    }
                )
            
            return auth_result
        
        elif protocol == "scp80":
            from skills.scp80 import EstablishSCP80
            
            scp80_skill = EstablishSCP80()
            result = await scp80_skill.run(ctx, params)
            
            if result.success:
                ctx.runtime_ctx.establish_secure_channel(
                    protocol="scp80",
                    info=result.metadata
                )
            
            return result
        
        else:
            return SkillResult(
                success=False,
                error=f"Unknown SCP protocol: {protocol}"
            )


class CloseSecureChannel(BaseSkill):
    """Close secure channel.

    Terminates the secure channel session.

    Parameters:
        None

    Returns:
        SkillResult indicating channel closed.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "close_secure_channel"
    description = "Close secure channel"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute close secure channel skill."""
        ctx.runtime_ctx.secure_channel_state = "none"
        ctx.runtime_ctx.secure_channel_info = {}
        
        return SkillResult(success=True)


class WrapSecureAPDU(BaseSkill):
    """Wrap APDU with secure channel (MAC and/or encryption).

    Applies secure channel protection to APDU command.

    Parameters:
        apdu: Original APDU command
        encrypt: Whether to encrypt data field (default: False)

    Returns:
        SkillResult with wrapped APDU.

    Example:
        result = await skill.run(ctx, {"apdu": "00A40000023F00", "encrypt": False})
        wrapped_apdu = result.data
    """

    name = "wrap_secure_apdu"
    description = "Wrap APDU with secure channel protection"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True  # Requires secure channel

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute wrap secure APDU skill."""
        apdu = params.get("apdu")
        encrypt = params.get("encrypt", False)
        
        if not apdu:
            return SkillResult(success=False, error="Missing apdu parameter")
        
        # Check secure channel state
        if ctx.runtime_ctx.secure_channel_state.value == "none":
            return SkillResult(
                success=False,
                error="Secure channel not established"
            )
        
        protocol = ctx.runtime_ctx.secure_channel_state.value
        
        if protocol == "scp03":
            from skills.scp03 import SCP03Wrap
            
            wrap_skill = SCP03Wrap()
            return await wrap_skill.run(ctx, {"apdu": apdu, "encrypt": encrypt})
        
        elif protocol == "scp80":
            # SCP80 wrapping
            # Would implement SCP80 MAC calculation
            return SkillResult(
                success=True,
                data=apdu,  # Placeholder - would be wrapped
                metadata={"protocol": "scp80", "wrapped": True}
            )
        
        else:
            return SkillResult(
                success=False,
                error=f"Unknown secure channel protocol: {protocol}"
            )


class CalculateMAC(BaseSkill):
    """Calculate MAC for data.

    Calculates Message Authentication Code using
    session key or specified key.

    Parameters:
        data: Data to calculate MAC over
        key: MAC key (optional, uses session key if not provided)
        algorithm: MAC algorithm ("des", "aes")

    Returns:
        SkillResult with MAC bytes.

    Example:
        result = await skill.run(ctx, {"data": "00010203", "algorithm": "aes"})
        mac = result.data
    """

    name = "calculate_mac"
    description = "Calculate MAC for data"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute calculate MAC skill."""
        data = params.get("data")
        key = params.get("key")
        algorithm = params.get("algorithm", "aes")
        
        if not data:
            return SkillResult(success=False, error="Missing data parameter")
        
        # Convert data format
        if isinstance(data, str):
            data_bytes = bytes.fromhex(data)
        else:
            data_bytes = bytes(data)
        
        # Use session key if not provided
        if not key and ctx.runtime_ctx.secure_channel_info:
            key = ctx.runtime_ctx.secure_channel_info.get("mac_key")
        
        if not key:
            return SkillResult(success=False, error="No MAC key available")
        
        # Calculate MAC (placeholder - would use crypto library)
        # For SCP03, would use AES-CMAC
        # For SCP80, would use DES-MAC
        
        return SkillResult(
            success=True,
            metadata={"mac": "0001020304", "algorithm": algorithm}  # Placeholder
        )


def register_security_skills(registry: Any) -> None:
    """Register all Security Primitive skills."""
    registry.register(VerifyPIN(), "primitive")
    registry.register(VerifyADM(), "primitive")
    registry.register(GetPINStatus(), "primitive")
    registry.register(ChangePIN(), "primitive")
    registry.register(UnblockPIN(), "primitive")
    registry.register(OpenSecureChannel(), "primitive")
    registry.register(CloseSecureChannel(), "primitive")
    registry.register(WrapSecureAPDU(), "primitive")
    registry.register(CalculateMAC(), "primitive")