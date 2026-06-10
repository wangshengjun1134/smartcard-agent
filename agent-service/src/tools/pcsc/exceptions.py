"""PCSC exceptions for smart card reader operations.

This module defines exceptions for PCSC-related errors.
"""


class PcscError(Exception):
    """Base exception for PCSC operations."""

    pass


class ReaderNotFoundError(PcscError):
    """No smart card reader available."""

    def __init__(self, message: str = "No smart card reader found"):
        super().__init__(message)


class CardNotFoundError(PcscError):
    """No card present in the reader."""

    def __init__(self, reader_name: str = ""):
        message = f"No card present in reader: {reader_name}" if reader_name else "No card present"
        super().__init__(message)


class ConnectionLostError(PcscError):
    """Connection to card lost during operation."""

    def __init__(self, message: str = "Connection to card lost"):
        super().__init__(message)


class APDUError(PcscError):
    """APDU command execution failed.

    Attributes:
        sw: Status word from the failed APDU
        description: Description of the error
    """

    def __init__(self, sw: str, description: str = ""):
        self.sw = sw
        self.description = description or f"APDU failed with SW={sw}"
        super().__init__(self.description)


class SecureChannelError(PcscError):
    """Secure channel operation failed."""

    def __init__(self, message: str = "Secure channel operation failed"):
        super().__init__(message)


class PinVerificationError(PcscError):
    """PIN verification failed.

    Attributes:
        retry_count: Remaining retry attempts
    """

    def __init__(self, retry_count: int = 0):
        self.retry_count = retry_count
        message = f"PIN verification failed, {retry_count} retries remaining"
        super().__init__(message)


class CardBlockedError(PcscError):
    """Card is blocked (PIN locked or permanently disabled)."""

    def __init__(self, message: str = "Card is blocked"):
        super().__init__(message)


class UnsupportedCardError(PcscError):
    """Card type not supported by the operation."""

    def __init__(self, card_type: str = ""):
        message = f"Unsupported card type: {card_type}" if card_type else "Unsupported card type"
        super().__init__(message)


class TimeoutError(PcscError):
    """Operation timed out."""

    def __init__(self, operation: str = ""):
        message = f"Operation timed out: {operation}" if operation else "Operation timed out"
        super().__init__(message)