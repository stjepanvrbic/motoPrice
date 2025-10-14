"""
Tests for custom exception hierarchy.
"""

from src.utils.exceptions import (
    APIError,
    ConfigurationError,
    DatabaseError,
    MotoPriceError,
    ParseError,
    RateLimitError,
    RequestTimeoutError,
    ScraperError,
    ValidationError,
    logError,
)


def testMotoPriceErrorBase():
    """Base exception has message and context."""
    error = MotoPriceError("Test error", retryable=True, key="value")

    assert str(error) == "Test error (key=value)"
    assert error.message == "Test error"
    assert error.retryable is True
    assert error.context == {"key": "value"}


def testMotoPriceErrorNoContext():
    """Base exception without context."""
    error = MotoPriceError("Simple error")

    assert str(error) == "Simple error"
    assert error.message == "Simple error"
    assert error.retryable is False
    assert error.context == {}


def testConfigurationErrorNotRetryable():
    """Configuration errors are not retryable."""
    error = ConfigurationError("Missing config", setting="DATABASE_URL")

    assert error.message == "Missing config"
    assert error.retryable is False
    assert error.context == {"setting": "DATABASE_URL"}
    assert isinstance(error, MotoPriceError)


def testDatabaseErrorRetryable():
    """Database errors are retryable by default."""
    error = DatabaseError("Connection failed", host="localhost")

    assert error.message == "Connection failed"
    assert error.retryable is True
    assert error.context == {"host": "localhost"}
    assert isinstance(error, MotoPriceError)


def testDatabaseErrorFatal():
    """Database errors can be marked as fatal."""
    error = DatabaseError("Schema mismatch", retryable=False, table="listings")

    assert error.retryable is False
    assert error.context == {"table": "listings"}


def testScraperErrorRetryable():
    """Scraper errors are retryable by default."""
    error = ScraperError("Request failed", url="https://example.com", status_code=503)

    assert error.message == "Request failed"
    assert error.retryable is True
    assert error.context == {"url": "https://example.com", "status_code": 503}
    assert isinstance(error, MotoPriceError)


def testScraperErrorFatal():
    """Scraper errors can be marked as fatal."""
    error = ScraperError("Invalid URL", retryable=False, url="invalid")

    assert error.retryable is False


def testValidationErrorNotRetryable():
    """Validation errors are not retryable."""
    error = ValidationError("Invalid price", field="price", value="-100")

    assert error.message == "Invalid price"
    assert error.retryable is False
    assert error.context == {"field": "price", "value": "-100"}
    assert isinstance(error, MotoPriceError)


def testAPIErrorRetryable():
    """API errors are retryable by default."""
    error = APIError("API timeout", endpoint="/api/v1/listings", status_code=504)

    assert error.message == "API timeout"
    assert error.retryable is True
    assert error.context == {"endpoint": "/api/v1/listings", "status_code": 504}
    assert isinstance(error, MotoPriceError)


def testAPIErrorFatal():
    """API errors can be marked as fatal."""
    error = APIError("Invalid API key", retryable=False)

    assert error.retryable is False


def testRateLimitError():
    """Rate limit errors are retryable."""
    error = RateLimitError(retry_after=60)

    assert error.message == "Rate limit exceeded"
    assert error.retryable is True
    assert error.context == {"retry_after": 60}
    assert isinstance(error, ScraperError)
    assert isinstance(error, MotoPriceError)


def testRequestTimeoutError():
    """Timeout errors are retryable."""
    error = RequestTimeoutError(url="https://example.com", timeout=30)

    assert error.message == "Request timed out"
    assert error.retryable is True
    assert error.context == {"url": "https://example.com", "timeout": 30}
    assert isinstance(error, ScraperError)


def testParseErrorNotRetryable():
    """Parse errors are not retryable."""
    error = ParseError("Missing selector", url="https://example.com", selector=".price")

    assert error.message == "Missing selector"
    assert error.retryable is False
    assert error.context == {"url": "https://example.com", "selector": ".price"}
    assert isinstance(error, ScraperError)


def testExceptionHierarchy():
    """Verify exception inheritance."""
    config_error = ConfigurationError("test")
    db_error = DatabaseError("test")
    scraper_error = ScraperError("test")
    validation_error = ValidationError("test")
    api_error = APIError("test")
    rate_limit_error = RateLimitError()
    timeout_error = RequestTimeoutError()
    parse_error = ParseError("test")

    # All inherit from MotoPriceError
    assert isinstance(config_error, MotoPriceError)
    assert isinstance(db_error, MotoPriceError)
    assert isinstance(scraper_error, MotoPriceError)
    assert isinstance(validation_error, MotoPriceError)
    assert isinstance(api_error, MotoPriceError)

    # Specific scraper errors inherit from ScraperError
    assert isinstance(rate_limit_error, ScraperError)
    assert isinstance(timeout_error, ScraperError)
    assert isinstance(parse_error, ScraperError)


def testLogErrorWithCustomException():
    """logError logs custom exceptions without errors."""
    error = ScraperError("Request failed", url="https://example.com", status_code=503)
    # Should not raise any exceptions
    logError(error)


def testLogErrorWithStandardException():
    """logError logs standard Python exceptions without errors."""
    error = ValueError("Invalid value")
    # Should not raise any exceptions
    logError(error)


def testLogErrorWithLevel():
    """logError respects different log levels."""
    error = MotoPriceError("Test message")
    # Should not raise any exceptions with different levels
    logError(error, level="debug")
    logError(error, level="info")
    logError(error, level="warning")
    logError(error, level="error")
    logError(error, level="critical")


def testContextInStringRepresentation():
    """Error string includes all context."""
    error = DatabaseError("Query failed", query="SELECT *", table="listings", timeout=30)

    error_str = str(error)
    assert "Query failed" in error_str
    assert "query=SELECT *" in error_str
    assert "table=listings" in error_str
    assert "timeout=30" in error_str


def testMultipleContextItems():
    """Errors can have multiple context items."""
    error = ScraperError(
        "Complex error",
        url="https://example.com",
        status_code=500,
        attempt=3,
        max_retries=5,
    )

    assert error.context["url"] == "https://example.com"
    assert error.context["status_code"] == 500
    assert error.context["attempt"] == 3
    assert error.context["max_retries"] == 5
    assert len(error.context) == 4
