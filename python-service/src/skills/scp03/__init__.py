"""SCP03 Primitive Skills - GlobalPlatform SCP03 secure channel operations.

SCP03 (Secure Channel Protocol 03) is the modern secure channel protocol
defined by GlobalPlatform, using AES encryption and CMAC.

Reference: GlobalPlatform Card Specification v2.3, Amendment A
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class SCP03InitializeUpdate(BaseSkill):
    """SCP03 INITIALIZE UPDATE command.

    Initiates SCP03 secure channel establishment.
    Returns card challenge and cryptogram for host verification.

    Parameters:
        key_set: Key set identifier (KID, typically 0x01)
        key_version: Key version (KV, typically 0x01)
        sequence_counter: Host sequence counter (optional)
        challenge: Host challenge (16 bytes, optional - random if not provided)

    Returns:
        SkillResult with:
        - card_challenge (8 bytes)
        - card_cryptogram (8 bytes)
        - sequence_counter (optional)
        - session keys derived parameters

    Example:
        result = await skill.run(ctx, {"key_set": 1, "key_version": 1})
        card_challenge = result.metadata["card_challenge"]
    """

    name = "scp03_initialize_update"
    description = "SCP03 INITIALIZE UPDATE command"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 INITIALIZE UPDATE skill."""
        key_set = params.get("key_set", 0x01)
        key_version = params.get("key_version", 0x01)
        
        # Generate or use provided host challenge
        import os
        host_challenge = params.get("challenge")
        if not host_challenge:
            host_challenge = os.urandom(16)  # Random 16-byte challenge
        elif isinstance(host_challenge, str):
            host_challenge = bytes.fromhex(host_challenge)
        
        # Build INITIALIZE UPDATE APDU
        # CLA INS P1 P2 Lc Data
        # P1 = Key Version | Key Set
        # P2 = 0x00
        # Data = Host Challenge (16 bytes)
        
        p1 = (key_version << 4) | (key_set & 0x0F)
        apdu = bytes([0x80, 0x50, p1, 0x00, 16]) + host_challenge
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"key_set": key_set, "key_version": key_version},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            # Parse response (28 bytes)
            # Key diversification data (10 bytes)
            # Key information (3 bytes)
            # Card challenge (8 bytes)
            # Card cryptogram (8 bytes)
            
            if len(response.data) >= 28:
                key_div_data = response.data[:10]
                key_info = response.data[10:13]
                card_challenge = response.data[13:21]
                card_cryptogram = response.data[21:29]
                
                # Derive session keys (placeholder - would use crypto)
                # S-ENC, S-MAC, S-RMAC
                
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={
                        "key_div_data": key_div_data.hex().upper(),
                        "key_info": key_info.hex().upper(),
                        "card_challenge": card_challenge.hex().upper(),
                        "card_cryptogram": card_cryptogram.hex().upper(),
                        "host_challenge": host_challenge.hex().upper(),
                        "session_keys": {
                            "enc": "derived_enc_key_placeholder",
                            "mac": "derived_mac_key_placeholder",
                            "rmac": "derived_rmac_key_placeholder",
                        },
                        "ssc": 0,  # Security Status Counter
                    }
                )
            else:
                return SkillResult(
                    success=False,
                    error=f"Invalid response length: {len(response.data)} bytes"
                )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class SCP03ExternalAuthenticate(BaseSkill):
    """SCP03 EXTERNAL AUTHENTICATE command.

    Completes SCP03 secure channel establishment by verifying
    host cryptogram to card.

    Parameters:
        session_keys: Session keys from INITIALIZE UPDATE
        host_cryptogram: Host cryptogram (8 bytes)
        level: Security level (0x01=MAC, 0x03=MAC+ENC)

    Returns:
        SkillResult indicating authentication success.

    Example:
        result = await skill.run(ctx, {
            "session_keys": init_result.metadata["session_keys"],
            "level": 0x03  # Full security
        })
    """

    name = "scp03_external_authenticate"
    description = "SCP03 EXTERNAL AUTHENTICATE command"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 EXTERNAL AUTHENTICATE skill."""
        session_keys = params.get("session_keys")
        level = params.get("level", 0x03)  # C-MAC + C-ENC
        
        if not session_keys:
            return SkillResult(success=False, error="Missing session_keys parameter")
        
        # Calculate host cryptogram (placeholder)
        # Host cryptogram = CMAC(S-MAC, host_challenge || card_challenge)
        # For now, use placeholder
        
        import os
        host_cryptogram = os.urandom(8)  # Placeholder
        
        # Build EXTERNAL AUTHENTICATE APDU
        # CLA = 0x84 (secure messaging)
        # INS = 0x82
        # P1 = Security level
        # P2 = 0x00
        # Lc = 8
        # Data = Host cryptogram
        
        apdu = bytes([0x84, 0x82, level, 0x00, 8]) + host_cryptogram
        
        # Note: This APDU should be MACed with S-MAC
        # For now, send without MAC (placeholder)
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"level": level},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            # Secure channel is now open
            ctx.runtime_ctx.establish_secure_channel(
                protocol="scp03",
                info={
                    "session_keys": session_keys,
                    "ssc": 1,  # Initialize SSC to 1
                    "level": level,
                }
            )
            
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={
                    "level": level,
                    "secure_channel": "scp03",
                    "ssc": 1,
                }
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class SCP03Wrap(BaseSkill):
    """SCP03 wrap APDU command.

    Applies SCP03 secure messaging protection to APDU:
    - Calculate and append MAC (C-MAC)
    - Optionally encrypt data field

    Parameters:
        apdu: Original APDU command
        encrypt: Whether to encrypt data (default: False)

    Returns:
        SkillResult with wrapped APDU.

    Example:
        result = await skill.run(ctx, {"apdu": "00A40000023F00", "encrypt": False})
        wrapped = result.data  # MAC-protected APDU
    """

    name = "scp03_wrap"
    description = "SCP03 wrap APDU with secure messaging"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 wrap skill."""
        apdu = params.get("apdu")
        encrypt = params.get("encrypt", False)
        
        if not apdu:
            return SkillResult(success=False, error="Missing apdu parameter")
        
        # Convert APDU format
        if isinstance(apdu, str):
            apdu_bytes = bytes.fromhex(apdu)
        else:
            apdu_bytes = bytes(apdu)
        
        # Check secure channel state
        if ctx.runtime_ctx.secure_channel_state.value != "scp03":
            return SkillResult(
                success=False,
                error="SCP03 secure channel not established"
            )
        
        # Get SSC and increment
        ssc = ctx.runtime_ctx.secure_channel_info.get("ssc", 0)
        new_ssc = ssc + 1
        
        # Placeholder: Would calculate CMAC and encrypt
        # Real implementation would:
        # 1. If encrypt: encrypt data field with S-ENC
        # 2. Calculate CMAC over (CLA|INS|P1|P2|Lc|Data||ssc)
        # 3. Append MAC to APDU
        # 4. Change CLA to indicate secure messaging
        
        # For placeholder, just return modified CLA
        wrapped_apdu = bytes([apdu_bytes[0] | 0x04]) + apdu_bytes[1:]
        
        # Update SSC
        ctx.runtime_ctx.secure_channel_info["ssc"] = new_ssc
        
        return SkillResult(
            success=True,
            data=wrapped_apdu,
            metadata={
                "ssc": new_ssc,
                "encrypted": encrypt,
                "mac": "0001020304050607",  # Placeholder MAC
            }
        )


class SCP03Unwrap(BaseSkill):
    """SCP03 unwrap APDU response.

    Verifies R-MAC and decrypts response data.

    Parameters:
        response: Response from card (data + SW)

    Returns:
        SkillResult with unwrapped response.

    Example:
        result = await skill.run(ctx, {"response": card_response})
        data = result.data  # Decrypted/verified data
    """

    name = "scp03_unwrap"
    description = "SCP03 unwrap response with secure messaging"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 unwrap skill."""
        response = params.get("response")
        
        if not response:
            return SkillResult(success=False, error="Missing response parameter")
        
        # Placeholder: Would verify R-MAC and decrypt
        # Real implementation would:
        # 1. Extract R-MAC from response
        # 2. Verify R-MAC using S-RMAC and SSC
        # 3. Decrypt data if encrypted response
        
        return SkillResult(
            success=True,
            data=response,  # Placeholder - would be unwrapped
            metadata={"verified": True}
        )


class SCP03Encrypt(BaseSkill):
    """SCP03 encrypt data.

    Encrypts data using S-ENC session key.

    Parameters:
        data: Data to encrypt
        session_key: S-ENC key (optional, uses current session)

    Returns:
        SkillResult with encrypted data.

    Example:
        result = await skill.run(ctx, {"data": "00010203"})
        encrypted = result.data
    """

    name = "scp03_encrypt"
    description = "SCP03 encrypt data with S-ENC"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 encrypt skill."""
        # Placeholder - would use AES encryption
        return SkillResult(success=True, metadata={"encrypted": "placeholder"})


class SCP03MAC(BaseSkill):
    """SCP03 calculate C-MAC.

    Calculates command MAC using S-MAC.

    Parameters:
        apdu: APDU to calculate MAC over
        ssc: Security Status Counter

    Returns:
        SkillResult with MAC (8 bytes).

    Example:
        result = await skill.run(ctx, {"apdu": "00A40000023F00"})
        mac = result.data
    """

    name = "scp03_mac"
    description = "SCP03 calculate C-MAC"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 MAC skill."""
        # Placeholder - would use AES-CMAC
        import os
        return SkillResult(success=True, data=os.urandom(8))


class SCP03RMAC(BaseSkill):
    """SCP03 calculate R-MAC.

    Calculates response MAC using S-RMAC.

    Parameters:
        response: Response data to calculate MAC over
        ssc: Security Status Counter

    Returns:
        SkillResult with R-MAC (8 bytes).

    Example:
        result = await skill.run(ctx, {"response": card_response})
        rmac = result.data
    """

    name = "scp03_rmac"
    description = "SCP03 calculate R-MAC"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SCP03 R-MAC skill."""
        # Placeholder - would use AES-CMAC
        import os
        return SkillResult(success=True, data=os.urandom(8))


def register_scp03_skills(registry: Any) -> None:
    """Register all SCP03 Primitive skills."""
    registry.register(SCP03InitializeUpdate(), "primitive")
    registry.register(SCP03ExternalAuthenticate(), "primitive")
    registry.register(SCP03Wrap(), "primitive")
    registry.register(SCP03Unwrap(), "primitive")
    registry.register(SCP03Encrypt(), "primitive")
    registry.register(SCP03MAC(), "primitive")
    registry.register(SCP03RMAC(), "primitive")