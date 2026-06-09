"""Runtime Context for managing smart card operation state.

This module provides the RuntimeContext class that maintains
the minimal state during card operations.
"""

import logging
from typing import Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from tools.pcsc.client import PcscClient

logger = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    """Runtime context for smart card operations.

    This class maintains the minimal runtime state needed for card operations:
    - PCSC client for hardware communication
    - Current connection state and reader info
    - ATR (Answer To Reset)

    All other state (file path, PIN status, capabilities, etc.) is managed
    by individual Skills through APDU commands — they don't need to be
    tracked here.

    Example:
        ctx = RuntimeContext()
        ctx.attach_client(PcscClient())
        response = ctx.send_apdu([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00])
    """

    # PCSC client (non-serializable, runtime only)
    pcsc_client: Optional["PcscClient"] = field(default=None, repr=False, compare=False)

    # Connection state (minimal — managed by connect/disconnect)
    connected: bool = False
    current_reader: Optional[str] = None
    atr: Optional[bytes] = None

    def connect(self, reader_name: str, atr: bytes) -> None:
        """Record successful connection.

        Args:
            reader_name: Name of the connected reader
            atr: Answer To Reset bytes
        """
        self.connected = True
        self.current_reader = reader_name
        self.atr = atr

    def disconnect(self) -> None:
        """Record disconnection."""
        self.connected = False
        self.current_reader = None
        self.atr = None

    def copy(self) -> "RuntimeContext":
        """Create a shallow copy of this context.

        Note: pcsc_client is NOT copied (non-serializable runtime resource).
        Use attach_client() on the copy to reattach the client.

        Returns:
            New RuntimeContext with same connection state.
        """
        new_ctx = RuntimeContext()
        new_ctx.connected = self.connected
        new_ctx.current_reader = self.current_reader
        new_ctx.atr = self.atr
        return new_ctx

    def attach_client(self, client: "PcscClient") -> None:
        """Attach a PCSC client to this context.

        Args:
            client: PcscClient instance for hardware communication.
        """
        self.pcsc_client = client

    def send_apdu(
        self,
        apdu: Any,
        check_sw: bool = True,
    ) -> Any:
        """Send APDU command through the attached PCSC client.

        Args:
            apdu: APDU command (list of int, bytes, or hex string).
            check_sw: Whether to raise exception on error SW.

        Returns:
            APDUResponse object with data and status word.

        Raises:
            RuntimeError: If no PCSC client is attached or not connected.
        """
        if self.pcsc_client is None:
            raise RuntimeError("No PCSC client attached to context")

        # Log APDU command
        apdu_str = apdu if isinstance(apdu, str) else (apdu.hex() if isinstance(apdu, bytes) else str(apdu))
        print(f"\n[APDU] Sending: {apdu_str}")

        try:
            if isinstance(apdu, str):
                resp = self.pcsc_client.send_apdu_hex(apdu, check_sw=check_sw)
            else:
                resp = self.pcsc_client.send_apdu(apdu, check_sw=check_sw)

            print(f"[APDU] Response: {resp.data.hex().upper() if resp.data else ''} {resp.sw}")
            return resp
        except Exception as e:
            # Mark connection as lost so skills can detect it
            self.connected = False
            self.current_reader = None
            self.atr = None
            print(f"[APDU] Error: {e}")
            raise