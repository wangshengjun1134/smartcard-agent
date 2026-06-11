"""Status Word (SW) parser for APDU response analysis.

This module provides detailed SW parsing and analysis functions.
"""

from typing import Dict, Tuple
from agent_service.apdu.constants.sw_codes import (
    SW_DESCRIPTIONS,
    SW_NORMAL,
    SW_SECURITY_CONDITION_NOT_SATISFIED,
    SW_FILE_NOT_FOUND,
    SW_UNKNOWN_ERROR,
)


def decode_sw(sw: str) -> str:
    """Decode Status Word to its description.

    Args:
        sw: Two-byte status word as hex string (e.g., "9000", "6982")

    Returns:
        Description of the status word meaning.
    """
    # Import from constants for consistency
    from agent_service.apdu.constants.sw_codes import decode_sw as _decode_sw
    return _decode_sw(sw)


def parse_sw(sw1: int, sw2: int) -> Dict[str, any]:
    """Parse SW1 and SW2 bytes into detailed information.

    Args:
        sw1: First status byte (SW1)
        sw2: Second status byte (SW2)

    Returns:
        Dictionary containing:
        - sw: Combined SW as hex string
        - description: Human-readable description
        - category: Error category (success, warning, error)
        - needs_get_response: Whether GET RESPONSE is needed
        - retry_count: PIN retry count if applicable
    """
    sw = f"{sw1:02X}{sw2:02X}"

    result = {
        "sw": sw,
        "description": decode_sw(sw),
        "needs_get_response": False,
        "retry_count": None,
    }

    # Determine category
    if sw1 == 0x90:
        result["category"] = "success"
    elif sw1 == 0x61:
        result["category"] = "success"
        result["needs_get_response"] = True
        result["get_response_length"] = sw2
    elif sw1 == 0x62:
        result["category"] = "warning"
    elif sw1 == 0x63:
        result["category"] = "warning"
        # PIN retry count in SW2 low nibble
        result["retry_count"] = sw2 & 0x0F
    elif sw1 == 0x64:
        result["category"] = "execution_error"
    elif sw1 >= 0x65 and sw1 <= 0x6F:
        result["category"] = "error"
    else:
        result["category"] = "unknown"

    return result


def analyze_response(response: bytes, sw1: int, sw2: int) -> Dict[str, any]:
    """Analyze complete APDU response.

    Args:
        response: Response data bytes
        sw1: Status word 1
        sw2: Status word 2

    Returns:
        Dictionary with response analysis.
    """
    sw_info = parse_sw(sw1, sw2)

    result = {
        "data": response,
        "data_length": len(response),
        "sw": sw_info["sw"],
        "sw_category": sw_info["category"],
        "sw_description": sw_info["description"],
        "success": sw_info["category"] in ["success"],
        "needs_get_response": sw_info.get("needs_get_response", False),
        "get_response_length": sw_info.get("get_response_length", 0),
        "retry_count": sw_info.get("retry_count"),
    }

    return result


def sw_to_bytes(sw: str) -> Tuple[int, int]:
    """Convert SW hex string to SW1, SW2 integers.

    Args:
        sw: SW as hex string (e.g., "9000")

    Returns:
        Tuple of (sw1, sw2) integers.
    """
    if len(sw) != 4:
        raise ValueError(f"Invalid SW length: {sw}")

    sw1 = int(sw[:2], 16)
    sw2 = int(sw[2:4], 16)

    return sw1, sw2


def is_successful_sw(sw: str) -> bool:
    """Check if SW indicates successful operation.

    Args:
        sw: SW as hex string

    Returns:
        True if successful.
    """
    sw1 = int(sw[:2], 16)
    return sw1 == 0x90 or sw1 == 0x61


def get_retry_count(sw: str) -> Optional[int]:
    """Get PIN retry count from SW.

    Args:
        sw: SW as hex string (63CX)

    Returns:
        Retry count if SW indicates PIN error, None otherwise.
    """
    if sw[:2] == "63":
        return int(sw[2:4], 16) & 0x0F
    return None


def needs_retry_after_error(sw: str) -> bool:
    """Check if error might be resolved by retry.

    Args:
        sw: SW as hex string

    Returns:
        True if retry might help.
    """
    # Transient errors that might succeed on retry
    retryable_sw = ["6F00", "6FFF"]
    return sw in retryable_sw