"""APDU command builders.

Provides helper classes for constructing ISO 7816-4 APDU commands
without manually crafting hex strings.

Example:
    apdu = SelectFile(fid="3F00", p2=0x0C).build()
    apdu = ReadBinary(offset=0, length=10).build()
    apdu = SendAPDU(cla=0x00, ins=0xA4, p1=0x00, p2=0x0C, data="3F00").build()
"""

from typing import Optional


class APDUBuilder:
    """Base APDU command builder."""

    def __init__(
        self,
        cla: int = 0x00,
        ins: int = 0x00,
        p1: int = 0x00,
        p2: int = 0x00,
        data: Optional[bytes | str | list[int]] = None,
        le: Optional[int] = None,
    ):
        self.cla = cla
        self.ins = ins
        self.p1 = p1
        self.p2 = p2
        self.data = self._parse_data(data) if data else None
        self.le = le

    def _parse_data(self, data: bytes | str | list[int]) -> bytes:
        """Parse data field into bytes."""
        if isinstance(data, str):
            return bytes.fromhex(data.replace(" ", ""))
        elif isinstance(data, list):
            return bytes(data)
        return data

    def build(self) -> str:
        """Build APDU command as hex string.

        Returns:
            APDU hex string with spaces (e.g., "00 A4 00 0C 02 3F 00").
        """
        parts = [self.cla, self.ins, self.p1, self.p2]
        
        if self.data is not None:
            parts.append(len(self.data))
            parts.extend(self.data)
            
        if self.le is not None:
            parts.append(self.le)
            
        return " ".join(f"{b:02X}" for b in parts)


class SelectFile(APDUBuilder):
    """SELECT FILE command (ISO 7816-4).

    Args:
        fid: File ID to select (hex string, e.g., "3F00").
        p1: P1 parameter (0x00=DF/EF by ID, 0x01=child DF, 0x02=EF under current DF, etc.)
        p2: P2 parameter (0x0C=no FCI, 0x00=return FCI).
    """

    def __init__(
        self,
        fid: str,
        p1: int = 0x00,
        p2: int = 0x0C,
    ):
        super().__init__(ins=0xA4, p1=p1, p2=p2, data=fid)


class ReadBinary(APDUBuilder):
    """READ BINARY command (ISO 7816-4).

    Args:
        offset: Offset to read from (0-65535).
        length: Number of bytes to read.
    """

    def __init__(
        self,
        offset: int = 0,
        length: int = 0,
    ):
        p1 = (offset >> 8) & 0xFF
        p2 = offset & 0xFF
        super().__init__(ins=0xB0, p1=p1, p2=p2, le=length)


class SendAPDU(APDUBuilder):
    """Generic APDU builder.

    Args:
        cla: CLA byte.
        ins: INS byte.
        p1: P1 parameter.
        p2: P2 parameter.
        data: Command data (hex string, bytes, or list of int).
        le: Expected response length.
    """

    pass
