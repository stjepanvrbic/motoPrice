"""
Custom exception hierarchy for motoPrice.

All application-specific exceptions inherit from MotoPriceError.
Exceptions are categorized as either retryable or fatal to guide error handling.
"""

import traceback
from typing import Any

from loguru import logger


class MotoPriceError(Exception):
    """Base exception for all motoPrice errors."""

    def __init__(self, message: str, retryable: bool = False, **context: Any):
        """
        Initialize error with message and context.

        Args:
            message: Error description
            retryable: Whether this error is retryable
            **context: Additional context for debugging
        """
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        self.context = context

    def __str__(self) -> str:
        """String representation including context."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class ConfigurationError(MotoPriceError):
    """Configuration or setup error."""

    def __init__(self, message: str, **context: Any):
        """
        Initialize configuration error.

        Args:
            message: Error description
            **context: Additional context
        """
        super().__init__(message, retryable=False, **context)


class DatabaseError(MotoPriceError):
    """Database operation error."""

    def __init__(self, message: str, retryable: bool = True, **context: Any):
        """
        Initialize database error.

        Args:
            message: Error description
            retryable: Whether operation can be retried (default True)
            **context: Additional context
        """
        super().__init__(message, retryable=retryable, **context)


class ScraperError(MotoPriceError):
    """Web scraping error."""

    def __init__(self, message: str, retryable: bool = True, **context: Any):
        """
        Initialize scraper error.

        Args:
            message: Error description
            retryable: Whether request can be retried (default True)
            **context: Additional context (url, status_code, etc.)
        """
        super().__init__(message, retryable=retryable, **context)


class ValidationError(MotoPriceError):
    """Data validation error."""

    def __init__(self, message: str, **context: Any):
        """
        Initialize validation error.

        Args:
            message: Error description
            **context: Additional context (field, value, etc.)
        """
        super().__init__(message, retryable=False, **context)


class APIError(MotoPriceError):
    """External API error."""

    def __init__(self, message: str, retryable: bool = True, **context: Any):
        """
        Initialize API error.

        Args:
            message: Error description
            retryable: Whether API call can be retried (default True)
            **context: Additional context (endpoint, status_code, etc.)
        """
        super().__init__(message, retryable=retryable, **context)


class RateLimitError(ScraperError):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", **context: Any):
        """
        Initialize rate limit error.

        Args:
            message: Error description
            **context: Additional context (retry_after, etc.)
        """
        super().__init__(message, retryable=True, **context)


class RequestTimeoutError(ScraperError):
    """Request timeout error."""

    def __init__(self, message: str = "Request timed out", **context: Any):
        """
        Initialize timeout error.

        Args:
            message: Error description
            **context: Additional context (url, timeout, etc.)
        """
        super().__init__(message, retryable=True, **context)


class ParseError(ScraperError):
    """HTML/JSON parsing error."""

    def __init__(self, message: str, **context: Any):
        """
        Initialize parse error.

        Args:
            message: Error description
            **context: Additional context (url, selector, etc.)
        """
        super().__init__(message, retryable=False, **context)


def logError(error: Exception, level: str = "error") -> None:
    """
    Log an error with appropriate level and context.

    Args:
        error: Exception to log
        level: Log level (debug, info, warning, error, critical)
    """
    log_func = getattr(logger, level, logger.error)

    if isinstance(error, MotoPriceError):
        # Log custom errors with context
        context_str = ""
        if error.context:
            context_str = " | ".join(f"{k}={v}" for k, v in error.context.items())

        retryable_str = "retryable" if error.retryable else "fatal"
        log_func(
            f"[{retryable_str}] {error.message}" + (f" | {context_str}" if context_str else "")
        )
    else:
        # Log standard Python exceptions
        log_func(f"{type(error).__name__}: {str(error)}")

    # Log traceback at debug level
    if level in ("error", "critical"):
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
