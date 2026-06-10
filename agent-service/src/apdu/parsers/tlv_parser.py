"""TLV (Tag-Length-Value) parser for BER-TLV encoding.

This module provides functions to parse BER-TLV encoded data
according to ISO 7816-4 specification.
"""

from typing import Dict, List, Tuple, Union, Any


def parse_tlv(data: bytes) -> Dict[str, Any]:
    """Parse BER-TLV encoded data into a dictionary.

    Args:
        data: BER-TLV encoded bytes

    Returns:
        Dictionary with tag keys and parsed values.
        Values can be bytes (primitive) or dict (constructed).
    """
    if not data:
        return {}

    result = {}
    offset = 0

    while offset < len(data):
        # Parse tag
        tag, tag_length = _parse_tag(data, offset)
        offset += tag_length

        # Parse length
        length, length_length = _parse_length(data, offset)
        offset += length_length

        # Parse value
        value_bytes = data[offset:offset + length]
        offset += length

        # Check if constructed (bit 6 of first tag byte = 1)
        is_constructed = (int(data[offset - tag_length - length_length]) & 0x20) != 0

        if is_constructed:
            # Recursively parse constructed TLV
            result[tag] = parse_tlv(value_bytes)
        else:
            result[tag] = value_bytes

    return result


def _parse_tag(data: bytes, offset: int) -> Tuple[str, int]:
    """Parse TLV tag bytes.

    Args:
        data: TLV data
        offset: Current position

    Returns:
        Tuple of (tag_hex_string, tag_byte_count).
    """
    if offset >= len(data):
        return "", 0

    first_byte = data[offset]

    # Bits 5-1 of first byte indicate tag type
    # If bits 5-1 are all 1, tag continues to next bytes
    if (first_byte & 0x1F) == 0x1F:
        # Multi-byte tag
        tag_bytes = [first_byte]
        offset += 1
        while offset < len(data):
            next_byte = data[offset]
            tag_bytes.append(next_byte)
            offset += 1
            # Bit 8 of continuation bytes indicates more tag bytes
            if (next_byte & 0x80) == 0:
                break
        tag_hex = bytes(tag_bytes).hex().upper()
        return tag_hex, len(tag_bytes)
    else:
        # Single-byte tag
        tag_hex = f"{first_byte:02X}"
        return tag_hex, 1


def _parse_length(data: bytes, offset: int) -> Tuple[int, int]:
    """Parse TLV length bytes.

    Args:
        data: TLV data
        offset: Current position

    Returns:
        Tuple of (length_value, length_byte_count).
    """
    if offset >= len(data):
        return 0, 0

    first_byte = data[offset]

    if (first_byte & 0x80) == 0:
        # Short form: length is in bits 7-1
        return first_byte, 1
    else:
        # Long form: first byte indicates number of length bytes
        num_length_bytes = first_byte & 0x7F
        if num_length_bytes == 0:
            # Indefinite length (not commonly used)
            return 0, 1

        length = 0
        for i in range(1, num_length_bytes + 1):
            if offset + i < len(data):
                length = (length << 8) | data[offset + i]

        return length, 1 + num_length_bytes


def find_tag(tlv_dict: Dict[str, Any], tag: str) -> Union[bytes, Dict, None]:
    """Find a specific tag in parsed TLV dictionary.

    Args:
        tlv_dict: Parsed TLV dictionary
        tag: Tag to find (hex string, e.g., "80", "82")

    Returns:
        Value of the tag, or None if not found.
    """
    tag_upper = tag.upper()

    # Direct match
    if tag_upper in tlv_dict:
        return tlv_dict[tag_upper]

    # Search in constructed tags
    for key, value in tlv_dict.items():
        if isinstance(value, dict):
            result = find_tag(value, tag)
            if result is not None:
                return result

    return None


def find_all_tags(tlv_dict: Dict[str, Any], tag: str) -> List[Union[bytes, Dict]]:
    """Find all occurrences of a tag in parsed TLV.

    Args:
        tlv_dict: Parsed TLV dictionary
        tag: Tag to find

    Returns:
        List of values for the tag.
    """
    tag_upper = tag.upper()
    results = []

    # Direct matches
    if tag_upper in tlv_dict:
        results.append(tlv_dict[tag_upper])

    # Search in constructed tags
    for value in tlv_dict.values():
        if isinstance(value, dict):
            results.extend(find_all_tags(value, tag))

    return results


def build_tlv(tag: str, value: bytes) -> bytes:
    """Build TLV encoded bytes from tag and value.

    Args:
        tag: Tag as hex string
        value: Value bytes

    Returns:
        TLV encoded bytes.
    """
    tag_bytes = bytes.fromhex(tag)
    length_bytes = _build_length(len(value))
    return tag_bytes + length_bytes + value


def _build_length(length: int) -> bytes:
    """Build length bytes for TLV encoding.

    Args:
        length: Length value

    Returns:
        Length bytes.
    """
    if length < 128:
        return bytes([length])
    else:
        # Calculate number of bytes needed
        length_bytes = []
        temp = length
        while temp > 0:
            length_bytes.insert(0, temp & 0xFF)
            temp >>= 8

        # First byte: 0x80 | number of length bytes
        return bytes([0x80 | len(length_bytes)] + length_bytes)