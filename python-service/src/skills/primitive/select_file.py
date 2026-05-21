"""Select File Skill - select a file by FID.

This skill selects a file on the smart card using its File ID.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.builders.select_builder import build_select_file


class SelectFileSkill(BaseSkill):
    """Skill for selecting a file by File ID.

    Parameters:
        fid: File ID as 4-character hex string (e.g., "3F00", "6F07")

    Updates runtime context:
        - selected_path: Path is updated with the selected FID

    Example:
        await skill.run(ctx, {"fid": "3F00"})  # Select MF
        await skill.run(ctx, {"fid": "7F20"})  # Select DF_GSM
    """

    name = "select_file"
    description = "Select a file by File ID (FID)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute SELECT FILE skill.

        Args:
            ctx: Skill execution context with PCSC client
            params: {"fid": "3F00"}

        Returns:
            SkillResult with selection status.
        """
        fid = params.get("fid")

        if not fid:
            return SkillResult(success=False, error="Missing required parameter: fid")

        # Validate FID format
        if not isinstance(fid, str) or len(fid) != 4:
            return SkillResult(success=False, error=f"Invalid FID format: {fid}")

        try:
            # Build SELECT APDU
            apdu = build_select_file(fid)
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
                # Update runtime context
                ctx.runtime_ctx.select_file(fid)

                return SkillResult(
                    success=True,
                    data=response.data,
                    sw=response.sw,
                    metadata={"fid": fid, "path": ctx.runtime_ctx.get_current_path()}
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

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate FID parameter.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (valid, error).
        """
        fid = params.get("fid")
        if not fid:
            return False, "Missing required parameter: fid"

        import re
        if not re.match(r"^[0-9A-Fa-f]{4}$", fid):
            return False, f"Invalid FID format: {fid} (must be 4 hex characters)"

        return True, ""