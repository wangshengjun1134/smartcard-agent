"""Read ICCID Skill - read the ICCID from a SIM/USIM card.

This composite skill reads the ICCID (Integrated Circuit Card ID)
from the card by selecting the EF_ICCID file.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.constants.file_ids import FID_MF, FID_EF_ICCID


class ReadIccidSkill(BaseSkill):
    """Composite skill for reading ICCID.

    This skill executes the following sequence:
    1. Select MF (3F00)
    2. Select EF_ICCID (2FE2) - located under MF
    3. Read Binary (10 bytes)

    The ICCID is encoded in BCD format and typically 19-20 digits.

    Example:
        result = await skill.run(ctx, {})
        iccid = parse_iccid(result.data)  # e.g., "89860012345678901234"
    """

    name = "read_iccid"
    description = "Read ICCID (Integrated Circuit Card ID) from SIM/USIM"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False
    supported_card_types = ["SIM", "USIM", "eUICC"]

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute READ ICCID skill.

        Args:
            ctx: Skill execution context
            params: {} (no parameters required)

        Returns:
            SkillResult with ICCID data.
        """
        try:
            # Step 1: Select MF
            result = await ctx.execute_skill("select_file", {"fid": FID_MF})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to select MF: {result.error}")

            # Step 2: Select EF_ICCID (under MF)
            result = await ctx.execute_skill("select_file", {"fid": FID_EF_ICCID})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to select EF_ICCID: {result.error}")

            # Step 3: Read binary (ICCID is 10 bytes)
            result = await ctx.execute_skill("read_binary", {"offset": 0, "length": 10})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to read ICCID: {result.error}")

            # Parse ICCID from BCD
            iccid_data = result.data
            iccid = parse_iccid(iccid_data)

            return SkillResult(
                success=True,
                data=iccid_data,
                sw=result.sw,
                metadata={
                    "iccid": iccid,
                    "length": len(iccid),
                }
            )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


def parse_iccid(data: bytes) -> str:
    """Parse ICCID from BCD-encoded bytes.

    ICCID format (ETSI TS 102 221):
    - Up to 10 bytes, BCD encoded
    - 19-20 digits typically

    Args:
        data: ICCID data bytes (typically 10)

    Returns:
        ICCID as decimal string.
    """
    if len(data) < 1:
        return ""

    # Decode BCD digits
    iccid_digits = []
    for byte in data:
        # Swap nibbles for ICCID (major digit first)
        high = (byte >> 4) & 0x0F
        low = byte & 0x0F

        # BCD digits: 0-9 are valid, 0xF is filler
        if high != 0x0F:
            iccid_digits.append(str(high))
        if low != 0x0F:
            iccid_digits.append(str(low))

    return "".join(iccid_digits)