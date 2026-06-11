"""APDU READ commands builder.

This module provides functions to build READ BINARY and READ RECORD
APDU commands according to ISO 7816-4 specification.
"""

from agent_service.apdu.constants.instructions import (
    INS_READ_BINARY,
    INS_READ_RECORD,
    CLA_ISO7816,
    READ_RECORD_P1_FIRST,
    READ_RECORD_P1_NEXT,
    READ_RECORD_P1_PREVIOUS,
    READ_RECORD_P1_ABSOLUTE,
)


def build_read_binary(
    offset: int = 0,
    length: int = 0,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build READ BINARY APDU command.

    Args:
        offset: Byte offset to read from (0-255)
        length: Number of bytes to read (0 = read all available)
        cla: Class byte

    Returns:
        APDU command as bytes.

    Example:
        >>> build_read_binary(0, 9)
        bytes.fromhex("00B0000009")
    """
    p1 = (offset >> 8) & 0x7F  # High byte of offset (bit 7 = 0)
    p2 = offset & 0xFF  # Low byte of offset
    le = length if length > 0 else 0  # Le = 0 means max available

    return bytes([cla, INS_READ_BINARY, p1, p2, le])


def build_read_binary_short_ef(
    short_ef: int,
    offset: int = 0,
    length: int = 0,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build READ BINARY with short EF identifier.

    Args:
        short_ef: Short EF identifier (1-30)
        offset: Byte offset
        length: Number of bytes to read
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = (short_ef & 0x1F) | 0x80  # Short EF indicator
    p2 = offset & 0xFF
    le = length if length > 0 else 0

    return bytes([cla, INS_READ_BINARY, p1, p2, le])


def build_read_record(
    record_number: int = 1,
    p1_mode: int = READ_RECORD_P1_ABSOLUTE,
    length: int = 0,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build READ RECORD APDU command.

    Args:
        record_number: Record number to read
        p1_mode: P1 mode (absolute, next, previous, etc.)
        length: Number of bytes to read (0 = read all)
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = record_number | p1_mode
    p2 = 0x04  # Read record with P3 as length
    le = length if length > 0 else 0

    return bytes([cla, INS_READ_RECORD, p1, p2, le])


def build_read_record_short_ef(
    short_ef: int,
    record_number: int = 1,
    p1_mode: int = READ_RECORD_P1_ABSOLUTE,
    length: int = 0,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build READ RECORD with short EF identifier.

    Args:
        short_ef: Short EF identifier (1-30)
        record_number: Record number
        p1_mode: P1 mode
        length: Number of bytes to read
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = (short_ef & 0x1F) | 0x80  # Short EF indicator
    p2 = record_number | 0x04 | (p1_mode << 3)
    le = length if length > 0 else 0

    return bytes([cla, INS_READ_RECORD, p1, p2, le])


def build_read_next_record(
    length: int = 0,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build READ NEXT RECORD APDU command.

    Args:
        length: Number of bytes to read
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = READ_RECORD_P1_NEXT
    p2 = 0x04
    le = length if length > 0 else 0

    return bytes([cla, INS_READ_RECORD, p1, p2, le])


def build_read_previous_record(
    length: int = 0,
    cla: int = CLA_ISO7816,
) -> bytes:
    """Build READ PREVIOUS RECORD APDU command.

    Args:
        length: Number of bytes to read
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = READ_RECORD_P1_PREVIOUS
    p2 = 0x04
    le = length if length > 0 else 0

    return bytes([cla, INS_READ_RECORD, p1, p2, le])