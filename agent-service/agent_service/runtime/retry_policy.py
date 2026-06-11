"""Retry Policy for smart card operations.

This module defines retry policies for handling transient errors
during card operations.
"""

from typing import List, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class RetryAction(Enum):
    """Action to take when retryable error occurs."""

    RETRY = "retry"
    RECONNECT = "reconnect"
    SKIP = "skip"
    ABORT = "abort"


@dataclass
class RetryPolicy:
    """Retry policy configuration.

    Attributes:
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
        retryable_sw: List of SW codes that can be retried
        retryable_exceptions: List of exception types that can be retried
        on_retry: Callback function called before retry
    """

    max_retries: int = 3
    retry_delay: float = 0.5
    retryable_sw: List[str] = None  # Default: ["6F00", "6FFF"]
    retryable_exceptions: List[str] = None  # Default: ["ConnectionLostError", "TimeoutError"]
    on_retry: Optional[Callable] = None

    def __post_init__(self):
        """Set defaults after initialization."""
        if self.retryable_sw is None:
            self.retryable_sw = ["6F00", "6FFF"]
        if self.retryable_exceptions is None:
            self.retryable_exceptions = ["ConnectionLostError", "TimeoutError"]

    def is_retryable_sw(self, sw: str) -> bool:
        """Check if SW code is retryable.

        Args:
            sw: Status word string

        Returns:
            True if the SW indicates a retryable error.
        """
        # Exact match
        if sw in self.retryable_sw:
            return True

        # Pattern match for dynamic SW
        sw_prefix = sw[:2]
        for retry_sw in self.retryable_sw:
            if retry_sw.endswith("XX") and retry_sw[:2] == sw_prefix:
                return True

        return False

    def is_retryable_exception(self, exception_name: str) -> bool:
        """Check if exception type is retryable.

        Args:
            exception_name: Exception class name

        Returns:
            True if the exception is retryable.
        """
        return exception_name in self.retryable_exceptions

    def get_retry_action(self, error: Any) -> RetryAction:
        """Determine retry action for an error.

        Args:
            error: Error object (APDUError or exception)

        Returns:
            RetryAction to take.
        """
        # Check if it's an APDU error
        if hasattr(error, "sw"):
            if error.sw == "6FFF":
                # Card mute - need reconnect
                return RetryAction.RECONNECT
            elif self.is_retryable_sw(error.sw):
                return RetryAction.RETRY

        # Check if it's an exception
        error_type = type(error).__name__
        if error_type == "ConnectionLostError":
            return RetryAction.RECONNECT
        elif error_type == "TimeoutError":
            return RetryAction.RETRY
        elif self.is_retryable_exception(error_type):
            return RetryAction.RETRY

        # Not retryable
        return RetryAction.ABORT


# Default retry policies
DEFAULT_RETRY_POLICY = RetryPolicy(
    max_retries=3,
    retry_delay=0.5,
)

AGGRESSIVE_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    retry_delay=0.1,
)

NO_RETRY_POLICY = RetryPolicy(
    max_retries=0,
    retry_delay=0.0,
    retryable_sw=[],
    retryable_exceptions=[],
)


class RetryEngine:
    """Engine for handling retries during card operations.

    Example:
        engine = RetryEngine(DEFAULT_RETRY_POLICY)
        result = engine.execute_with_retry(lambda: client.send_apdu(apdu))
    """

    def __init__(self, policy: RetryPolicy = DEFAULT_RETRY_POLICY):
        """Initialize retry engine.

        Args:
            policy: Retry policy to use
        """
        self.policy = policy
        self.retry_count = 0
        self.last_error: Optional[Any] = None

    def execute_with_retry(
        self,
        operation: Callable,
        on_reconnect: Optional[Callable] = None,
        on_retry: Optional[Callable] = None,
    ) -> Any:
        """Execute an operation with retry handling.

        Args:
            operation: Function to execute
            on_reconnect: Callback for reconnect action
            on_retry: Callback before retry

        Returns:
            Result of the operation.

        Raises:
            Last error if all retries exhausted.
        """
        self.retry_count = 0
        self.last_error = None

        while True:
            try:
                result = operation()
                # Success - reset state
                self.retry_count = 0
                self.last_error = None
                return result

            except Exception as e:
                self.last_error = e
                action = self.policy.get_retry_action(e)

                if action == RetryAction.ABORT:
                    raise e

                self.retry_count += 1
                if self.retry_count > self.policy.max_retries:
                    raise e

                # Callback
                if on_retry:
                    on_retry(self.retry_count, e)
                elif self.policy.on_retry:
                    self.policy.on_retry(self.retry_count, e)

                # Handle action
                if action == RetryAction.RECONNECT:
                    if on_reconnect:
                        on_reconnect()

                # Delay before retry
                import time
                time.sleep(self.policy.retry_delay)

    def get_retry_count(self) -> int:
        """Get current retry count.

        Returns:
            Number of retries attempted.
        """
        return self.retry_count

    def reset(self) -> None:
        """Reset retry state."""
        self.retry_count = 0
        self.last_error = None