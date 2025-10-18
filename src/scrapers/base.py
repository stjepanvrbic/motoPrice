"""
Base scraper framework with retry logic, rate limiting, and error handling.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Any

import requests
from fake_useragent import UserAgent

from src.utils.config import getConfig
from src.utils.exceptions import RateLimitError, RequestTimeoutError, ScraperError, logError
from src.utils.logger import getLogger

logger = getLogger(__name__)


def retryWithBackoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Decorated function that retries on failure
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1

                    # Don't retry if error is not retryable
                    if hasattr(e, "retryable") and not e.retryable:
                        logError(e)
                        raise

                    # Max retries exceeded
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        logError(e)
                        raise

                    # Log retry attempt
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after {delay}s - {type(e).__name__}: {str(e)}"
                    )

                    # Wait with exponential backoff
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)

            return None

        return wrapper

    return decorator


class RateLimiter:
    """Rate limiter to prevent exceeding request limits."""

    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: float | None = None

    def wait(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        self.last_request_time = time.time()


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, source_name: str):
        """
        Initialize scraper.

        Args:
            source_name: Name of the scraping source
        """
        self.source_name = source_name
        self.logger = getLogger(f"scraper.{source_name}")
        self.config = getConfig()

        # Initialize session
        self.session = requests.Session()

        # Initialize user agent rotation
        self.ua = UserAgent()

        # Initialize rate limiter
        requests_per_second = 1.0 / self.config.scraping.delay_between_requests
        self.rate_limiter = RateLimiter(requests_per_second)

        self.logger.info(f"Initialized {source_name} scraper")

    def getHeaders(self) -> dict[str, str]:
        """
        Get request headers with rotated user agent.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    @retryWithBackoff(max_retries=3)
    def makeRequest(self, url: str, method: str = "GET", **kwargs: Any) -> requests.Response:
        """
        Make HTTP request with retry logic and rate limiting.

        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            ScraperError: On request failure
            RequestTimeoutError: On timeout
            RateLimitError: On rate limit
        """
        # Apply rate limiting
        self.rate_limiter.wait()

        # Set headers if not provided
        if "headers" not in kwargs:
            kwargs["headers"] = self.getHeaders()

        # Set timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.config.scraping.timeout

        try:
            self.logger.debug(f"{method} {url}")
            response = self.session.request(method, url, **kwargs)

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    f"Rate limited by {self.source_name}",
                    url=url,
                    retry_after=retry_after,
                    status_code=429,
                )

            # Raise for bad status codes
            response.raise_for_status()

            return response

        except requests.Timeout as e:
            raise RequestTimeoutError(
                f"Request to {url} timed out", url=url, timeout=kwargs.get("timeout")
            ) from e

        except requests.RequestException as e:
            status_code = e.response.status_code if hasattr(e, "response") and e.response else None
            raise ScraperError(
                f"Request to {url} failed: {str(e)}", url=url, status_code=status_code
            ) from e

    @abstractmethod
    def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Scrape data from source.

        Args:
            **kwargs: Source-specific arguments

        Returns:
            List of scraped data dictionaries

        Raises:
            ScraperError: On scraping failure
        """
        pass

    def close(self):
        """Close session and cleanup resources."""
        self.session.close()
        self.logger.info(f"Closed {self.source_name} scraper")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
