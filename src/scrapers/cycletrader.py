"""
CycleTrader scraper using Playwright for browser automation.
"""

import os
import re
import time
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.scrapers.base import BaseScraper
from src.utils.exceptions import ParseError, ScraperError, logError
from src.utils.logger import getLogger

logger = getLogger(__name__)


class CycleTraderScraper(BaseScraper):
    """CycleTrader scraper using Playwright."""

    BASE_URL = "https://www.cycletrader.com"

    def __init__(self, headless: bool = False, proxy: str | None = None):
        """Initialize CycleTrader scraper.

        Args:
            headless: Run browser in headless mode. Default False because CycleTrader
                      actively blocks headless browsers. Set to True only for mocked tests.
            proxy: Proxy server URL (e.g., "http://proxy.example.com:8080")
        """
        super().__init__("cycletrader")
        self.playwright = None
        self.browser = None
        self.context = None
        self.headless = headless
        self.proxy = proxy

    def _launchBrowser(self):
        """Launch Playwright browser with anti-detection measures."""
        if self.browser is None:
            self.playwright = sync_playwright().start()
            assert self.playwright is not None

            # Launch browser with anti-detection args
            # IMPORTANT: CycleTrader blocks headless browsers despite anti-detection measures
            # For production use, headless=False is required (browser window will be visible)
            # For containerized/CI environments, use mocked data or accept that scraping will fail
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Create context with realistic browser fingerprint
            context_options = {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "locale": "en-US",
                "timezone_id": "America/New_York",
            }

            # Add proxy if provided
            if self.proxy:
                context_options["proxy"] = {"server": self.proxy}

            self.context = self.browser.new_context(**context_options)

            self.logger.info("Browser launched with anti-detection measures")

    def _addAntiDetectionScripts(self, page):
        """Add JavaScript to hide automation indicators."""
        # Remove webdriver property
        page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
        )

        # Override the plugins length
        page.add_init_script(
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            })
        """
        )

        # Override the languages
        page.add_init_script(
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            })
        """
        )

    def _detectDataDomeCaptcha(self, page) -> bool:
        """
        Detect if DataDome CAPTCHA is present on the page.

        Args:
            page: Playwright page object

        Returns:
            True if CAPTCHA detected, False otherwise
        """
        html = page.content()
        return "datadome" in html.lower() or "captcha-delivery.com" in html.lower()

    def _solveCaptchaWith2Captcha(self, page, pageUrl: str) -> bool:
        """
        Solve DataDome CAPTCHA using 2Captcha service or manual solving.

        If TWOCAPTCHA_API_KEY environment variable is set, uses automatic solving.
        Otherwise, waits for manual CAPTCHA solving in the browser window.

        Args:
            page: Playwright page object
            pageUrl: Current page URL

        Returns:
            True if CAPTCHA solved successfully, False otherwise
        """
        apiKey = os.getenv("TWOCAPTCHA_API_KEY")

        if not apiKey:
            # Fallback to manual solving
            self.logger.warning(
                "DataDome CAPTCHA detected. TWOCAPTCHA_API_KEY not set - falling back to manual solving."
            )
            self.logger.info(
                "Please solve the CAPTCHA in the browser window (60 second timeout)..."
            )

            # Wait up to 60 seconds for manual CAPTCHA solve
            for i in range(12):  # 12 * 5 = 60 seconds
                time.sleep(5)
                if not self._detectDataDomeCaptcha(page):
                    self.logger.info("CAPTCHA solved manually!")
                    return True
                if (i + 1) % 3 == 0:  # Log every 15 seconds
                    remaining = 60 - ((i + 1) * 5)
                    self.logger.info(f"Still waiting... ({remaining} seconds remaining)")

            self.logger.warning("CAPTCHA not solved within 60 seconds")
            return False

        # Automatic solving with 2Captcha
        try:
            from twocaptcha import TwoCaptcha

            solver = TwoCaptcha(apiKey)

            self.logger.info(
                "DataDome CAPTCHA detected, attempting automatic solve with 2Captcha..."
            )

            # Get the current page URL and captcha URL
            currentUrl = page.url

            # Extract DataDome captcha URL from iframe
            html = page.content()
            # Look for the iframe with captcha-delivery.com/captcha/ URL
            captchaUrlMatch = re.search(
                r'<iframe[^>]*src="(https://[^"]*captcha-delivery\.com/captcha/[^"]*)"', html
            )

            if not captchaUrlMatch:
                self.logger.warning(
                    "Could not extract DataDome captcha URL. Falling back to manual solving..."
                )
                # Fall back to manual solving
                for i in range(12):  # 12 * 5 = 60 seconds
                    time.sleep(5)
                    if not self._detectDataDomeCaptcha(page):
                        self.logger.info("CAPTCHA solved manually!")
                        return True
                    if (i + 1) % 3 == 0:
                        remaining = 60 - ((i + 1) * 5)
                        self.logger.info(f"Still waiting... ({remaining} seconds remaining)")
                return False

            captchaUrl = captchaUrlMatch.group(1)
            # Unescape HTML entities (&amp; → &)
            captchaUrl = captchaUrl.replace("&amp;", "&")
            self.logger.info("Sending DataDome CAPTCHA to 2Captcha service...")
            self.logger.info(f"Captcha URL: {captchaUrl[:100]}...")

            # Use 2Captcha's DataDome task
            # Note: This may take 30-120 seconds
            # DataDome solving requires proxy parameter (format: {'type': 'HTTP', 'uri': 'host:port'})
            # We provide a placeholder since we're not using a proxy
            proxyConfig = {"type": "HTTP", "uri": "127.0.0.1:8080"}

            result = solver.datadome(
                captcha_url=captchaUrl,
                pageurl=currentUrl,
                userAgent=page.evaluate("navigator.userAgent"),
                proxy=proxyConfig,
            )

            if result and "code" in result:
                self.logger.info("CAPTCHA solved by 2Captcha! Injecting solution...")

                # Inject the solution cookie
                # DataDome uses a specific cookie format
                page.evaluate(f"document.cookie = 'datadome={result['code']}; path=/'")

                # Reload the page with the solution
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

                # Verify CAPTCHA is solved
                if not self._detectDataDomeCaptcha(page):
                    self.logger.info("✓ CAPTCHA successfully solved automatically!")
                    return True
                else:
                    self.logger.warning(
                        "CAPTCHA solution didn't work. Falling back to manual solving..."
                    )
                    # Fall back to manual
                    for i in range(12):
                        time.sleep(5)
                        if not self._detectDataDomeCaptcha(page):
                            self.logger.info("CAPTCHA solved manually!")
                            return True
                        if (i + 1) % 3 == 0:
                            remaining = 60 - ((i + 1) * 5)
                            self.logger.info(f"Still waiting... ({remaining} seconds remaining)")
                    return False
            else:
                self.logger.warning("2Captcha failed to solve. Falling back to manual solving...")
                for i in range(12):
                    time.sleep(5)
                    if not self._detectDataDomeCaptcha(page):
                        self.logger.info("CAPTCHA solved manually!")
                        return True
                    if (i + 1) % 3 == 0:
                        remaining = 60 - ((i + 1) * 5)
                        self.logger.info(f"Still waiting... ({remaining} seconds remaining)")
                return False

        except ImportError:
            self.logger.error("2captcha-python not installed. Run: pip install 2captcha-python")
            return False
        except Exception as e:
            self.logger.warning(f"Error with 2Captcha automatic solving: {e}")
            self.logger.info("Falling back to manual solving...")
            # Fall back to manual solving
            for i in range(12):  # 12 * 5 = 60 seconds
                time.sleep(5)
                if not self._detectDataDomeCaptcha(page):
                    self.logger.info("CAPTCHA solved manually!")
                    return True
                if (i + 1) % 3 == 0:
                    remaining = 60 - ((i + 1) * 5)
                    self.logger.info(f"Still waiting... ({remaining} seconds remaining)")
            return False

    def buildSearchUrl(
        self,
        make: str | None = None,
        model: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        price_max: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Build search URL for CycleTrader.

        Args:
            make: Motorcycle make (e.g., "Ducati")
            model: Motorcycle model (e.g., "Panigale V4")
            year_min: Minimum year
            year_max: Maximum year
            price_max: Maximum price
            **kwargs: Additional query parameters

        Returns:
            Search URL
        """
        params: dict[str, Any] = {}

        if make:
            params["make"] = make
        if model:
            params["model"] = model
        if year_min:
            params["yearMin"] = year_min
        if year_max:
            params["yearMax"] = year_max
        if price_max:
            params["priceMax"] = price_max

        # Add any additional parameters
        params.update(kwargs)

        query_string = urlencode(params)
        url = f"{self.BASE_URL}/motorcycles-for-sale?{query_string}"

        self.logger.info(f"Built search URL: {url}")
        return url

    def parseSearchResults(self, html: str) -> list[dict[str, Any]]:
        """
        Parse search results page.

        Args:
            html: HTML content of search results page

        Returns:
            List of listing data dictionaries

        Raises:
            ParseError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            listings = []

            # Find all listing cards
            listing_cards = soup.find_all("article", class_="search-card")

            if not listing_cards:
                self.logger.warning("No listing cards found on page")
                return []

            for card in listing_cards:
                try:
                    listing_data = self._parseListingCard(card)
                    if listing_data:
                        listings.append(listing_data)
                except Exception as e:
                    self.logger.warning(f"Failed to parse listing card: {e}")
                    continue

            self.logger.info(f"Parsed {len(listings)} listings from search results")
            return listings

        except Exception as e:
            raise ParseError(f"Failed to parse search results: {str(e)}") from e

    def _parseListingCard(self, card) -> dict[str, Any] | None:
        """
        Parse individual listing card from search results.

        Args:
            card: BeautifulSoup element for listing card

        Returns:
            Listing data dictionary or None if parsing fails
        """
        try:
            # Extract listing URL
            link = card.find("a", href=True)
            if not link:
                return None

            url = link["href"]
            if not url.startswith("http"):
                url = self.BASE_URL + url

            # Extract price - look for the specific price div
            # Try to find the main price element (has class 'price' as one of the classes)
            price_elem = card.find(
                "div", class_=lambda x: x and "price" in x and "wrapper" not in str(x).lower()
            )
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self._parsePrice(price_text) if price_text else None

            # Extract title (usually contains year, make, model)
            title_elem = card.find(class_=lambda x: x and "title" in x.lower())
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Extract mileage
            mileage_elem = card.find(class_=lambda x: x and "mileage" in x.lower())
            mileage_text = mileage_elem.get_text(strip=True) if mileage_elem else None
            mileage = self._parseMileage(mileage_text) if mileage_text else None

            # Extract location
            location_elem = card.find(class_=lambda x: x and "location" in x.lower())
            location = location_elem.get_text(strip=True) if location_elem else None

            return {
                "url": url,
                "title": title,
                "price": price,
                "mileage": mileage,
                "location": location,
                "source": "cycletrader",
            }

        except Exception as e:
            self.logger.debug(f"Error parsing listing card: {e}")
            return None

    def parseListingDetails(self, html: str, url: str) -> dict[str, Any]:
        """
        Parse individual listing detail page.

        Args:
            html: HTML content of listing page
            url: Listing URL

        Returns:
            Complete listing data dictionary

        Raises:
            ParseError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            data: dict[str, Any] = {"url": url, "source": "cycletrader"}

            # Extract title
            title_elem = soup.find("h1")
            data["title"] = title_elem.get_text(strip=True) if title_elem else ""

            # Extract price
            price_elem = soup.find(class_=lambda x: x and "price" in x.lower())
            price_text = price_elem.get_text(strip=True) if price_elem else None
            data["price"] = self._parsePrice(price_text) if price_text else None

            # Extract description
            desc_elem = soup.find(class_=lambda x: x and "description" in x.lower())
            data["description"] = desc_elem.get_text(strip=True) if desc_elem else ""

            # Extract specifications
            specs = self._extractSpecifications(soup)
            data.update(specs)

            # Extract images
            data["image_urls"] = self._extractImages(soup)

            self.logger.info(f"Parsed listing details for {url}")
            return data

        except Exception as e:
            raise ParseError(f"Failed to parse listing details: {str(e)}", url=url) from e

    def _extractSpecifications(self, soup) -> dict[str, Any]:
        """Extract specifications from listing page."""
        specs = {}

        # Look for spec list
        spec_list = soup.find("dl") or soup.find("ul", class_=lambda x: x and "spec" in x.lower())

        if spec_list:
            items = spec_list.find_all(["dt", "dd"]) or spec_list.find_all("li")

            for i in range(0, len(items) - 1, 2):
                key = items[i].get_text(strip=True).lower()
                value = items[i + 1].get_text(strip=True)

                if "year" in key:
                    specs["year"] = self._parseYear(value)
                elif "make" in key:
                    specs["make"] = value
                elif "model" in key:
                    specs["model"] = value
                elif "mileage" in key or "odometer" in key:
                    specs["mileage"] = self._parseMileage(value)
                elif "condition" in key:
                    specs["condition"] = value
                elif "vin" in key:
                    specs["vin"] = value

        return specs

    def _extractImages(self, soup) -> list[str]:
        """Extract image URLs from listing page."""
        images = []

        # Find image gallery
        img_elements = soup.find_all("img", src=True)

        for img in img_elements:
            src = img["src"]
            # Filter out icons, logos, etc.
            if any(x in src.lower() for x in ["icon", "logo", "avatar"]):
                continue

            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = self.BASE_URL + src

            if src not in images:
                images.append(src)

        return images[:20]  # Limit to 20 images

    def _parsePrice(self, price_text: str) -> float | None:
        """Parse price from text."""
        if not price_text:
            return None

        # Remove currency symbols, commas, spaces, asterisks
        cleaned = price_text.replace("$", "").replace(",", "").replace(" ", "").replace("*", "")

        # Handle "Call for price", "Contact dealer", etc.
        if not cleaned or not any(c.isdigit() for c in cleaned):
            return None

        try:
            # Extract just the numeric part (in case there are letters mixed in)
            match = re.search(r"(\d+\.?\d*)", cleaned)
            if match:
                return float(match.group(1))
            return None
        except ValueError:
            return None

    def _parseMileage(self, mileage_text: str) -> int | None:
        """Parse mileage from text."""
        if not mileage_text:
            return None

        # Remove commas, "miles", "mi", spaces
        cleaned = (
            mileage_text.replace(",", "")
            .replace("miles", "")
            .replace("mi", "")
            .replace(" ", "")
            .lower()
        )

        # Handle "k" suffix (e.g., "5.2k" = 5200)
        if "k" in cleaned:
            try:
                num = float(cleaned.replace("k", ""))
                return int(num * 1000)
            except ValueError:
                return None

        try:
            return int(float(cleaned))
        except ValueError:
            return None

    def _parseYear(self, year_text: str) -> int | None:
        """Parse year from text."""
        if not year_text:
            return None

        try:
            return int(year_text.strip())
        except ValueError:
            return None

    def scrapeSearchResults(self, search_url: str, max_pages: int = 5) -> list[dict[str, Any]]:
        """
        Scrape search results with pagination.

        Args:
            search_url: Search URL
            max_pages: Maximum number of pages to scrape

        Returns:
            List of all listings from all pages

        Raises:
            ScraperError: On scraping failure
        """
        self._launchBrowser()
        all_listings: list[dict[str, Any]] = []
        page_num = 1

        try:
            if not self.context:
                raise ScraperError("Browser context not initialized")

            page = self.context.new_page()

            # Add anti-detection scripts
            self._addAntiDetectionScripts(page)

            while page_num <= max_pages:
                self.logger.info(f"Scraping page {page_num}/{max_pages}")

                # Navigate to page
                page.goto(search_url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)  # Wait for dynamic content to load

                # Check for DataDome CAPTCHA
                if self._detectDataDomeCaptcha(page):
                    self.logger.warning("DataDome CAPTCHA detected")
                    if not self._solveCaptchaWith2Captcha(page, search_url):
                        raise ScraperError(
                            "Failed to solve DataDome CAPTCHA. "
                            "Either solve it manually or set TWOCAPTCHA_API_KEY environment variable.",
                            retryable=True,
                        )
                    # Wait a bit after CAPTCHA solve
                    page.wait_for_timeout(2000)

                # Get HTML
                html = page.content()

                # Parse listings
                listings = self.parseSearchResults(html)

                if not listings:
                    self.logger.info(f"No listings found on page {page_num}, stopping")
                    break

                all_listings.extend(listings)

                # Check for next page
                next_button = page.query_selector('a[aria-label="Next"]')
                if not next_button or page_num >= max_pages:
                    break

                # Click next page
                search_url = next_button.get_attribute("href")
                if not search_url.startswith("http"):
                    search_url = self.BASE_URL + search_url

                page_num += 1

            page.close()
            self.logger.info(f"Scraped {len(all_listings)} total listings")
            return all_listings

        except Exception as e:
            logError(e)
            raise ScraperError(f"Failed to scrape search results: {str(e)}", url=search_url) from e

    def scrape(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Scrape CycleTrader listings.

        Args:
            **kwargs: Search parameters (make, model, year_min, year_max, etc.)

        Returns:
            List of scraped listings
        """
        search_url = self.buildSearchUrl(**kwargs)
        max_pages = kwargs.get("max_pages", 5)

        return self.scrapeSearchResults(search_url, max_pages=max_pages)

    def close(self):
        """Close browser and cleanup resources."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        super().close()
        self.logger.info("Browser closed")
