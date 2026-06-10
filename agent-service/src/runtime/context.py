"""Runtime Context for managing smart card operation state.

This module provides the RuntimeContext class that maintains
the minimal state during card operations.
"""

import logging
import time
from typing import Any, Optional, Callable, List, TYPE_CHECKING
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
    - APDU event listeners for broadcasting

    All other state (file path, PIN status, capabilities, etc.) is managed
    by individual Skills through APDU commands — they don't need to be
    tracked here.

    Example:
        ctx = RuntimeContext()
        ctx.attach_client(PcscClient())
        ctx.add_apdu_listener(my_listener)
        response = ctx.send_apdu([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00])
    """

    # PCSC client (non-serializable, runtime only)
    pcsc_client: Optional["PcscClient"] = field(default=None, repr=False, compare=False)

    # Connection state (minimal — managed by connect/disconnect)
    connected: bool = False
    current_reader: Optional[str] = None
    atr: Optional[bytes] = None

    # APDU event listeners (for broadcasting APDU execution events)
    _apdu_listeners: List[Callable] = field(default_factory=list, repr=False, compare=False)

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

    def add_apdu_listener(self, listener: Callable) -> None:
        """Add an APDU event listener.

        The listener will be called with the following arguments:
            capdu: Command APDU (hex string)
            rapdu: Response APDU (hex string)
            sw: Status word (e.g., "9000")
            duration_ms: Execution duration in milliseconds
            source: Source of the APDU call ("skill" or "tool")
            error: Optional error message

        Args:
            listener: Callable function to receive APDU events.
        """
        self._apdu_listeners.append(listener)

    def remove_apdu_listener(self, listener: Callable) -> None:
        """Remove an APDU event listener.

        Args:
            listener: The listener to remove.
        """
        self._apdu_listeners.remove(listener)

    def send_apdu(
        self,
        apdu: Any,
        check_sw: bool = True,
        source: str = "skill",
    ) -> Any:
        """Send APDU command through the attached PCSC client.

        Args:
            apdu: APDU command (list of int, bytes, or hex string).
            check_sw: Whether to raise exception on error SW.
            source: Source identifier for event broadcast ("skill" or "tool").

        Returns:
            APDUResponse object with data and status word.

        Raises:
            RuntimeError: If no PCSC client is attached or not connected.
        """
        if self.pcsc_client is None:
            raise RuntimeError("No PCSC client attached to context")

        # Normalize APDU to hex string
        apdu_str = apdu if isinstance(apdu, str) else (apdu.hex() if isinstance(apdu, bytes) else bytes(apdu).hex())
        apdu_str = apdu_str.upper().replace(" ", "")
        logger.debug(f"[APDU] Sending: {apdu_str}")

        start_time = time.time()
        try:
            if isinstance(apdu, str):
                resp = self.pcsc_client.send_apdu_hex(apdu, check_sw=check_sw)
            else:
                resp = self.pcsc_client.send_apdu(apdu, check_sw=check_sw)

            duration_ms = int((time.time() - start_time) * 1000)
            rapdu_str = resp.data.hex().upper() if resp.data else ""

            logger.debug(f"[APDU] Response: {rapdu_str} SW={resp.sw}")

            # Notify all listeners
            for listener in self._apdu_listeners:
                try:
                    listener(
                        capdu=apdu_str,
                        rapdu=rapdu_str,
                        sw=resp.sw,
                        duration_ms=duration_ms,
                        source=source,
                        error=None if resp.sw == "9000" else f"SW: {resp.sw}",
                    )
                except Exception as e:
                    logger.warning(f"[APDU Listener] Failed: {e}")

            return resp
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Mark connection as lost so skills can detect it
            self.connected = False
            self.current_reader = None
            self.atr = None
            logger.error(f"[APDU] Error: {e}")

            # Notify all listeners of error
            for listener in self._apdu_listeners:
                try:
                    listener(
                        capdu=apdu_str,
                        rapdu="",
                        sw="N/A",
                        duration_ms=duration_ms,
                        source=source,
                        error=str(e),
                    )
                except Exception as listener_err:
                    logger.warning(f"[APDU Listener] Failed: {listener_err}")

            raise