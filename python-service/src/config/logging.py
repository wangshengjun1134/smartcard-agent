"""Logging configuration.

This module sets up application logging.
"""

import logging
import sys
from typing import Optional

from config.settings import get_settings


def setup_logging(
    level: Optional[str] = None,
    format_str: Optional[str] = None,
) -> None:
    """Setup application logging.

    Args:
        level: Log level override (default: from settings)
        format_str: Format string override (default: from settings)
    """
    settings = get_settings()

    log_level = level or settings.LOG_LEVEL
    log_format = format_str or settings.LOG_FORMAT

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set specific logger levels
    logging.getLogger("smartcard").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)