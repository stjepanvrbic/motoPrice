"""
Logging setup for motoPrice using loguru.
"""

import sys
from pathlib import Path

from loguru import logger

from .config import getConfig

# Remove default logger
logger.remove()

_initialized = False


def setupLogging():
    """
    Configure logging based on application config.

    Sets up console and file logging with rotation.
    """
    global _initialized
    if _initialized:
        return

    config = getConfig()
    log_config = config.logging

    # Console logging
    if log_config.console:
        logger.add(
            sys.stderr,
            format=log_config.format,
            level=log_config.level,
            colorize=True,
        )

    # File logging with rotation
    log_file = Path(log_config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_file),  # Convert to string for loguru
        format=log_config.format,
        level=log_config.level,
        rotation=log_config.rotation,
        retention=log_config.retention,
        compression="zip",
    )

    _initialized = True
    logger.info("Logging initialized")


def getLogger(name: str):
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if not _initialized:
        setupLogging()

    return logger.bind(name=name)
