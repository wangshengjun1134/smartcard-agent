"""Status Word (SW) codes mapping for ISO 7816.

This module defines the meaning of APDU response status words (SW1-SW2).
"""

from typing import Dict


# Normal completion
SW_NORMAL = "9000"
SW_NORMAL_WITH_DATA = "61XX"  # XX bytes available

# Warning conditions
SW_WARNING_CORRUPTED_DATA = "6281"
SW_WARNING_RETURN_DATA_TRUNCATED = "6282"
SW_WARNING_FILE_EOF_REACHED = "6283"
SW_WARNING_SELECTED_FILE_INVALIDATED = "6284"
SW_WARNING_FCI_FORMAT_INVALID = "6285"
SW_WARNING_MORE_DATA_AVAILABLE = "61"

# Execution errors
SW_ERROR_WRONG_LENGTH = "6700"
SW_ERROR_CLA_NOT_SUPPORTED = "6800"
SW_ERROR_INS_NOT_SUPPORTED = "6900"
SW_ERROR_COMMAND_INCOMPATIBLE = "6A00"
SW_ERROR_P1_P2_WRONG = "6B00"
SW_ERROR_DATA_FIELD_WRONG = "6D00"
SW_ERROR_FUNCTION_NOT_SUPPORTED = "6E00"

# Security errors
SW_SECURITY_CONDITION_NOT_SATISFIED = "6982"
SW_SECURITY_AUTH_METHOD_BLOCKED = "6983"
SW_SECURITY_KEY_EXPIRED = "6984"
SW_SECURITY_REFERENCE_DATA_NOT_FOUND = "6A88"
SW_SECURITY_WRONG_PIN = "63CX"  # C = retry counter

# File errors
SW_FILE_NOT_FOUND = "6A82"
SW_RECORD_NOT_FOUND = "6A83"
SW_FILE_EXISTS = "6A84"
SW_INSUFFICIENT_MEMORY = "6A85"

# Other errors
SW_UNKNOWN_ERROR = "6F00"
SW_CARD_MUTE = "6FFF"


# SW code to description mapping
SW_DESCRIPTIONS: Dict[str, str] = {
    "9000": "正常完成",
    "61": "有数据可返回，使用 GET RESPONSE 获取",
    "6281": "数据已损坏",
    "6282": "返回数据被截断",
    "6283": "已到达文件末尾",
    "6284": "选定的文件已被无效化",
    "6285": "FCI 格式无效",
    "6700": "错误的长度",
    "6800": "CLA 不支持",
    "6900": "INS 不支持",
    "6982": "安全条件不满足",
    "6983": "认证方法被阻塞",
    "6984": "密钥已过期",
    "6A00": "命令与文件结构不兼容",
    "6A82": "文件未找到",
    "6A83": "记录未找到",
    "6A84": "文件已存在",
    "6A85": "内存不足",
    "6A88": "引用数据未找到",
    "6F00": "未知错误",
    "6FFF": "卡片无响应",
}


def decode_sw(sw: str) -> str:
    """Decode Status Word to its description.

    Args:
        sw: Two-byte status word as hex string (e.g., "9000", "6982")

    Returns:
        Description of the status word meaning.
    """
    # Exact match
    if sw in SW_DESCRIPTIONS:
        return SW_DESCRIPTIONS[sw]

    # Pattern match for dynamic SW codes
    sw1 = sw[:2] if len(sw) >= 2 else ""

    if sw1 == "61":
        length = int(sw[2:4], 16) if len(sw) >= 4 else 0
        return f"正常完成，有 {length} 字节可返回"

    if sw1 == "63":
        retry_count = int(sw[2:4], 16) & 0x0F if len(sw) >= 4 else 0
        return f"PIN 错误，剩余 {retry_count} 次重试"

    if sw.upper() == "6100":
        return "无数据可返回"

    return f"未知状态码: {sw}"


def is_success(sw: str) -> bool:
    """Check if status word indicates success.

    Args:
        sw: Status word string

    Returns:
        True if the operation was successful.
    """
    return sw == "9000" or sw.startswith("61")


def is_retryable(sw: str) -> bool:
    """Check if the error is potentially retryable.

    Args:
        sw: Status word string

    Returns:
        True if the error might succeed on retry.
    """
    retryable_codes = [
        "6F00",  # Unknown error - might be transient
        "6FFF",  # Card mute - might recover after reset
    ]
    return sw in retryable_codes


def needs_get_response(sw: str) -> bool:
    """Check if GET RESPONSE should be issued.

    Args:
        sw: Status word string

    Returns:
        True if GET RESPONSE is needed to retrieve data.
    """
    return sw.startswith("61")


def get_response_length(sw: str) -> int:
    """Get the expected length for GET RESPONSE.

    Args:
        sw: Status word string (61XX)

    Returns:
        Number of bytes to retrieve.
    """
    if sw.startswith("61") and len(sw) >= 4:
        return int(sw[2:4], 16)
    return 0