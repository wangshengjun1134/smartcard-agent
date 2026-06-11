"""APDU authentication commands builder.

This module provides functions to build VERIFY PIN, CHANGE PIN,
UNBLOCK PIN, and GET CHALLENGE APDU commands.
"""

from agent_service.apdu.constants.instructions import (
    INS_VERIFY,
    INS_CHANGE,
    INS_UNBLOCK,
    INS_GET_CHALLENGE,
    CLA_ISO7816,
    CLA_GSM,
    PIN_REF_PIN1,
    PIN_REF_PIN2,
    PIN_REF_PUK1,
    PIN_REF_ADM1,
)


def build_verify_pin(
    pin_ref: int = PIN_REF_PIN1,
    pin: str = "",
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build VERIFY PIN APDU command.

    Args:
        pin_ref: PIN reference number (1 for PIN1, 2 for PIN2)
        pin: PIN value as string (digits only)
        cla: Class byte

    Returns:
        APDU command as bytes.

    Example:
        >>> build_verify_pin(PIN_REF_PIN1, "1234")
        bytes.fromhex("0020000108FFFFFFFFFFFFFFFF")  # padded to 8 bytes
    """
    p1 = 0x00
    p2 = pin_ref

    if pin:
        # Pad PIN to 8 bytes with FF
        pin_bytes = pin.encode("ascii")
        padded = pin_bytes + b"\xFF" * (8 - len(pin_bytes))
        lc = 8
        return bytes([cla, INS_VERIFY, p1, p2, lc]) + padded
    else:
        # Verify without PIN (check status)
        return bytes([cla, INS_VERIFY, p1, p2])


def build_change_pin(
    pin_ref: int = PIN_REF_PIN1,
    old_pin: str = "",
    new_pin: str = "",
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build CHANGE PIN APDU command.

    Args:
        pin_ref: PIN reference number
        old_pin: Current PIN value
        new_pin: New PIN value
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = 0x00
    p2 = pin_ref

    # Both PINs padded to 8 bytes each, total 16 bytes
    old_bytes = old_pin.encode("ascii") if old_pin else b""
    new_bytes = new_pin.encode("ascii") if new_pin else b""
    old_padded = old_bytes + b"\xFF" * (8 - len(old_bytes))
    new_padded = new_bytes + b"\xFF" * (8 - len(new_bytes))
    lc = 16

    return bytes([cla, INS_CHANGE, p1, p2, lc]) + old_padded + new_padded


def build_unblock_pin(
    pin_ref: int = PIN_REF_PIN1,
    puk: str = "",
    new_pin: str = "",
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build UNBLOCK PIN APDU command.

    Args:
        pin_ref: PIN reference number (unblocks this PIN)
        puk: PUK value
        new_pin: New PIN value
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = 0x00
    p2 = pin_ref

    # PUK (8 bytes) + new PIN (8 bytes)
    puk_bytes = puk.encode("ascii") if puk else b""
    new_bytes = new_pin.encode("ascii") if new_pin else b""
    puk_padded = puk_bytes + b"\xFF" * (8 - len(puk_bytes))
    new_padded = new_bytes + b"\xFF" * (8 - len(new_bytes))
    lc = 16

    return bytes([cla, INS_UNBLOCK, p1, p2, lc]) + puk_padded + new_padded


def build_get_challenge(
    length: int = 8,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build GET CHALLENGE APDU command.

    Args:
        length: Number of challenge bytes to request
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = 0x00
    p2 = 0x00
    le = length

    return bytes([cla, INS_GET_CHALLENGE, p1, p2, le])


def build_run_gsm_algorithm(
    rand: bytes,
    cla: int = CLA_GSM,
) -> bytes:
    """Build RUN GSM ALGORITHM APDU command (GSM specific).

    Args:
        rand: 16-byte RAND value for GSM authentication
        cla: Class byte (default: 0xA0 for GSM)

    Returns:
        APDU command as bytes.
    """
    p1 = 0x00
    p2 = 0x00
    lc = len(rand)

    return bytes([cla, INS_GET_CHALLENGE, p1, p2, lc]) + rand


def build_get_response(
    length: int,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build GET RESPONSE APDU command.

    Args:
        length: Number of bytes to retrieve
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    from agent_service.apdu.constants.instructions import INS_GET_RESPONSE

    p1 = 0x00
    p2 = 0x00
    le = length

    return bytes([cla, INS_GET_RESPONSE, p1, p2, le])