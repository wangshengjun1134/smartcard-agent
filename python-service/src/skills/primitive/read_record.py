"""Read Record Skill - read a record from a linear/cyclic file.

This skill reads a record from the currently selected linear fixed
or cyclic file.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.builders.read_builder import build_read_record


class ReadRecordSkill(BaseSkill):
    """Skill for reading a record from a linear/cyclic file.

    Parameters:
        record_number: Record number to read (default: 1)
        length: Number of bytes to read (default: 0 = all)

    Requires:
        - A linear fixed or cyclic file must be selected

    Example:
        await skill.run(ctx, {"record_number": 1})
    """

    name = "read_record"
    description = "Read a record from a linear/cyclic file"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute READ RECORD skill.

        Args:
            ctx: Skill execution context
            params: {"record_number": 1, "length": 0}

        Returns:
            SkillResult with record data.
        """
        record_number = params.get("record_number", 1)
        length = params.get("length", 0)

        # Validate parameters
        if not isinstance(record_number, int) or record_number < 1:
            return SkillResult(success=False, error=f"Invalid record_number: {record_number}")

        if not isinstance(length, int) or length < 0:
            return SkillResult(success=False, error=f"Invalid length: {length}")

        try:
            # Build READ RECORD APDU
            apdu = build_read_record(record_number, length=length)
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