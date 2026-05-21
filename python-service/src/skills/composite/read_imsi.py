"""Read IMSI Skill - read the IMSI from a SIM/USIM card.

This composite skill reads the IMSI (International Mobile Subscriber Identity)
from the card by selecting the appropriate file and reading the data.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.constants.file_ids import FID_MF, FID_DF_GSM, FID_EF_IMSI


class ReadImsiSkill(BaseSkill):
    """Composite skill for reading IMSI.

    This skill executes the following sequence:
    1. Select MF (3F00)
    2. Select DF_GSM (7F20)
    3. Select EF_IMSI (6F07)
    4. Read Binary (9 bytes)

    The IMSI is encoded in BCD format:
    - First byte: Length + parity
    - Following bytes: MCC + MNC + MSIN in BCD

    Example:
        result = await skill.run(ctx, {})
        imsi = parse_imsi(result.data)  # e.g., "46000123456789"
    """

    name = "read_imsi"
    description = "Read IMSI (International Mobile Subscriber Identity) from SIM/USIM"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False
    supported_card_types = ["SIM", "USIM"]

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute READ IMSI skill.

        Args:
            ctx: Skill execution context
            params: {} (no parameters required)

        Returns:
            SkillResult with IMSI data.
        """
        try:
            # Step 1: Select MF
            result = await ctx.execute_skill("select_file", {"fid": FID_MF})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to select MF: {result.error}")

            # Step 2: Select DF_GSM/DF_USIM
            result = await ctx.execute_skill("select_file", {"fid": FID_DF_GSM})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to select DF_GSM: {result.error}")

            # Step 3: Select EF_IMSI
            result = await ctx.execute_skill("select_file", {"fid": FID_EF_IMSI})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to select EF_IMSI: {result.error}")

            # Step 4: Read binary (IMSI is 9 bytes)
            result = await ctx.execute_skill("read_binary", {"offset": 0, "length": 9})
            if not result.success:
                return SkillResult(success=False, error=f"Failed to read IMSI: {result.error}")

            # Parse IMSI from BCD
            imsi_data = result.data
            imsi = parse_imsi(imsi_data)

            return SkillResult(
                success=True,
                data=imsi_data,
                sw=result.sw,
                metadata={
                    "imsi": imsi,
                    "mcc": imsi[:3] if len(imsi) >= 3 else "",
                    "mnc": imsi[3:5] if len(imsi) >= 5 else "",
                    "msin": imsi[5:] if len(imsi) > 5 else "",
                }
            )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


def parse_imsi(data: bytes) -> str:
    """Parse IMSI from BCD-encoded bytes.

    IMSI format (ETSI TS 102 221):
    - Byte 1: Length of IMSI (bits 1-4) + parity (bit 8)
    - Bytes 2-9: BCD-encoded digits

    Args:
        data: 9 bytes of IMSI data

    Returns:
        IMSI as decimal string (up to 15 digits).
    """
    if len(data) < 2:
        return ""

    # First byte contains length in low nibble
    length = data[0] & 0x0F

    # Decode BCD digits from remaining bytes
    imsi_digits = []
    for i in range(1, len(data)):
        byte = data[i]
        # Low nibble first, then high nibble
        low = byte & 0x0F
        high = (byte >> 4) & 0x0F

        # BCD digits: 0-9 are valid, 0xF is filler
        if low != 0x0F:
            imsi_digits.append(str(low))
        if high != 0x0f and len(imsi_digits) < length:
            imsi_digits.append(str(high))

    # IMSI length is specified in first byte
    return "".join(imsi_digits[:length]) if length > 0 else "".join(imsi_digits)