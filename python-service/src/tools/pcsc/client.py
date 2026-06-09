"""PCSC Client for smart card reader operations.

This module provides the PcscClient class for connecting to smart card
readers and sending APDU commands using pyscard library.
"""

import asyncio
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from tools.pcsc.exceptions import (
    ReaderNotFoundError,
    CardNotFoundError,
    ConnectionLostError,
    APDUError,
)


@dataclass
class ReaderInfo:
    """Smart card reader information."""

    name: str
    index: int
    atr: Optional[bytes] = None


@dataclass
class APDUResponse:
    """APDU command response."""

    data: bytes
    sw1: int
    sw2: int

    @property
    def sw(self) -> str:
        """Get combined status word as hex string."""
        return f"{self.sw1:02X}{self.sw2:02X}"

    @property
    def success(self) -> bool:
        """Check if response indicates success."""
        return self.sw1 == 0x90 or self.sw1 == 0x61


class PcscClient:
    """Smart card reader client using pyscard.

    This class provides methods for:
    - Connecting to smart card readers
    - Sending APDU commands
    - Managing card connections

    Example:
        client = PcscClient()
        client.connect()
        response = client.send_apdu([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00])
        client.disconnect()
    """

    def __init__(self, reader_index: int = 0):
        """Initialize PCSC client.

        Args:
            reader_index: Index of reader to use (default: 0, first reader)
        """
        self.reader_index = reader_index
        self.connection: Optional[Any] = None
        self.reader: Optional[Any] = None
        self.reader_name: Optional[str] = None
        self.atr: Optional[bytes] = None
        self._connected = False

    def list_readers(self) -> List[ReaderInfo]:
        """List all available smart card readers.

        Returns:
            List of ReaderInfo objects for each available reader.

        Raises:
            ReaderNotFoundError: If no readers are available.
        """
        try:
            from smartcard.System import readers
        except ImportError:
            raise ImportError("pyscard not installed. Run: pip install pyscard")

        reader_list = readers()
        if not reader_list:
            raise ReaderNotFoundError()

        result = []
        for i, r in enumerate(reader_list):
            result.append(ReaderInfo(name=str(r), index=i))

        return result

    def connect(self, reader_index: Optional[int] = None) -> bytes:
        """Connect to smart card reader and card.

        Args:
            reader_index: Optional reader index override

        Returns:
            ATR (Answer To Reset) bytes from the card.

        Raises:
            ReaderNotFoundError: If no reader available.
            CardNotFoundError: If no card in reader.
            ConnectionLostError: If connection fails.
        """
        if reader_index is not None:
            self.reader_index = reader_index

        try:
            from smartcard.System import readers
            from smartcard.Exceptions import NoCardException, CardConnectionException
        except ImportError:
            raise ImportError("pyscard not installed. Run: pip install pyscard")

        # Get readers
        reader_list = readers()
        if not reader_list:
            raise ReaderNotFoundError()

        # Select reader
        if self.reader_index >= len(reader_list):
            raise ReaderNotFoundError(
                f"Reader index {self.reader_index} out of range (available: {len(reader_list)})"
            )

        self.reader = reader_list[self.reader_index]
        self.reader_name = str(self.reader)

        # Create connection
        try:
            from smartcard.CardConnection import CardConnection
            self.connection = self.reader.createConnection()
            # Try T1 first, fallback to T0
            try:
                self.connection.connect(CardConnection.T1_protocol)
            except Exception:
                self.connection.connect(CardConnection.T0_protocol)
        except NoCardException:
            raise CardNotFoundError(self.reader_name)
        except Exception as e:
            raise ConnectionLostError(f"Failed to connect: {e}")

        # Get ATR
        self.atr = self.connection.getATR()
        self._connected = True

        return self.atr

    def disconnect(self) -> None:
        """Disconnect from smart card."""
        if self.connection:
            try:
                self.connection.disconnect()
            except Exception:
                pass  # Ignore disconnect errors
            self.connection = None
            self.reader = None
            self.atr = None
            self._connected = False

    def reconnect(self) -> bytes:
        """Reconnect to the card (after connection lost).

        Returns:
            ATR bytes from reconnection.
        """
        self.disconnect()
        return self.connect()

    def reset_card(self, cold_reset: bool = False) -> bytes:
        """Reset the smart card.

        Args:
            cold_reset: True for cold reset, False for warm reset

        Returns:
            New ATR after reset.
        """
        if not self.connection:
            raise ConnectionLostError("Not connected to card")

        try:
            from smartcard.scard import SCARD_RESET_CARD, SCARD_UNPOWER_CARD

            # Disconnect and reconnect for reset
            self.disconnect()
            return self.connect()

        except Exception as e:
            raise ConnectionLostError(f"Card reset failed: {e}")

    def send_apdu(
        self,
        apdu: List[int] | bytes,
        check_sw: bool = True,
    ) -> APDUResponse:
        """Send APDU command to card.

        Args:
            apdu: APDU command as list of integers or bytes
            check_sw: Whether to raise exception on error SW

        Returns:
            APDUResponse object with data and status word.

        Raises:
            ConnectionLostError: If connection lost during operation.
            APDUError: If check_sw=True and SW indicates error.
        """
        if not self.connection:
            raise ConnectionLostError("Not connected to card")

        # Convert to list if bytes
        if isinstance(apdu, bytes):
            apdu = list(apdu)

        try:
            data, sw1, sw2 = self.connection.transmit(apdu)
        except Exception as e:
            # Mark connection as lost
            self._connected = False
            raise ConnectionLostError(f"APDU transmission failed: {e}")

        response = APDUResponse(
            data=bytes(data) if data else bytes(),
            sw1=sw1,
            sw2=sw2,
        )

        # Check SW if requested
        if check_sw and not response.success:
            from apdu.constants.sw_codes import decode_sw
            raise APDUError(response.sw, decode_sw(response.sw))

        return response

    def send_apdu_hex(self, apdu_hex: str, check_sw: bool = True) -> APDUResponse:
        """Send APDU command from hex string.

        Args:
            apdu_hex: APDU as hex string (e.g., "00A40000023F00" or "00 A4 00 00")
            check_sw: Whether to raise exception on error SW

        Returns:
            APDUResponse object.
        """
        # 兼容带空格的格式
        cleaned = apdu_hex.replace(" ", "").replace("\n", "").strip()
        if not cleaned:
            raise ValueError("Empty APDU hex string")
        apdu_bytes = bytes.fromhex(cleaned)
        return self.send_apdu(list(apdu_bytes), check_sw)

    @property
    def is_connected(self) -> bool:
        """Check if connected to card."""
        return self._connected and self.connection is not None

    def get_reader_info(self) -> Optional[ReaderInfo]:
        """Get current reader information.

        Returns:
            ReaderInfo if connected, None otherwise.
        """
        if self.reader_name:
            return ReaderInfo(
                name=self.reader_name,
                index=self.reader_index,
                atr=self.atr,
            )
        return None