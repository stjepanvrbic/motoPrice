"""
Tests for base scraper framework.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from src.scrapers.base import BaseScraper, RateLimiter, retryWithBackoff
from src.utils.exceptions import RateLimitError, RequestTimeoutError, ScraperError


class ConcreteScraper(BaseScraper):
    """Concrete implementation for testing."""

    def scrape(self, **kwargs):
        """Test implementation."""
        return [{"test": "data"}]


def testRetryDecoratorSuccess():
    """Retry decorator returns result on success."""
    call_count = 0

    @retryWithBackoff(max_retries=3)
    def successFunc():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successFunc()
    assert result == "success"
    assert call_count == 1


def testRetryDecoratorRetries():
    """Retry decorator retries on failure."""
    call_count = 0

    @retryWithBackoff(max_retries=3, base_delay=0.01)
    def failThenSucceed():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ScraperError("Temporary failure")
        return "success"

    result = failThenSucceed()
    assert result == "success"
    assert call_count == 3


def testRetryDecoratorMaxRetriesExceeded():
    """Retry decorator raises after max retries."""
    call_count = 0

    @retryWithBackoff(max_retries=2, base_delay=0.01)
    def alwaysFails():
        nonlocal call_count
        call_count += 1
        raise ScraperError("Permanent failure")

    with pytest.raises(ScraperError):
        alwaysFails()

    assert call_count == 3  # Initial + 2 retries


def testRetryDecoratorNonRetryableError():
    """Retry decorator doesn't retry non-retryable errors."""
    call_count = 0

    @retryWithBackoff(max_retries=3, base_delay=0.01)
    def nonRetryableError():
        nonlocal call_count
        call_count += 1
        from src.utils.exceptions import ValidationError

        raise ValidationError("Not retryable")

    from src.utils.exceptions import ValidationError

    with pytest.raises(ValidationError, match="Not retryable"):
        nonRetryableError()

    assert call_count == 1  # No retries


def testRetryDecoratorExponentialBackoff():
    """Retry decorator uses exponential backoff."""
    call_times = []

    @retryWithBackoff(max_retries=3, base_delay=0.1, max_delay=1.0)
    def recordTimes():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise ScraperError("Retry me")
        return "done"

    recordTimes()

    # Verify increasing delays between calls
    assert len(call_times) == 3
    delay1 = call_times[1] - call_times[0]
    delay2 = call_times[2] - call_times[1]
    assert delay1 >= 0.1  # First delay ~0.1s
    assert delay2 >= 0.2  # Second delay ~0.2s (doubled)
    assert delay2 > delay1  # Exponential increase


def testRateLimiterBasic():
    """Rate limiter enforces minimum interval."""
    limiter = RateLimiter(requests_per_second=10.0)  # 0.1s interval

    start = time.time()
    limiter.wait()
    limiter.wait()
    limiter.wait()
    elapsed = time.time() - start

    # Should take at least 0.2s (2 intervals)
    assert elapsed >= 0.2


def testRateLimiterInitialRequest():
    """Rate limiter doesn't delay first request."""
    limiter = RateLimiter(requests_per_second=1.0)

    start = time.time()
    limiter.wait()
    elapsed = time.time() - start

    # First request should be immediate
    assert elapsed < 0.05


def testBaseScraperInitialization():
    """BaseScraper initializes correctly."""
    scraper = ConcreteScraper("test_source")

    assert scraper.source_name == "test_source"
    assert scraper.session is not None
    assert scraper.ua is not None
    assert scraper.rate_limiter is not None

    scraper.close()


def testBaseScraperGetHeaders():
    """BaseScraper generates headers with random user agent."""
    scraper = ConcreteScraper("test_source")

    headers1 = scraper.getHeaders()
    headers2 = scraper.getHeaders()

    # Headers should contain required fields
    assert "User-Agent" in headers1
    assert "Accept" in headers1
    assert "Connection" in headers1

    # User-Agent should rotate (might be same by chance, so we just check it exists)
    assert len(headers1["User-Agent"]) > 0
    assert len(headers2["User-Agent"]) > 0

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestSuccess(mock_request):
    """makeRequest returns response on success."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_request.return_value = mock_response

    scraper = ConcreteScraper("test_source")
    response = scraper.makeRequest("https://example.com")

    assert response.status_code == 200
    mock_request.assert_called_once()

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestRateLimit(mock_request):
    """makeRequest raises RateLimitError on 429."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "30"}
    mock_request.return_value = mock_response

    scraper = ConcreteScraper("test_source")

    with pytest.raises(RateLimitError) as exc_info:
        scraper.makeRequest("https://example.com")

    assert exc_info.value.retryable is True
    assert "retry_after" in exc_info.value.context

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestTimeout(mock_request):
    """makeRequest raises RequestTimeoutError on timeout."""
    mock_request.side_effect = requests.Timeout("Connection timeout")

    scraper = ConcreteScraper("test_source")

    with pytest.raises(RequestTimeoutError) as exc_info:
        scraper.makeRequest("https://example.com")

    assert exc_info.value.retryable is True
    assert "url" in exc_info.value.context

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestNetworkError(mock_request):
    """makeRequest raises ScraperError on network error."""
    mock_request.side_effect = requests.ConnectionError("Network unreachable")

    scraper = ConcreteScraper("test_source")

    with pytest.raises(ScraperError) as exc_info:
        scraper.makeRequest("https://example.com")

    assert exc_info.value.retryable is True

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestWithCustomHeaders(mock_request):
    """makeRequest uses custom headers if provided."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_request.return_value = mock_response

    scraper = ConcreteScraper("test_source")
    custom_headers = {"Custom-Header": "value"}

    scraper.makeRequest("https://example.com", headers=custom_headers)

    # Verify custom headers were used
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs["headers"] == custom_headers

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestWithTimeout(mock_request):
    """makeRequest respects timeout configuration."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_request.return_value = mock_response

    scraper = ConcreteScraper("test_source")
    scraper.makeRequest("https://example.com")

    # Verify timeout was set from config
    call_kwargs = mock_request.call_args[1]
    assert "timeout" in call_kwargs
    assert call_kwargs["timeout"] == scraper.config.scraping.timeout

    scraper.close()


def testScraperContextManager():
    """BaseScraper works as context manager."""
    with ConcreteScraper("test_source") as scraper:
        assert scraper.session is not None

    # Session should be closed after context
    # (Can't easily test this without accessing private session state)


def testScraperAbstractMethod():
    """BaseScraper scrape() must be implemented."""
    # This is enforced by ABC, verify ConcreteScraper implements it
    scraper = ConcreteScraper("test_source")
    result = scraper.scrape()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == {"test": "data"}

    scraper.close()


@patch("requests.Session.request")
def testMakeRequestRetries(mock_request):
    """makeRequest retries on retryable errors."""
    # First call fails, second succeeds
    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = Mock()

    mock_request.side_effect = [
        requests.ConnectionError("Temporary failure"),
        mock_response_success,
    ]

    scraper = ConcreteScraper("test_source")
    response = scraper.makeRequest("https://example.com")

    assert response.status_code == 200
    assert mock_request.call_count == 2  # Initial + 1 retry

    scraper.close()


def testRateLimiterDifferentRates():
    """Rate limiter works with different rates."""
    # Fast rate
    fast_limiter = RateLimiter(requests_per_second=100.0)  # 0.01s interval
    start = time.time()
    fast_limiter.wait()
    fast_limiter.wait()
    fast_elapsed = time.time() - start
    assert fast_elapsed < 0.05  # Very quick

    # Slow rate
    slow_limiter = RateLimiter(requests_per_second=2.0)  # 0.5s interval
    start = time.time()
    slow_limiter.wait()
    slow_limiter.wait()
    slow_elapsed = time.time() - start
    assert slow_elapsed >= 0.5  # At least one interval
