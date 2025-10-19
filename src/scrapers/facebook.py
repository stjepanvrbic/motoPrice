"""
Facebook Marketplace scraper using Playwright for browser automation.

Facebook Marketplace has less structured data than CycleTrader, so this scraper
uses more flexible parsing with fuzzy matching and fallback strategies.
"""

import random
import re
import time
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from src.scrapers.base import BaseScraper
from src.utils.exceptions import ScraperError
from src.utils.logger import getLogger

logger = getLogger(__name__)


class FacebookMarketplaceScraper(BaseScraper):
    """Facebook Marketplace scraper using Playwright."""

    BASE_URL = "https://www.facebook.com/marketplace"

    def __init__(self):
        """Initialize Facebook Marketplace scraper."""
        super().__init__("facebook")
        self.playwright = None
        self.browser = None
        self.context = None
        self.source = self.source_name  # Alias for consistency with tests

    def _launchBrowser(self):
        """Launch Playwright browser with anti-detection measures."""
        if self.browser is None:
            self.playwright = sync_playwright().start()

            # Launch browser with anti-detection args
            # Facebook requires non-headless mode for initial development
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Create context with realistic browser fingerprint
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
            )

            # Inject anti-detection script
            self.context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
            )

    def _closeBrowser(self):
        """Close browser and cleanup resources."""
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def __enter__(self):
        """Context manager entry."""
        self._launchBrowser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._closeBrowser()
        return False

    def buildSearchUrl(
        self,
        query: str | None = None,
        make: str | None = None,
        model: str | None = None,
        minPrice: int | None = None,
        maxPrice: int | None = None,
        location: str | None = None,
        radius: int | None = 50,
    ) -> str:
        """
        Build Facebook Marketplace search URL.

        Args:
            query: Search query (e.g., "Ducati Panigale V4")
            make: Motorcycle make
            model: Motorcycle model
            minPrice: Minimum price filter
            maxPrice: Maximum price filter
            location: Location for search (city, state, or ZIP)
            radius: Search radius in miles (default: 50)

        Returns:
            Complete search URL
        """
        # Build query string from make/model if not provided
        if not query and (make or model):
            parts = []
            if make:
                parts.append(make)
            if model:
                parts.append(model)
            query = " ".join(parts)

        if not query:
            raise ValueError("Either query or make/model must be provided")

        # Start with category for motorcycles
        # Facebook uses numeric category IDs - 807311116002614 is for motorcycles
        url = f"{self.BASE_URL}/category/motorcycles"

        # Add search query and filters
        params = {"query": query}

        if minPrice:
            params["minPrice"] = str(minPrice)
        if maxPrice:
            params["maxPrice"] = str(maxPrice)

        if location:
            # Facebook uses location differently - this is simplified
            params["location"] = location
        if radius:
            params["radius"] = str(radius)

        # Build final URL
        if params:
            url = f"{url}?{urlencode(params)}"

        return url

    def _simulateHumanBehavior(self, page):
        """
        Simulate human-like behavior to avoid detection.

        Args:
            page: Playwright page object
        """
        # Random mouse movements
        for _ in range(random.randint(1, 3)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.3))

        # Random scroll
        page.evaluate(f"window.scrollBy(0, {random.randint(100, 300)})")
        time.sleep(random.uniform(0.5, 1.5))

    def _scrollToLoadMore(self, page, scrolls: int = 3):
        """
        Scroll page to trigger infinite scroll and load more listings.

        Args:
            page: Playwright page object
            scrolls: Number of scroll iterations

        Returns:
            None
        """
        logger.info(f"Scrolling page {scrolls} times to load more listings")

        for i in range(scrolls):
            # Get current height
            previousHeight = page.evaluate("document.body.scrollHeight")

            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for content to load
            time.sleep(random.uniform(1.5, 2.5))

            # Check if new content loaded
            newHeight = page.evaluate("document.body.scrollHeight")
            if newHeight == previousHeight:
                logger.info(f"No new content loaded after scroll {i + 1}")
                break

            # Simulate human behavior
            self._simulateHumanBehavior(page)

    def _parsePrice(self, priceText: str) -> int | None:
        """
        Parse price from text.

        Args:
            priceText: Price text (e.g., "$15,000", "$15k")

        Returns:
            Price as integer or None if parsing fails
        """
        if not priceText:
            return None

        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r"[$,]", "", priceText.strip())

            # Handle "k" suffix (e.g., "15k" = 15000)
            if "k" in cleaned.lower():
                cleaned = cleaned.lower().replace("k", "")
                return int(float(cleaned) * 1000)

            # Try to extract first number
            match = re.search(r"\d+", cleaned)
            if match:
                return int(match.group())

            return None
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse price '{priceText}': {e}")
            return None

    def _parseMileage(self, mileageText: str) -> int | None:
        """
        Parse mileage from text.

        Args:
            mileageText: Mileage text (e.g., "5,000 mi", "5k miles")

        Returns:
            Mileage as integer or None if parsing fails
        """
        if not mileageText:
            return None

        try:
            # Remove commas
            cleaned = re.sub(r"[,]", "", mileageText.strip())

            # Handle "k" suffix first (before removing text)
            if "k" in cleaned.lower():
                # Extract number before 'k'
                match = re.search(r"(\d+(?:\.\d+)?)\s*k", cleaned, flags=re.IGNORECASE)
                if match:
                    return int(float(match.group(1)) * 1000)

            # Remove "mi" or "miles" etc.
            cleaned = re.sub(r"\s*(mi|miles|kilometers|km)\s*", "", cleaned, flags=re.IGNORECASE)

            # Extract first number
            match = re.search(r"\d+", cleaned)
            if match:
                return int(match.group())

            return None
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse mileage '{mileageText}': {e}")
            return None

    def _parseYear(self, text: str) -> int | None:
        """
        Parse year from text.

        Args:
            text: Text that may contain year (e.g., "2022 Ducati Panigale V4")

        Returns:
            Year as integer or None if parsing fails
        """
        if not text:
            return None

        try:
            # Look for 4-digit year (1900-2099)
            match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
            if match:
                return int(match.group(1))
            return None
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse year from '{text}': {e}")
            return None

    def _parseListingCard(self, cardElement) -> dict[str, Any] | None:
        """
        Parse a single listing card from search results.

        Facebook Marketplace has less structured data, so this uses
        flexible parsing with fallback strategies.

        Args:
            cardElement: BeautifulSoup element for listing card

        Returns:
            Dictionary with listing data or None if parsing fails
        """
        try:
            # Extract URL - Facebook uses data-testid for links
            linkElement = cardElement.find("a", href=True)
            if not linkElement:
                logger.debug("No link found in listing card")
                return None

            url = linkElement.get("href")
            if not url:
                return None

            # Make URL absolute
            if url.startswith("/"):
                url = f"https://www.facebook.com{url}"

            # Extract title - usually in span or div with specific classes
            titleElement = cardElement.find(
                "span", class_=re.compile(".*marketplace.*", re.IGNORECASE)
            )
            if not titleElement:
                # Fallback: try any span in the link
                titleElement = linkElement.find("span")

            title = titleElement.get_text(strip=True) if titleElement else None

            # Extract price - look for $ symbol
            priceElement = None
            for elem in cardElement.find_all(string=re.compile(r"\$\d+")):
                priceElement = elem
                break

            priceText = priceElement.strip() if priceElement else None
            price = self._parsePrice(priceText) if priceText else None

            # Extract location - often in separate div
            locationElement = cardElement.find(string=re.compile(r"[A-Z][a-z]+,\s*[A-Z]{2}"))
            location = locationElement.strip() if locationElement else None

            # Try to extract year from title
            year = self._parseYear(title) if title else None

            # Extract image URL
            imgElement = cardElement.find("img")
            imageUrl = imgElement.get("src") if imgElement else None

            return {
                "url": url,
                "title": title,
                "price": price,
                "year": year,
                "location": location,
                "imageUrl": imageUrl,
            }

        except Exception as e:
            logger.warning(f"Failed to parse listing card: {e}")
            return None

    def _parseSearchResults(self, html: str) -> list[dict[str, Any]]:
        """
        Parse search results page.

        Args:
            html: Page HTML

        Returns:
            List of listing dictionaries
        """
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        # Facebook Marketplace uses dynamic class names, so we need flexible selectors
        # Look for common patterns in listing cards
        cardSelectors = [
            {"role": "article"},  # Listings are often in article elements
            {"data-testid": re.compile(".*listing.*", re.IGNORECASE)},
            {"class": re.compile(".*listing.*card.*", re.IGNORECASE)},
        ]

        listingCards = []
        for selector in cardSelectors:
            cards = soup.find_all("div", selector)
            if cards:
                listingCards = cards
                logger.info(f"Found {len(cards)} listing cards using selector {selector}")
                break

        if not listingCards:
            logger.warning("No listing cards found in search results")
            return []

        for card in listingCards:
            listingData = self._parseListingCard(card)
            if listingData:
                listings.append(listingData)

        logger.info(f"Parsed {len(listings)} listings from search results")
        return listings

    def search(
        self,
        query: str | None = None,
        make: str | None = None,
        model: str | None = None,
        minPrice: int | None = None,
        maxPrice: int | None = None,
        location: str | None = None,
        radius: int | None = 50,
        maxPages: int = 3,
        scrollsPerPage: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Search Facebook Marketplace for motorcycles.

        Args:
            query: Search query
            make: Motorcycle make
            model: Motorcycle model
            minPrice: Minimum price
            maxPrice: Maximum price
            location: Location for search
            radius: Search radius in miles
            maxPages: Maximum number of pages to scrape (via scrolling)
            scrollsPerPage: Number of scrolls per "page"

        Returns:
            List of listing dictionaries
        """
        searchUrl = self.buildSearchUrl(
            query=query,
            make=make,
            model=model,
            minPrice=minPrice,
            maxPrice=maxPrice,
            location=location,
            radius=radius,
        )

        logger.info(f"Searching Facebook Marketplace: {searchUrl}")

        self._launchBrowser()

        try:
            if not self.context:
                raise ScraperError("Browser context not initialized", retryable=False)

            page = self.context.new_page()

            # Navigate to search results
            page.goto(searchUrl, wait_until="networkidle", timeout=30000)

            # Wait for initial load
            time.sleep(random.uniform(2, 4))

            # Simulate human behavior
            self._simulateHumanBehavior(page)

            # Scroll to load more results
            totalScrolls = maxPages * scrollsPerPage
            self._scrollToLoadMore(page, scrolls=totalScrolls)

            # Get page HTML
            html = page.content()

            # Parse listings
            listings = self._parseSearchResults(html)

            # Close page
            page.close()

            return listings

        except PlaywrightTimeout as e:
            raise ScraperError(
                "Timeout loading Facebook Marketplace search results",
                retryable=True,
                context={"url": searchUrl},
            ) from e
        except Exception as e:
            raise ScraperError(
                f"Failed to search Facebook Marketplace: {e}",
                retryable=False,
                context={"url": searchUrl},
            ) from e
        finally:
            self._closeBrowser()

    def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Scrape Facebook Marketplace listings.

        Implements the abstract scrape method from BaseScraper.

        Args:
            **kwargs: Search parameters (query, make, model, minPrice, maxPrice,
                      location, radius, maxPages, scrollsPerPage)

        Returns:
            List of scraped listings
        """
        return self.search(**kwargs)

    def scrapeListingDetails(self, url: str) -> dict[str, Any]:
        """
        Scrape detailed information from a single listing page.

        Args:
            url: Listing URL

        Returns:
            Dictionary with detailed listing data
        """
        logger.info(f"Scraping listing details: {url}")

        self._launchBrowser()

        try:
            if not self.context:
                raise ScraperError("Browser context not initialized", retryable=False)

            page = self.context.new_page()

            # Navigate to listing
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for content
            time.sleep(random.uniform(2, 4))

            # Simulate human behavior
            self._simulateHumanBehavior(page)

            # Get page HTML
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Parse listing details
            # Note: Facebook's HTML structure changes frequently
            # This is a simplified implementation

            listing: dict[str, Any] = {"url": url}

            # Title
            titleElement = soup.find("h1")
            listing["title"] = titleElement.get_text(strip=True) if titleElement else None

            # Price
            priceElement = soup.find(string=re.compile(r"\$[\d,]+"))
            listing["price"] = self._parsePrice(priceElement) if priceElement else None

            # Description
            # Look for large text blocks
            descElement = soup.find("div", class_=re.compile(".*description.*", re.IGNORECASE))
            if not descElement:
                # Fallback: look for large paragraphs
                paragraphs = soup.find_all("p")
                if paragraphs:
                    descElement = max(paragraphs, key=lambda p: len(p.get_text()))

            listing["description"] = descElement.get_text(strip=True) if descElement else None

            # Location
            locationElement = soup.find(string=re.compile(r"[A-Z][a-z]+,\s*[A-Z]{2}"))
            listing["location"] = locationElement.strip() if locationElement else None

            # Extract year, make, model from title
            if listing.get("title"):
                listing["year"] = self._parseYear(listing["title"])

            # Images
            images: list[str] = []
            imgElements = soup.find_all("img", src=True)
            for img in imgElements:
                src = img.get("src")
                if src and ("scontent" in src or "fbcdn" in src):  # Facebook CDN URLs
                    images.append(src)

            listing["images"] = images[:20]  # Limit to 20 images

            # Close page
            page.close()

            logger.info(f"Successfully scraped listing details: {listing.get('title')}")
            return listing

        except PlaywrightTimeout as e:
            raise ScraperError(
                "Timeout loading Facebook listing page",
                retryable=True,
                context={"url": url},
            ) from e
        except Exception as e:
            raise ScraperError(
                f"Failed to scrape Facebook listing: {e}",
                retryable=False,
                context={"url": url},
            ) from e
        finally:
            self._closeBrowser()
