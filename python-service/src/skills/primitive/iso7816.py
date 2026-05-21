"""ISO7816 Core Primitive Skills - Core APDU operations.

This module provides all ISO7816-4 defined APDU commands as skills,
organized according to the specification categories:
- File management commands (SELECT, READ, UPDATE, etc.)
- Security commands (VERIFY, AUTHENTICATE, etc.)
- Transmission commands (GET_RESPONSE, ENVELOPE, etc.)
- Card management commands (STATUS, MANAGE_CHANNEL, etc.)

Reference: ISO/IEC 7816-4, ETSI TS 102 221
"""

from typing import Dict, Any, Optional
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.constants.instructions import *
from apdu.constants.file_ids import FID_MF


class SendAPDUSkill(BaseSkill):
    """Send raw APDU command to card.

    Allows sending any APDU command without specific skill support.
    Useful for testing, debugging, or unsupported commands.

    Parameters:
        apdu: APDU bytes (list of integers or hex string)
        check_sw: Whether to raise error on non-success SW (default: True)
        expected_sw: Expected SW to match (default: "9000")

    Returns:
        SkillResult with response data and SW.

    Example:
        result = await skill.run(ctx, {"apdu": "00A40000023F00"})
        data = result.data
        sw = result.sw
    """

    name = "send_apdu"
    description = "Send raw APDU command to card"
    dangerous = True  # Can send any command including destructive ones
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute send APDU skill."""
        apdu = params.get("apdu")
        check_sw = params.get("check_sw", True)
        expected_sw = params.get("expected_sw", "9000")

        if not apdu:
            return SkillResult(success=False, error="Missing required parameter: apdu")

        try:
            # Convert APDU format
            if isinstance(apdu, str):
                apdu_list = list(bytes.fromhex(apdu))
                apdu_bytes = bytes.fromhex(apdu)
            else:
                apdu_list = apdu
                apdu_bytes = bytes(apdu)

            # Send APDU
            response = ctx.pcsc.send_apdu(apdu_list, check_sw=False)

            # Record execution
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"apdu": apdu_bytes.hex().upper()},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            # Check expected SW if specified
            if expected_sw and response.sw != expected_sw:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=f"Unexpected SW: {response.sw} ({decode_sw(response.sw)})",
                    data=response.data,
                )

            return SkillResult(
                success=response.success,
                data=response.data,
                sw=response.sw,
                metadata={"apdu": apdu_bytes.hex().upper()}
            )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class SelectSkill(BaseSkill):
    """SELECT command (ISO7816-4).

    Selects a file by FID, AID, or path.
    Returns FCI/FCP template with file info.

    Parameters:
        fid: File ID (4 hex chars, e.g., "3F00")
        aid: Application ID (hex string, e.g., "A0000000871001")
        select_mode: P1 byte (0x00=by FID, 0x04=by AID)
        select_type: P2 byte (0x04=FCI, 0x00=no data)

    Returns:
        SkillResult with FCI/FCP data and SW.

    Example:
        # Select by FID
        result = await skill.run(ctx, {"fid": "3F00"})
        
        # Select by AID
        result = await skill.run(ctx, {"aid": "A0000000871001"})
    """

    name = "select"
    description = "SELECT file by FID or AID (ISO7816-4)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SELECT skill."""
        from apdu.builders.select_builder import build_select_file, build_select_by_aid

        fid = params.get("fid")
        aid = params.get("aid")
        select_mode = params.get("select_mode", 0x00)
        select_type = params.get("select_type", 0x04)

        try:
            if fid:
                apdu = build_select_file(fid)
            elif aid:
                apdu = build_select_by_aid(aid)
            else:
                return SkillResult(success=False, error="Missing fid or aid parameter")

            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            # Record execution
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"fid": fid, "aid": aid},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                # Update runtime context
                if fid:
                    ctx.runtime_ctx.select_file(fid)
                elif aid:
                    ctx.runtime_ctx.select_application(aid)

                # Parse FCI/FCP
                from apdu.parsers.fcp_parser import parse_fcp
                fcp_info = parse_fcp(response.data) if response.data else {}

                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={
                        "fid": fid,
                        "aid": aid,
                        "fcp": fcp_info,
                        "path": ctx.runtime_ctx.get_current_path(),
                    }
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class ReadBinarySkill(BaseSkill):
    """READ BINARY command (ISO7816-4).

    Reads bytes from a transparent file.

    Parameters:
        offset: Byte offset (default: 0)
        length: Bytes to read (0 = read all available)

    Returns:
        SkillResult with read data.

    Example:
        result = await skill.run(ctx, {"offset": 0, "length": 9})
    """

    name = "read_binary"
    description = "READ BINARY from transparent file (ISO7816-4)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute READ BINARY skill."""
        from apdu.builders.read_builder import build_read_binary

        offset = params.get("offset", 0)
        length = params.get("length", 0)

        try:
            apdu = build_read_binary(offset, length)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"offset": offset, "length": length},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"offset": offset, "length": len(response.data)}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class ReadRecordSkill(BaseSkill):
    """READ RECORD command (ISO7816-4).

    Reads a record from a linear fixed or cyclic file.

    Parameters:
        record_number: Record number (default: 1)
        read_mode: P1 mode (absolute, next, previous)
        length: Bytes to read (0 = read all)

    Returns:
        SkillResult with record data.

    Example:
        result = await skill.run(ctx, {"record_number": 1, "length": 28})
    """

    name = "read_record"
    description = "READ RECORD from linear/cyclic file (ISO7816-4)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute READ RECORD skill."""
        from apdu.builders.read_builder import build_read_record

        record_number = params.get("record_number", 1)
        length = params.get("length", 0)

        try:
            apdu = build_read_record(record_number, length=length)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"record_number": record_number},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"record_number": record_number, "length": len(response.data)}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class GetResponseSkill(BaseSkill):
    """GET RESPONSE command (ISO7816-4).

    Retrieves additional data after 61XX SW.

    Parameters:
        length: Bytes to retrieve

    Returns:
        SkillResult with response data.

    Example:
        # After SELECT returns 6115
        result = await skill.run(ctx, {"length": 15})
    """

    name = "get_response"
    description = "GET RESPONSE to retrieve additional data (ISO7816-4)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GET RESPONSE skill."""
        from apdu.builders.auth_builder import build_get_response

        length = params.get("length", 0)

        if length <= 0:
            return SkillResult(success=False, error="Invalid length parameter")

        try:
            apdu = build_get_response(length)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"length": length},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"length": len(response.data)}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class VerifySkill(BaseSkill):
    """VERIFY PIN command (ISO7816-4, ETSI TS 102 221).

    Verifies a PIN (CHV) on the card.

    Parameters:
        pin_ref: PIN reference (1=PIN1, 2=PIN2, 5=PUK1, 0A=ADM1)
        pin: PIN value (4-8 digits)

    Returns:
        SkillResult with verification status.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1, "pin": "1234"})
    """

    name = "verify"
    description = "VERIFY PIN on smart card (ISO7816-4)"
    dangerous = False
    requires_pin = False  # This skill verifies PIN, doesn't require it
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute VERIFY skill."""
        from apdu.builders.auth_builder import build_verify_pin
        from apdu.parsers.sw_parser import get_retry_count

        pin_ref = params.get("pin_ref", 1)
        pin = params.get("pin", "")

        try:
            apdu = build_verify_pin(pin_ref, pin)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            # Don't log actual PIN
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"pin_ref": pin_ref},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                ctx.runtime_ctx.verify_pin(pin_ref)
                return SkillResult(
                    success=True,
                    sw=response.sw,
                    metadata={"pin_ref": pin_ref, "verified": True}
                )
            else:
                retry_count = get_retry_count(response.sw)
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                    metadata={"pin_ref": pin_ref, "retry_count": retry_count}
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class ChangePINSkill(BaseSkill):
    """CHANGE PIN command (ISO7816-4).

    Changes a PIN value.

    Parameters:
        pin_ref: PIN reference
        old_pin: Current PIN
        new_pin: New PIN value

    Returns:
        SkillResult indicating success.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1, "old_pin": "1234", "new_pin": "5678"})
    """

    name = "change_pin"
    description = "CHANGE PIN on smart card (ISO7816-4)"
    dangerous = True
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute CHANGE PIN skill."""
        from apdu.builders.auth_builder import build_change_pin

        pin_ref = params.get("pin_ref", 1)
        old_pin = params.get("old_pin", "")
        new_pin = params.get("new_pin", "")

        try:
            apdu = build_change_pin(pin_ref, old_pin, new_pin)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"pin_ref": pin_ref},  # Don't log PINs
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    sw=response.sw,
                    metadata={"pin_ref": pin_ref, "changed": True}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class UnblockPINSkill(BaseSkill):
    """UNBLOCK PIN command (ISO7816-4).

    Unblocks a blocked PIN using PUK.

    Parameters:
        pin_ref: PIN reference to unblock
        puk: PUK value
        new_pin: New PIN value to set

    Returns:
        SkillResult indicating success.

    Example:
        result = await skill.run(ctx, {"pin_ref": 1, "puk": "12345678", "new_pin": "1234"})
    """

    name = "unblock_pin"
    description = "UNBLOCK PIN using PUK (ISO7816-4)"
    dangerous = True
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute UNBLOCK PIN skill."""
        from apdu.builders.auth_builder import build_unblock_pin

        pin_ref = params.get("pin_ref", 1)
        puk = params.get("puk", "")
        new_pin = params.get("new_pin", "")

        try:
            apdu = build_unblock_pin(pin_ref, puk, new_pin)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"pin_ref": pin_ref},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    sw=response.sw,
                    metadata={"pin_ref": pin_ref, "unblocked": True}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class GetChallengeSkill(BaseSkill):
    """GET CHALLENGE command (ISO7816-4).

    Requests random challenge from card for authentication.

    Parameters:
        length: Challenge length (default: 8)

    Returns:
        SkillResult with challenge bytes.

    Example:
        result = await skill.run(ctx, {"length": 8})
        challenge = result.data  # 8 random bytes
    """

    name = "get_challenge"
    description = "GET CHALLENGE from smart card (ISO7816-4)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GET CHALLENGE skill."""
        from apdu.builders.auth_builder import build_get_challenge

        length = params.get("length", 8)

        try:
            apdu = build_get_challenge(length)
            apdu_bytes = bytes(apdu)
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"length": length},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"length": len(response.data)}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class InternalAuthenticateSkill(BaseSkill):
    """INTERNAL AUTHENTICATE command (ISO7816-4, GSM).

    Authenticates card to terminal using challenge.

    Parameters:
        challenge: Challenge bytes (for GSM, 16 bytes RAND)

    Returns:
        SkillResult with authentication response (SRES, Kc for GSM).

    Example:
        # GSM authentication
        result = await skill.run(ctx, {"challenge": rand_bytes})
        sres_kc = result.data  # 4+8 bytes
    """

    name = "internal_authenticate"
    description = "INTERNAL AUTHENTICATE (ISO7816-4, GSM)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute INTERNAL AUTHENTICATE skill."""
        challenge = params.get("challenge")

        if not challenge:
            return SkillResult(success=False, error="Missing challenge parameter")

        try:
            # Build INTERNAL AUTHENTICATE APDU
            cla = params.get("cla", 0x00)
            apdu = bytes([cla, INS_INTERNAL_AUTHENTICATE, 0x00, 0x00, len(challenge)]) + challenge
            apdu_bytes = apdu
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"challenge_length": len(challenge)},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"challenge_length": len(challenge)}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class ManageChannelSkill(BaseSkill):
    """MANAGE CHANNEL command (ISO7816-4).

    Opens, closes, or manages logical channels.

    Parameters:
        action: "open", "close", or "manage"
        channel_number: Channel number for close/manage

    Returns:
        SkillResult with channel info.

    Example:
        # Open new logical channel
        result = await skill.run(ctx, {"action": "open"})
        channel = result.metadata["channel_number"]
    """

    name = "manage_channel"
    description = "MANAGE CHANNEL for logical channel operations (ISO7816-4)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute MANAGE CHANNEL skill."""
        action = params.get("action", "open")
        channel_number = params.get("channel_number", 0)

        try:
            # Build MANAGE CHANNEL APDU
            # P1: 0x00=open, 0x80=close, others for manage
            if action == "open":
                p1 = 0x00
            elif action == "close":
                p1 = 0x80
            else:
                p1 = channel_number

            apdu = bytes([CLA_ISO7816, INS_MANAGE_CHANNEL, p1, 0x00])
            apdu_bytes = apdu
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"action": action},
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                # For open, response data contains channel number
                new_channel = response.data[0] if response.data else channel_number
                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"action": action, "channel_number": new_channel}
                )
            else:
                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


# Additional ISO7816 core skills would follow similar patterns...
# (update_binary, update_record, search_record, envelope, etc.)


def register_iso7816_skills(registry: Any) -> None:
    """Register all ISO7816 Core Primitive skills."""
    registry.register(SendAPDUSkill(), "primitive")
    registry.register(SelectSkill(), "primitive")
    registry.register(ReadBinarySkill(), "primitive")
    registry.register(ReadRecordSkill(), "primitive")
    registry.register(GetResponseSkill(), "primitive")
    registry.register(VerifySkill(), "primitive")
    registry.register(ChangePINSkill(), "primitive")
    registry.register(UnblockPINSkill(), "primitive")
    registry.register(GetChallengeSkill(), "primitive")
    registry.register(InternalAuthenticateSkill(), "primitive")
    registry.register(ManageChannelSkill(), "primitive")