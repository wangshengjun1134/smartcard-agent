"""APDU SELECT command builder.

This module provides functions to build SELECT APDU commands
according to ISO 7816-4 specification.
"""

from typing import Union

from agent_service.apdu.constants.instructions import (
    INS_SELECT,
    CLA_ISO7816,
    CLA_GSM,
    SELECT_TYPE_FCI,
)


def build_select_file(
    fid: str,
    cla: int = CLA_ISO7816,
    select_type: int = SELECT_TYPE_FCI,
) -> bytes:
    """Build SELECT FILE APDU command.

    Args:
        fid: File ID as 4-character hex string (e.g., "3F00", "6F07")
        cla: Class byte (default: 0x00 for ISO 7816)
        select_type: P2 byte for response type (default: 0x04 for FCI)

    Returns:
        APDU command as bytes.

    Example:
        >>> build_select_file("3F00")
        bytes.fromhex("00A40000023F00")
    """
    fid_bytes = bytes.fromhex(fid)
    p1 = 0x00  # Select by FID from current DF or MF
    p2 = select_type
    lc = len(fid_bytes)  # Length of data field

    # CLA INS P1 P2 Lc Data
    return bytes([cla, INS_SELECT, p1, p2, lc]) + fid_bytes


def build_select_by_aid(
    aid: str,
    cla: int = CLA_ISO7816,
    select_type: int = SELECT_TYPE_FCI,
) -> bytes:
    """Build SELECT by AID APDU command.

    Args:
        aid: Application ID as hex string (e.g., "A0000000871001")
        cla: Class byte
        select_type: P2 byte for response type

    Returns:
        APDU command as bytes.
    """
    aid_bytes = bytes.fromhex(aid)
    p1 = 0x04  # Select by DF name (AID)
    p2 = select_type
    lc = len(aid_bytes)

    return bytes([cla, INS_SELECT, p1, p2, lc]) + aid_bytes


def build_select_from_mf(
    fid: str,
    cla: int = CLA_ISO7816,
    select_type: int = SELECT_TYPE_FCI,
) -> bytes:
    """Build SELECT from MF APDU command.

    This resets to MF and then selects the file.

    Args:
        fid: File ID as hex string
        cla: Class byte
        select_type: P2 byte for response type

    Returns:
        APDU command as bytes.
    """
    fid_bytes = bytes.fromhex(fid)
    p1 = 0x00
    p2 = select_type | 0x08  # From MF flag
    lc = len(fid_bytes)

    return bytes([cla, INS_SELECT, p1, p2, lc]) + fid_bytes


def build_select_parent_df(cla: int = CLA_ISO7816) -> bytes:
    """Build SELECT PARENT DF APDU command.

    Args:
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = 0x03  # Select parent DF
    p2 = 0x00  # No data requested

    return bytes([cla, INS_SELECT, p1, p2])


def build_select_next_occurrence(cla: int = CLA_ISO7816) -> bytes:
    """Build SELECT NEXT OCCURRENCE APDU command.

    Used for partial AID selection to find next matching application.

    Args:
        cla: Class byte

    Returns:
        APDU command as bytes.
    """
    p1 = 0x02  # Next occurrence
    p2 = SELECT_TYPE_FCI

    return bytes([cla, INS_SELECT, p1, p2])