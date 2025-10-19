"""
Unit tests for Facebook Marketplace scraper.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.scrapers.facebook import FacebookMarketplaceScraper


class TestFacebookMarketplaceScraper(unittest.TestCase):
    """Test Facebook Marketplace scraper functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = FacebookMarketplaceScraper()

    def tearDown(self):
        """Clean up after tests."""
        if self.scraper.browser:
            self.scraper._closeBrowser()

    def testScraperInitialization(self):
        """Test scraper initializes correctly."""
        assert self.scraper.source == "facebook"
        assert self.scraper.BASE_URL == "https://www.facebook.com/marketplace"
        assert self.scraper.playwright is None
        assert self.scraper.browser is None
        assert self.scraper.context is None

    # Search URL Construction Tests

    def testBuildSearchUrlWithQuery(self):
        """Test building search URL with query parameter."""
        url = self.scraper.buildSearchUrl(query="Ducati Panigale V4")
        assert "marketplace/category/motorcycles" in url
        assert "query=Ducati+Panigale+V4" in url

    def testBuildSearchUrlWithMakeModel(self):
        """Test building search URL from make and model."""
        url = self.scraper.buildSearchUrl(make="Ducati", model="Panigale V4")
        assert "marketplace/category/motorcycles" in url
        assert "query=Ducati+Panigale+V4" in url

    def testBuildSearchUrlWithPriceFilters(self):
        """Test building search URL with price filters."""
        url = self.scraper.buildSearchUrl(
            query="Ducati Panigale V4",
            minPrice=10000,
            maxPrice=25000,
        )
        assert "minPrice=10000" in url
        assert "maxPrice=25000" in url

    def testBuildSearchUrlWithLocation(self):
        """Test building search URL with location."""
        url = self.scraper.buildSearchUrl(
            query="Ducati Panigale V4",
            location="New York, NY",
            radius=100,
        )
        assert "location=New+York" in url
        assert "radius=100" in url

    def testBuildSearchUrlNoQueryRaisesError(self):
        """Test that missing query raises ValueError."""
        with pytest.raises(ValueError, match="Either query or make/model must be provided"):
            self.scraper.buildSearchUrl()

    # Price Parsing Tests

    def testPriceParsing(self):
        """Test parsing valid price strings."""
        testCases = [
            ("$15,000", 15000),
            ("$15000", 15000),
            ("15000", 15000),
            ("$15k", 15000),
            ("15K", 15000),
            ("Price: $20,000", 20000),
        ]

        for priceText, expected in testCases:
            with self.subTest(priceText=priceText):
                result = self.scraper._parsePrice(priceText)
                assert result == expected

    def testPriceParsingInvalid(self):
        """Test parsing invalid price strings."""
        testCases = ["", "N/A", "Contact for price", "abc"]

        for priceText in testCases:
            with self.subTest(priceText=priceText):
                result = self.scraper._parsePrice(priceText)
                assert result is None

    # Mileage Parsing Tests

    def testMileageParsing(self):
        """Test parsing valid mileage strings."""
        testCases = [
            ("5,000 mi", 5000),
            ("5000 miles", 5000),
            ("5k miles", 5000),
            ("5K mi", 5000),
            ("12000", 12000),
        ]

        for mileageText, expected in testCases:
            with self.subTest(mileageText=mileageText):
                result = self.scraper._parseMileage(mileageText)
                assert result == expected

    def testMileageParsingInvalid(self):
        """Test parsing invalid mileage strings."""
        testCases = ["", "N/A", "Unknown", "abc"]

        for mileageText in testCases:
            with self.subTest(mileageText=mileageText):
                result = self.scraper._parseMileage(mileageText)
                assert result is None

    # Year Parsing Tests

    def testYearParsing(self):
        """Test parsing year from text."""
        testCases = [
            ("2022 Ducati Panigale V4", 2022),
            ("Ducati Panigale V4 2021", 2021),
            ("2020", 2020),
            ("Year: 2019", 2019),
        ]

        for text, expected in testCases:
            with self.subTest(text=text):
                result = self.scraper._parseYear(text)
                assert result == expected

    def testYearParsingInvalid(self):
        """Test parsing invalid year text."""
        testCases = ["", "N/A", "Ducati Panigale", "123", "12345"]

        for text in testCases:
            with self.subTest(text=text):
                result = self.scraper._parseYear(text)
                assert result is None

    # Listing Card Parsing Tests

    def testParseListingCardValid(self):
        """Test parsing a valid listing card."""
        from bs4 import BeautifulSoup

        html = """
        <div role="article">
            <a href="/marketplace/item/123456789">
                <span>2022 Ducati Panigale V4</span>
                <img src="https://scontent.xx.fbcdn.net/image.jpg" />
            </a>
            <span>$18,500</span>
            <span>Los Angeles, CA</span>
        </div>
        """

        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("div", {"role": "article"})

        result = self.scraper._parseListingCard(card)

        assert result is not None
        assert "facebook.com/marketplace/item/123456789" in result["url"]
        assert result["title"] == "2022 Ducati Panigale V4"
        assert result["price"] == 18500
        assert result["year"] == 2022
        assert result["imageUrl"] is not None

    def testParseListingCardPartialData(self):
        """Test parsing listing card with some missing data."""
        from bs4 import BeautifulSoup

        html = """
        <div role="article">
            <a href="/marketplace/item/123456789">
                <span>Ducati Motorcycle</span>
            </a>
        </div>
        """

        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("div", {"role": "article"})

        result = self.scraper._parseListingCard(card)

        assert result is not None
        assert "facebook.com/marketplace/item/123456789" in result["url"]
        assert result["title"] == "Ducati Motorcycle"
        assert result["price"] is None
        assert result["year"] is None

    def testParseListingCardNoLink(self):
        """Test parsing listing card without link returns None."""
        from bs4 import BeautifulSoup

        html = """
        <div role="article">
            <span>2022 Ducati Panigale V4</span>
        </div>
        """

        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("div", {"role": "article"})

        result = self.scraper._parseListingCard(card)

        assert result is None

    # Search Results Parsing Tests

    def testParseSearchResultsValid(self):
        """Test parsing valid search results page."""
        html = """
        <html>
            <body>
                <div role="article">
                    <a href="/marketplace/item/111">
                        <span>2022 Ducati Panigale V4</span>
                    </a>
                    <span>$18,500</span>
                </div>
                <div role="article">
                    <a href="/marketplace/item/222">
                        <span>2021 Ducati Panigale V4S</span>
                    </a>
                    <span>$22,000</span>
                </div>
                <div role="article">
                    <a href="/marketplace/item/333">
                        <span>2020 Ducati Panigale V4R</span>
                    </a>
                    <span>$30,000</span>
                </div>
            </body>
        </html>
        """

        results = self.scraper._parseSearchResults(html)

        assert len(results) == 3
        assert results[0]["title"] == "2022 Ducati Panigale V4"
        assert results[0]["price"] == 18500
        assert results[1]["title"] == "2021 Ducati Panigale V4S"
        assert results[2]["price"] == 30000

    def testParseSearchResultsEmpty(self):
        """Test parsing search results with no listings."""
        html = """
        <html>
            <body>
                <div>No listings found</div>
            </body>
        </html>
        """

        results = self.scraper._parseSearchResults(html)

        assert len(results) == 0

    # Context Manager Tests

    def testContextManager(self):
        """Test scraper works as context manager."""
        with (
            patch.object(FacebookMarketplaceScraper, "_launchBrowser") as mockLaunch,
            patch.object(FacebookMarketplaceScraper, "_closeBrowser") as mockClose,
        ):

            with FacebookMarketplaceScraper() as scraper:
                assert scraper is not None

            mockLaunch.assert_called_once()
            mockClose.assert_called_once()

    # Browser Management Tests

    @patch("src.scrapers.facebook.sync_playwright")
    def testLaunchBrowser(self, mockPlaywright):
        """Test browser launch with anti-detection measures."""
        # Setup mocks
        mockPlaywrightInstance = MagicMock()
        mockPlaywright.return_value.start.return_value = mockPlaywrightInstance

        mockBrowser = MagicMock()
        mockPlaywrightInstance.chromium.launch.return_value = mockBrowser

        mockContext = MagicMock()
        mockBrowser.new_context.return_value = mockContext

        # Launch browser
        self.scraper._launchBrowser()

        # Verify browser launched with correct args
        mockPlaywrightInstance.chromium.launch.assert_called_once()
        args = mockPlaywrightInstance.chromium.launch.call_args[1]
        assert not args["headless"]
        assert "--disable-blink-features=AutomationControlled" in args["args"]

        # Verify context created
        mockBrowser.new_context.assert_called_once()
        contextArgs = mockBrowser.new_context.call_args[1]
        assert "Mozilla" in contextArgs["user_agent"]

        # Verify anti-detection script injected
        mockContext.add_init_script.assert_called_once()

    def testCloseBrowser(self):
        """Test browser cleanup."""
        # Setup mock browser components
        mockContext = MagicMock()
        mockBrowser = MagicMock()
        mockPlaywright = MagicMock()

        self.scraper.context = mockContext
        self.scraper.browser = mockBrowser
        self.scraper.playwright = mockPlaywright

        # Close browser
        self.scraper._closeBrowser()

        # Verify cleanup
        mockContext.close.assert_called_once()
        mockBrowser.close.assert_called_once()
        mockPlaywright.stop.assert_called_once()

        # Verify references cleared
        assert self.scraper.context is None
        assert self.scraper.browser is None
        assert self.scraper.playwright is None


if __name__ == "__main__":
    unittest.main()
