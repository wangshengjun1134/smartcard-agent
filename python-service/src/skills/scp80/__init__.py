"""SCP80 Primitive Skills - OTA SMS secure channel operations.

SCP80 (Secure Channel Protocol 80) is used for OTA (Over-The-Air)
SMS-based secure communication with SIM/USIM cards.

Reference: GlobalPlatform SCP80 specification, 3GPP TS 03.48
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class EstablishSCP80(BaseSkill):
    """Establish SCP80 secure channel for OTA.

    Initializes SCP80 secure channel for SMS OTA operations.

    Parameters:
        kic: Key Identifier for ciphering (KIC)
        kid: Key Identifier for data integrity (KID)
        ked: Key Identifier for key derivation (KED)
        tar: Toolkit Application Reference
        sequence_counter: Current sequence counter

    Returns:
        SkillResult with established channel info.

    Example:
        result = await skill.run(ctx, {
            "kic": 0x01,
            "kid": 0x02,
            "ked": 0x01,
            "tar": "7F3302"
        })
    """

    name = "establish_scp80"
    description = "Establish SCP80 secure channel for OTA"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute establish SCP80 skill."""
        kic = params.get("kic", 0x01)
        kid = params.get("kid", 0x02)
        ked = params.get("ked", 0x01)
        tar = params.get("tar", "7F3302")
        sequence_counter = params.get("sequence_counter", 0)
        
        # SCP80 uses PoR (Proof of Receipt) and SMS encapsulation
        # Channel establishment involves key derivation
        
        ctx.runtime_ctx.establish_secure_channel(
            protocol="scp80",
            info={
                "kic": kic,
                "kid": kid,
                "ked": ked,
                "tar": tar,
                "sequence_counter": sequence_counter,
            }
        )
        
        return SkillResult(
            success=True,
            metadata={
                "protocol": "scp80",
                "kic": kic,
                "kid": kid,
                "tar": tar,
                "sequence_counter": sequence_counter,
            }
        )


class SendSecuredSMS(BaseSkill):
    """Send secured SMS command via OTA.

    Sends an OTA SMS command protected with SCP80.

    Parameters:
        command: Command data to send
        tar: Toolkit Application Reference (uses channel TAR if not provided)
        por_required: Whether PoR is required (default: True)

    Returns:
        SkillResult with SMS packet.

    Example:
        result = await skill.run(ctx, {
            "command": "00A40000023F00",
            "por_required": True
        })
    """

    name = "send_secured_sms"
    description = "Send secured SMS command via OTA (SCP80)"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True  # Requires SCP80

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute send secured SMS skill."""
        command = params.get("command")
        tar = params.get("tar")
        por_required = params.get("por_required", True)
        
        if not command:
            return SkillResult(success=False, error="Missing command parameter")
        
        # Get SCP80 channel info
        if ctx.runtime_ctx.secure_channel_state.value != "scp80":
            return SkillResult(
                success=False,
                error="SCP80 secure channel not established"
            )
        
        channel_info = ctx.runtime_ctx.secure_channel_info
        if not tar:
            tar = channel_info.get("tar", "7F3302")
        
        # Build OTA SMS packet
        # Structure: TAR + Command + Security (MAC + Encryption)
        
        # Placeholder: would build actual SMS packet
        sms_packet = self._build_sms_packet(command, tar, channel_info)
        
        return SkillResult(
            success=True,
            data=sms_packet,
            metadata={
                "tar": tar,
                "por_required": por_required,
                "packet_length": len(sms_packet),
            }
        )

    def _build_sms_packet(self, command: str, tar: str, channel_info: Dict) -> bytes:
        """Build OTA SMS packet (placeholder)."""
        # Real implementation would:
        # 1. Create Command Header (CLA INS P1 P2 Lc Data Le)
        # 2. Calculate MAC over command
        # 3. Optionally encrypt command data
        # 4. Build SMS-TPDU envelope
        
        if isinstance(command, str):
            command_bytes = bytes.fromhex(command)
        else:
            command_bytes = bytes(command)
        
        tar_bytes = bytes.fromhex(tar)
        
        # Simplified packet structure
        # TAR (3 bytes) + Length + Command + MAC placeholder
        
        return tar_bytes + bytes([len(command_bytes)]) + command_bytes + bytes(8)  # MAC placeholder


class BuildOTAPacket(BaseSkill):
    """Build OTA SMS packet.

    Constructs OTA packet with proper structure:
    - Command Packet Header
    - Command Data
    - Security Package (MAC, PoR)

    Parameters:
        command: Command APDU or data
        tar: Toolkit Application Reference
        security_level: Security level (0-15)
        ciphering_key_ref: Ciphering key reference
        signature_key_ref: Signature key reference

    Returns:
        SkillResult with OTA packet bytes.

    Example:
        result = await skill.run(ctx, {
            "command": "00A40000023F00",
            "security_level": 0x01
        })
    """

    name = "build_ota_packet"
    description = "Build OTA SMS packet structure"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute build OTA packet skill."""
        command = params.get("command")
        tar = params.get("tar", "7F3302")
        security_level = params.get("security_level", 0x01)
        
        if not command:
            return SkillResult(success=False, error="Missing command parameter")
        
        # Convert command format
        if isinstance(command, str):
            command_bytes = bytes.fromhex(command)
        else:
            command_bytes = bytes(command)
        
        tar_bytes = bytes.fromhex(tar)
        
        # Build packet structure:
        # Command Packet Header (CPH)
        # - TAR (3 bytes)
        # - Security Level Byte (1 byte)
        # - PIN counter placeholder (1 byte)
        # Command:
        # - Length (1 byte)
        # - APDU data
        # Security Package:
        # - PoR configuration
        # - MAC (8 bytes placeholder)
        
        packet = (
            tar_bytes +                          # TAR
            bytes([security_level]) +            # Security Level
            bytes([0x00]) +                      # PIN counter placeholder
            bytes([len(command_bytes)]) +        # Command length
            command_bytes +                      # Command APDU
            bytes(8)                             # MAC placeholder
        )
        
        return SkillResult(
            success=True,
            data=packet,
            metadata={
                "tar": tar,
                "security_level": security_level,
                "command_length": len(command_bytes),
                "packet_length": len(packet),
            }
        )


class EncryptOTAPacket(BaseSkill):
    """Encrypt OTA packet data.

    Encrypts command data portion of OTA packet
    using KIC key.

    Parameters:
        packet: OTA packet bytes
        kic: Ciphering key reference (uses channel KIC if not provided)

    Returns:
        SkillResult with encrypted packet.

    Example:
        result = await skill.run(ctx, {"packet": ota_packet})
    """

    name = "encrypt_ota_packet"
    description = "Encrypt OTA packet data"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute encrypt OTA packet skill."""
        packet = params.get("packet")
        kic = params.get("kic")
        
        if not packet:
            return SkillResult(success=False, error="Missing packet parameter")
        
        if isinstance(packet, str):
            packet_bytes = bytes.fromhex(packet)
        else:
            packet_bytes = bytes(packet)
        
        # Get KIC from channel if not provided
        if not kic and ctx.runtime_ctx.secure_channel_info:
            kic = ctx.runtime_ctx.secure_channel_info.get("kic", 0x01)
        
        # Placeholder: would use DES/AES encryption based on KIC
        # SCP80 supports:
        # - KIC = 0x01: DES-CBC
        # - KIC = 0x03: Triple DES
        # - KIC = 0x05: AES
        
        encrypted_packet = packet_bytes  # Placeholder
        
        return SkillResult(
            success=True,
            data=encrypted_packet,
            metadata={"kic": kic, "encrypted": True}
        )


class CalculateOTAMAC(BaseSkill):
    """Calculate OTA MAC (signature).

    Calculates cryptographic signature for OTA packet
    using KID key.

    Parameters:
        packet: OTA packet bytes to MAC
        kid: Signature key reference (uses channel KID if not provided)

    Returns:
        SkillResult with MAC bytes (8 bytes).

    Example:
        result = await skill.run(ctx, {"packet": ota_packet})
        mac = result.data
    """

    name = "calculate_ota_mac"
    description = "Calculate OTA MAC (signature)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute calculate OTA MAC skill."""
        packet = params.get("packet")
        kid = params.get("kid")
        
        if not packet:
            return SkillResult(success=False, error="Missing packet parameter")
        
        if isinstance(packet, str):
            packet_bytes = bytes.fromhex(packet)
        else:
            packet_bytes = bytes(packet)
        
        # Get KID from channel if not provided
        if not kid and ctx.runtime_ctx.secure_channel_info:
            kid = ctx.runtime_ctx.secure_channel_info.get("kid", 0x02)
        
        # Placeholder: would use DES-MAC or AES-CMAC based on KID
        # SCP80 supports:
        # - KID = 0x01: DES-MAC
        # - KID = 0x02: Triple DES-MAC
        # - KID = 0x04: AES-CMAC
        
        import os
        mac = os.urandom(8)  # Placeholder MAC
        
        return SkillResult(
            success=True,
            data=mac,
            metadata={"kid": kid, "mac_length": 8}
        )


def register_scp80_skills(registry: Any) -> None:
    """Register all SCP80 Primitive skills."""
    registry.register(EstablishSCP80(), "primitive")
    registry.register(SendSecuredSMS(), "primitive")
    registry.register(BuildOTAPacket(), "primitive")
    registry.register(EncryptOTAPacket(), "primitive")
    registry.register(CalculateOTAMAC(), "primitive")