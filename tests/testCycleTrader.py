"""
Unit tests for CycleTrader scraper.

Tests parsing methods and URL construction without requiring browser automation.
"""

from bs4 import BeautifulSoup

from src.scrapers.cycletrader import CycleTraderScraper


class TestCycleTraderScraper:
    """Test CycleTrader scraper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = CycleTraderScraper()

    def teardown_method(self):
        """Clean up after tests."""
        self.scraper.close()

    def testSearchUrlConstruction(self):
        """Verify search URL is constructed correctly."""
        url = self.scraper.buildSearchUrl(
            make="Ducati", model="Panigale V4", year_min=2018, year_max=2024, price_max=30000
        )

        assert "cycletrader.com" in url
        assert "make=Ducati" in url
        assert "model=Panigale+V4" in url or "model=Panigale%20V4" in url
        assert "yearMin=2018" in url
        assert "yearMax=2024" in url
        assert "priceMax=30000" in url

    def testSearchUrlWithMinimalParams(self):
        """Verify search URL with only make."""
        url = self.scraper.buildSearchUrl(make="Honda")

        assert "cycletrader.com" in url
        assert "make=Honda" in url

    def testPriceParsingValid(self):
        """Test price parsing with valid inputs."""
        assert self.scraper._parsePrice("$14,250") == 14250.0
        assert self.scraper._parsePrice("$6,500") == 6500.0
        assert self.scraper._parsePrice("$31,245") == 31245.0
        assert self.scraper._parsePrice("$17,500*") == 17500.0
        assert self.scraper._parsePrice("$12,990") == 12990.0
        assert self.scraper._parsePrice("10000") == 10000.0
        assert self.scraper._parsePrice("9999.99") == 9999.99

    def testPriceParsingInvalid(self):
        """Test price parsing with invalid inputs."""
        assert self.scraper._parsePrice("Call for price") is None
        assert self.scraper._parsePrice("Contact dealer") is None
        assert self.scraper._parsePrice("") is None
        assert self.scraper._parsePrice(None) is None
        assert self.scraper._parsePrice("N/A") is None

    def testMileageParsingValid(self):
        """Test mileage parsing with valid inputs."""
        assert self.scraper._parseMileage("1,854 mi") == 1854
        assert self.scraper._parseMileage("12,500 miles") == 12500
        assert self.scraper._parseMileage("5.2k") == 5200
        assert self.scraper._parseMileage("10k") == 10000
        assert self.scraper._parseMileage("500") == 500
        assert self.scraper._parseMileage("1,000") == 1000

    def testMileageParsingInvalid(self):
        """Test mileage parsing with invalid inputs."""
        assert self.scraper._parseMileage("") is None
        assert self.scraper._parseMileage(None) is None
        assert self.scraper._parseMileage("Unknown") is None
        assert self.scraper._parseMileage("N/A") is None

    def testYearParsingValid(self):
        """Test year parsing with valid inputs."""
        assert self.scraper._parseYear("2024") == 2024
        assert self.scraper._parseYear("2019") == 2019
        assert self.scraper._parseYear("  2020  ") == 2020

    def testYearParsingInvalid(self):
        """Test year parsing with invalid inputs."""
        assert self.scraper._parseYear("") is None
        assert self.scraper._parseYear(None) is None
        assert self.scraper._parseYear("Unknown") is None

    def testParseListingCardValid(self):
        """Test parsing a valid listing card."""
        html = """
        <article class="search-card">
            <a href="/listing/2019-Ducati-PANIGALE+959+CORSE-5037265765">
                <div class="title">2019 Ducati PANIGALE 959 CORSE Sportbike</div>
            </a>
            <div class="price font-white tide-font-400 tide-font-20">$14,250</div>
            <div class="mileage">1,854 mi</div>
            <div class="location">2 mi away</div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("article")

        result = self.scraper._parseListingCard(card)

        assert result is not None
        assert (
            result["url"]
            == "https://www.cycletrader.com/listing/2019-Ducati-PANIGALE+959+CORSE-5037265765"
        )
        assert result["title"] == "2019 Ducati PANIGALE 959 CORSE Sportbike"
        assert result["price"] == 14250.0
        assert result["mileage"] == 1854
        assert result["location"] == "2 mi away"
        assert result["source"] == "cycletrader"

    def testParseListingCardPartialData(self):
        """Test parsing a listing card with missing optional fields."""
        html = """
        <article class="search-card">
            <a href="/motorcycles/2020-honda-cbr">
                <div class="title">2020 Honda CBR600RR</div>
            </a>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("article")

        result = self.scraper._parseListingCard(card)

        assert result is not None
        assert "cycletrader.com" in result["url"]
        assert result["title"] == "2020 Honda CBR600RR"
        assert result["price"] is None
        assert result["mileage"] is None
        assert result["source"] == "cycletrader"

    def testParseListingCardNoLink(self):
        """Test parsing a card with no link."""
        html = """
        <article class="search-card">
            <div class="title">Some Title</div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("article")

        result = self.scraper._parseListingCard(card)

        assert result is None

    def testParseSearchResultsValid(self):
        """Test parsing search results page with multiple listings."""
        html = """
        <html>
            <body>
                <article class="search-card">
                    <a href="/listing/listing-1">
                        <div class="title">Motorcycle 1</div>
                    </a>
                    <div class="price font-white tide-font-400 tide-font-20">$10,000</div>
                </article>
                <article class="search-card">
                    <a href="/listing/listing-2">
                        <div class="title">Motorcycle 2</div>
                    </a>
                    <div class="price font-white tide-font-400 tide-font-20">$15,000</div>
                </article>
                <article class="search-card">
                    <a href="/listing/listing-3">
                        <div class="title">Motorcycle 3</div>
                    </a>
                </article>
            </body>
        </html>
        """

        results = self.scraper.parseSearchResults(html)

        assert len(results) == 3
        assert results[0]["title"] == "Motorcycle 1"
        assert results[0]["price"] == 10000.0
        assert results[1]["title"] == "Motorcycle 2"
        assert results[1]["price"] == 15000.0
        assert results[2]["title"] == "Motorcycle 3"
        assert results[2]["price"] is None

    def testParseSearchResultsEmpty(self):
        """Test parsing search results with no listings."""
        html = """
        <html>
            <body>
                <div>No listings found</div>
            </body>
        </html>
        """

        results = self.scraper.parseSearchResults(html)

        assert len(results) == 0

    def testExtractImagesValid(self):
        """Test image extraction from listing page."""
        html = """
        <html>
            <body>
                <img src="https://example.com/bike1.jpg" />
                <img src="//example.com/bike2.jpg" />
                <img src="/images/bike3.jpg" />
                <img src="/images/icon.png" />
                <img src="/images/logo.gif" />
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        images = self.scraper._extractImages(soup)

        # Should extract bike images but not icons/logos
        assert len(images) <= 5
        assert "https://example.com/bike1.jpg" in images
        assert "https://example.com/bike2.jpg" in images
        assert any("bike3.jpg" in img for img in images)

    def testExtractImagesLimit(self):
        """Test that image extraction respects the 20 image limit."""
        # Generate HTML with 30 images
        img_tags = "".join([f'<img src="https://example.com/bike{i}.jpg" />' for i in range(30)])
        html = f"<html><body>{img_tags}</body></html>"
        soup = BeautifulSoup(html, "html.parser")

        images = self.scraper._extractImages(soup)

        # Should be limited to 20
        assert len(images) == 20
