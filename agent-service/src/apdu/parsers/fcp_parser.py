"""FCP (File Control Parameters) parser.

This module parses File Control Parameters from SELECT command responses
according to ISO 7816-4 and ETSI TS 102 221 specifications.
"""

from typing import Dict, Any, Optional
from apdu.parsers.tlv_parser import parse_tlv, find_tag


# FCP template tags (ISO 7816-4)
FCP_TAG_FMD = "64"  # File Management Data
FCP_TAG_FCI = "6F"  # File Control Information
FCP_TAG_FCP = "62"  # File Control Parameters

# FCP content tags
FCP_TAG_FILE_SIZE = "80"  # File size (transparent) or record length
FCP_TAG_TOTAL_FILE_SIZE = "81"  # Total file size including structure
FCP_TAG_FILE_DESCRIPTOR = "82"  # File descriptor byte
FCP_TAG_FILE_ID = "83"  # File identifier
FCP_TAG_DF_NAME = "84"  # DF name (AID)
FCP_TAG_PROPRIETARY = "85"  # Proprietary information
FCP_TAG_SECURITY_ATTRIBUTES = "86"  # Security attributes compact format
FCP_TAG_SECURITY_ATTRIBUTES_EXP = "87"  # Security attributes expanded format
FCP_TAG_LIFE_CYCLE_STATUS = "8A"  # Life cycle status byte

# Life cycle status values
LCS_NO_INFORMATION = 0x00
LCS_CREATED = 0x01
LCS_ACTIVATED = 0x05
LCS_DEACTIVATED = 0x04
LCS_TERMINATED = 0x06


def parse_fcp(data: bytes) -> Dict[str, Any]:
    """Parse File Control Parameters from SELECT response.

    Args:
        data: FCP/FCI/FMD response data from SELECT command

    Returns:
        Dictionary containing parsed file information:
        - file_size: File size in bytes
        - file_descriptor: File type and structure
        - file_id: File identifier (hex string)
        - df_name: DF name/AID (hex string, if present)
        - life_cycle_status: Life cycle status
        - security_attributes: Security info
    """
    if not data:
        return {}

    # Parse TLV structure
    tlv = parse_tlv(data)

    # Determine which template is used
    template = None
    for template_tag in [FCP_TAG_FCI, FCP_TAG_FCP, FCP_TAG_FMD]:
        if template_tag in tlv:
            template = tlv[template_tag]
            break

    if template is None:
        # Direct FCP content (no wrapper)
        template = tlv

    result = {}

    # Parse file size
    file_size_data = find_tag(template, FCP_TAG_FILE_SIZE)
    if file_size_data:
        result["file_size"] = _parse_size(file_size_data)

    # Parse total file size
    total_size_data = find_tag(template, FCP_TAG_TOTAL_FILE_SIZE)
    if total_size_data:
        result["total_file_size"] = _parse_size(total_size_data)

    # Parse file descriptor
    fd_data = find_tag(template, FCP_TAG_FILE_DESCRIPTOR)
    if fd_data:
        result["file_descriptor"] = _parse_file_descriptor(fd_data)

    # Parse file ID
    fid_data = find_tag(template, FCP_TAG_FILE_ID)
    if fid_data:
        result["file_id"] = fid_data.hex().upper()

    # Parse DF name
    df_name_data = find_tag(template, FCP_TAG_DF_NAME)
    if df_name_data:
        result["df_name"] = df_name_data.hex().upper()

    # Parse life cycle status
    lcs_data = find_tag(template, FCP_TAG_LIFE_CYCLE_STATUS)
    if lcs_data:
        result["life_cycle_status"] = _parse_lifecycle_status(lcs_data)

    # Parse security attributes
    sec_data = find_tag(template, FCP_TAG_SECURITY_ATTRIBUTES)
    if sec_data:
        result["security_attributes_compact"] = sec_data.hex().upper()

    sec_exp_data = find_tag(template, FCP_TAG_SECURITY_ATTRIBUTES_EXP)
    if sec_exp_data:
        result["security_attributes_expanded"] = sec_exp_data.hex().upper()

    return result


def _parse_size(data: bytes) -> int:
    """Parse size from FCP size tag.

    Args:
        data: Size bytes

    Returns:
        Size as integer.
    """
    size = 0
    for byte in data:
        size = (size << 8) | byte
    return size


def _parse_file_descriptor(data: bytes) -> Dict[str, Any]:
    """Parse file descriptor byte.

    Args:
        data: File descriptor bytes

    Returns:
        Dictionary with file type and structure info.
    """
    if not data:
        return {}

    result = {}

    # First byte describes file structure
    fd_byte = data[0]

    # Check file type
    if fd_byte == 0x00:
        result["type"] = "transparent"
    elif fd_byte == 0x01:
        result["type"] = "linear_fixed"
        if len(data) >= 3:
            result["record_length"] = data[1]
            result["record_count"] = data[2]
    elif fd_byte == 0x02:
        result["type"] = "linear_variable"
        if len(data) >= 2:
            result["record_count"] = data[1]
    elif fd_byte == 0x03:
        result["type"] = "cyclic"
        if len(data) >= 3:
            result["record_length"] = data[1]
            result["record_count"] = data[2]
    elif fd_byte == 0x04:
        result["type"] = "execute"
    elif fd_byte == 0x06:
        result["type"] = "df"  # Dedicated File
    elif fd_byte == 0x07:
        result["type"] = "ef"  # Elementary File (binary)
    elif fd_byte == 0x08:
        result["type"] = "mf"  # Master File

    return result


def _parse_lifecycle_status(data: bytes) -> str:
    """Parse life cycle status byte.

    Args:
        data: Life cycle status byte

    Returns:
        Status description string.
    """
    if not data:
        return "unknown"

    lcs = data[0]

    if lcs == LCS_NO_INFORMATION:
        return "no_information"
    elif lcs == LCS_CREATED:
        return "created"
    elif lcs == LCS_ACTIVATED:
        return "activated"
    elif lcs == LCS_DEACTIVATED:
        return "deactivated"
    elif lcs == LCS_TERMINATED:
        return "terminated"
    else:
        return f"unknown_0x{lcs:02X}"


def get_file_type(fcp: Dict[str, Any]) -> str:
    """Get file type from parsed FCP.

    Args:
        fcp: Parsed FCP dictionary

    Returns:
        File type string (transparent, linear_fixed, cyclic, df, etc.)
    """
    if "file_descriptor" in fcp:
        return fcp["file_descriptor"].get("type", "unknown")
    return "unknown"