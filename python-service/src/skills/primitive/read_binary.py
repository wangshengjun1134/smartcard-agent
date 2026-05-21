"""Read Binary Skill - read data from a transparent file.

This skill reads bytes from the currently selected transparent file.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.builders.read_builder import build_read_binary


class ReadBinarySkill(BaseSkill):
    """Skill for reading binary data from a transparent file.

    Parameters:
        offset: Byte offset to read from (default: 0)
        length: Number of bytes to read (default: 0 = all available)

    Requires:
        - A transparent file must be selected

    Example:
        await skill.run(ctx, {"offset": 0, "length": 9})  # Read IMSI
    """

    name = "read_binary"
    description = "Read binary data from a transparent file"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute READ BINARY skill.

        Args:
            ctx: Skill execution context
            params: {"offset": 0, "length": 9}

        Returns:
            SkillResult with read data.
        """
        offset = params.get("offset", 0)
        length = params.get("length", 0)

        # Validate parameters
        if not isinstance(offset, int) or offset < 0:
            return SkillResult(success=False, error=f"Invalid offset: {offset}")

        if not isinstance(length, int) or length < 0:
            return SkillResult(success=False, error=f"Invalid length: {length}")

        try:
            # Build READ BINARY APDU
            apdu = build_read_binary(offset, length)
            apdu_bytes = bytes(apdu)

            # Send APDU
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            # Record execution
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params=params,
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

    def can_execute(self, ctx: Any) -> tuple[bool, str]:
        """Check if a file is selected.

        Args:
            ctx: Runtime context

        Returns:
            Tuple of (can_execute, reason).
        """
        if not ctx.connected:
            return False, "Not connected to card"

        if not ctx.runtime_ctx.selected_path:
            return False, "No file selected"

        return True, ""