"""Runtime Context for managing smart card operation state.

This module provides the RuntimeContext class that maintains
the current state during card operations.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import copy


class ConnectionState(Enum):
    """Card connection state."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"


class SecureChannelState(Enum):
    """Secure channel state."""

    NONE = "none"
    SCP03 = "scp03"
    SCP80 = "scp80"


@dataclass
class ExecutionStep:
    """Record of a single execution step."""

    skill_name: str
    params: Dict[str, Any]
    apdu: Optional[bytes] = None
    response: Optional[bytes] = None
    sw: Optional[str] = None
    success: bool = False
    timestamp: Optional[str] = None


@dataclass
class RuntimeContext:
    """Runtime context for smart card operations.

    This class maintains the current state during card operations:
    - Connection state and reader info
    - Selected file path
    - Current application
    - PIN verification status
    - Secure channel state
    - Card capabilities
    - Execution history

    Example:
        ctx = RuntimeContext()
        ctx.connect(reader_name="ACS ACR38", atr=bytes.fromhex("3B..."))
        ctx.select_file("3F00")
        ctx.select_file("7F20")
    """

    # Connection state
    connected: bool = False
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    current_reader: Optional[str] = None
    atr: Optional[bytes] = None

    # File system navigation
    selected_path: List[str] = field(default_factory=list)  # ["3F00", "7F20", ...]
    current_application: Optional[str] = None  # AID if selected by AID

    # Security state
    pin_verified: Dict[int, bool] = field(default_factory=dict)  # {pin_ref: verified}
    secure_channel_state: SecureChannelState = SecureChannelState.NONE
    secure_channel_info: Dict[str, Any] = field(default_factory=dict)

    # Card capabilities
    card_capabilities: List[str] = field(default_factory=list)
    card_type: Optional[str] = None  # "USIM", "SIM", "eUICC", etc.
    discovered_apps: List[str] = field(default_factory=list)  # List of AIDs

    # Execution tracking
    execution_history: List[ExecutionStep] = field(default_factory=list)
    last_apdu: Optional[bytes] = None
    last_response: Optional[bytes] = None
    last_sw: Optional[str] = None

    def connect(self, reader_name: str, atr: bytes) -> None:
        """Record successful connection.

        Args:
            reader_name: Name of the connected reader
            atr: Answer To Reset bytes
        """
        self.connected = True
        self.connection_state = ConnectionState.CONNECTED
        self.current_reader = reader_name
        self.atr = atr
        self.selected_path = ["3F00"]  # Start at MF
        self.pin_verified = {}
        self.secure_channel_state = SecureChannelState.NONE

    def disconnect(self) -> None:
        """Record disconnection."""
        self.connected = False
        self.connection_state = ConnectionState.DISCONNECTED
        self.current_reader = None
        self.atr = None
        self.selected_path = []
        self.current_application = None
        self.pin_verified = {}
        self.secure_channel_state = SecureChannelState.NONE

    def select_file(self, fid: str) -> None:
        """Record file selection.

        Args:
            fid: File ID that was selected
        """
        if fid == "3F00":
            # Selecting MF resets path
            self.selected_path = ["3F00"]
        else:
            self.selected_path.append(fid)
        self.current_application = None

    def select_application(self, aid: str) -> None:
        """Record application selection by AID.

        Args:
            aid: Application ID that was selected
        """
        self.current_application = aid

    def verify_pin(self, pin_ref: int) -> None:
        """Record PIN verification.

        Args:
            pin_ref: PIN reference number
        """
        self.pin_verified[pin_ref] = True

    def clear_pin_verification(self, pin_ref: int) -> None:
        """Clear PIN verification status.

        Args:
            pin_ref: PIN reference number
        """
        self.pin_verified[pin_ref] = False

    def is_pin_verified(self, pin_ref: int) -> bool:
        """Check if PIN is verified.

        Args:
            pin_ref: PIN reference number

        Returns:
            True if PIN is currently verified.
        """
        return self.pin_verified.get(pin_ref, False)

    def establish_secure_channel(self, protocol: SecureChannelState, info: Dict[str, Any] = None) -> None:
        """Record secure channel establishment.

        Args:
            protocol: Secure channel protocol (SCP03, SCP80)
            info: Additional secure channel info
        """
        self.secure_channel_state = protocol
        if info:
            self.secure_channel_info = info

    def record_execution(
        self,
        skill_name: str,
        params: Dict[str, Any],
        apdu: Optional[bytes] = None,
        response: Optional[bytes] = None,
        sw: Optional[str] = None,
        success: bool = False,
    ) -> None:
        """Record an execution step.

        Args:
            skill_name: Name of the skill executed
            params: Skill parameters
            apdu: APDU command bytes
            response: Response data bytes
            sw: Status word
            success: Whether execution succeeded
        """
        from datetime import datetime

        step = ExecutionStep(
            skill_name=skill_name,
            params=params,
            apdu=apdu,
            response=response,
            sw=sw,
            success=success,
            timestamp=datetime.now().isoformat(),
        )
        self.execution_history.append(step)

        # Update last execution info
        if apdu:
            self.last_apdu = apdu
        if response:
            self.last_response = response
        if sw:
            self.last_sw = sw

    def add_capability(self, capability: str) -> None:
        """Add discovered card capability.

        Args:
            capability: Capability name
        """
        if capability not in self.card_capabilities:
            self.card_capabilities.append(capability)

    def add_discovered_app(self, aid: str) -> None:
        """Add discovered application.

        Args:
            aid: Application ID
        """
        if aid not in self.discovered_apps:
            self.discovered_apps.append(aid)

    def get_current_path(self) -> str:
        """Get current file path as string.

        Returns:
            Path string like "3F00/7F20/6F07"
        """
        return "/".join(self.selected_path)

    def get_state_dict(self) -> Dict[str, Any]:
        """Get state as dictionary for serialization.

        Returns:
            Dictionary representation of current state.
        """
        return {
            "connected": self.connected,
            "connection_state": self.connection_state.value,
            "current_reader": self.current_reader,
            "atr": self.atr.hex() if self.atr else None,
            "selected_path": self.selected_path,
            "current_application": self.current_application,
            "pin_verified": self.pin_verified,
            "secure_channel_state": self.secure_channel_state.value,
            "card_type": self.card_type,
            "card_capabilities": self.card_capabilities,
            "discovered_apps": self.discovered_apps,
        }

    def restore_from_dict(self, state: Dict[str, Any]) -> None:
        """Restore state from dictionary.

        Args:
            state: State dictionary
        """
        self.connected = state.get("connected", False)
        self.connection_state = ConnectionState(state.get("connection_state", "disconnected"))
        self.current_reader = state.get("current_reader")
        atr_hex = state.get("atr")
        self.atr = bytes.fromhex(atr_hex) if atr_hex else None
        self.selected_path = state.get("selected_path", [])
        self.current_application = state.get("current_application")
        self.pin_verified = state.get("pin_verified", {})
        self.secure_channel_state = SecureChannelState(state.get("secure_channel_state", "none"))
        self.card_type = state.get("card_type")
        self.card_capabilities = state.get("card_capabilities", [])
        self.discovered_apps = state.get("discovered_apps", [])

    def copy(self) -> RuntimeContext:
        """Create a deep copy of this context.

        Returns:
            New RuntimeContext with same state.
        """
        new_ctx = RuntimeContext()
        new_ctx.restore_from_dict(self.get_state_dict())
        new_ctx.execution_history = copy.deepcopy(self.execution_history)
        return new_ctx