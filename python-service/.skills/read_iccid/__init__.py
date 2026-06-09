"""Read ICCID from smart card."""

from skills.base.base_skill import BaseSkill, SkillResult
from skills.base.apdu import SelectFile, ReadBinary


class ReadICCIDSkill(BaseSkill):
    """Read ICCID (Integrated Circuit Card Identifier) from smart card."""

    name = "read_iccid"
    description = "读取 ICCID（集成电路卡识别码）"
    category = "composite"
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx, params=None):
        """Execute ICCID read operation."""
        if params is None:
            params = {}

        try:
            # 检查连接状态
            if not ctx.connected:
                return SkillResult(
                    success=False,
                    data=None,
                    error="未连接到卡片，请先通过 APDU 控制台连接读卡器"
                )

            # Select MF (3F00)
            apdu_select = SelectFile(fid="3F00").build()
            resp = ctx.send_apdu(apdu_select)

            if resp.sw1 not in (0x90, 0x61):
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Failed to select MF: {resp.sw}"
                )

            # Select EF_ICCID (2FE2)
            apdu_select_ef = SelectFile(fid="2FE2").build()
            resp = ctx.send_apdu(apdu_select_ef)

            if resp.sw1 not in (0x90, 0x61):
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Failed to select EF_ICCID: {resp.sw}"
                )

            # Read Binary (10 bytes)
            apdu_read = ReadBinary(offset=0, length=10).build()
            resp = ctx.send_apdu(apdu_read)

            if resp.sw1 not in (0x90, 0x61):
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Failed to read ICCID: {resp.sw}"
                )

            # Parse ICCID from response data
            iccid_bytes = resp.data
            iccid_hex = iccid_bytes.hex().upper()

            return SkillResult(
                success=True,
                data={"iccid": iccid_hex, "iccid_raw": iccid_bytes.hex()},
                error=None
            )

        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e)
            )


def register():
    """Register the Read ICCID skill."""
    return ReadICCIDSkill()
