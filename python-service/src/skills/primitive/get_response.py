"""Get Response Skill - retrieve data using GET RESPONSE.

This skill retrieves additional data from the card when SW indicates
more data is available (61XX).
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.builders.auth_builder import build_get_response


class GetResponseSkill(BaseSkill):
    """Skill for retrieving data with GET RESPONSE.

    Parameters:
        length: Number of bytes to retrieve (required)

    Used when previous command returns SW 61XX,
    indicating XX bytes are available.

    Example:
        await skill.run(ctx, {"length": 15})  # Get 15 bytes
    """

    name = "get_response"
    description = "Retrieve data using GET RESPONSE command"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GET RESPONSE skill.

        Args:
            ctx: Skill execution context
            params: {"length": 15}

        Returns:
            SkillResult with retrieved data.
        """
        length = params.get("length", 0)

        if not isinstance(length, int) or length < 1:
            return SkillResult(success=False, error=f"Invalid length: {length}")

        try:
            # Build GET RESPONSE APDU
            apdu = build_get_response(length)
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