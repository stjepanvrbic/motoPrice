"""
Integration tests for CycleTrader scraper against real website.

These tests verify the scraper works with the actual CycleTrader website.
Run manually to verify scraper functionality and detect website changes.

Usage:
    pytest tests/integration/testCycleTraderIntegration.py -v -s
"""

import pytest

from src.scrapers.cycletrader import CycleTraderScraper


@pytest.mark.integration()
def testCycleTraderSearchUrlConstruction():
    """Verify search URL construction."""
    scraper = CycleTraderScraper()

    url = scraper.buildSearchUrl(make="Ducati", model="Panigale V4")

    assert "cycletrader.com" in url
    assert "make=Ducati" in url
    assert "Panigale" in url

    scraper.close()


@pytest.mark.integration()
def testCycleTraderRealScrape():
    """
    Integration test: Scrape real CycleTrader listings.

    Verifies:
    - Browser automation works
    - Website is accessible
    - HTML structure matches our selectors
    - Data extraction works correctly
    """
    scraper = CycleTraderScraper()

    try:
        # Scrape first page only to minimize load
        listings = scraper.scrape(make="Ducati", model="Panigale V4", max_pages=1)

        # Verify we got results
        assert len(listings) > 0, "No listings found - website may have changed"

        # Verify data structure
        first_listing = listings[0]
        assert "url" in first_listing, "Missing URL field"
        assert "title" in first_listing, "Missing title field"
        assert "source" in first_listing, "Missing source field"
        assert first_listing["source"] == "cycletrader"

        # Verify URL is valid
        assert first_listing["url"].startswith("http"), f"Invalid URL: {first_listing['url']}"
        assert "cycletrader.com" in first_listing["url"]

        # Verify title is not empty
        assert len(first_listing["title"]) > 0, "Title is empty"

        # Verify at least some listings have price data
        listings_with_price = [listing for listing in listings if listing.get("price")]
        assert len(listings_with_price) > 0, "No listings have price data"

        # Verify price data is reasonable
        for listing in listings_with_price:
            assert isinstance(
                listing["price"], int | float
            ), f"Invalid price type: {type(listing['price'])}"
            assert listing["price"] > 0, f"Invalid price: {listing['price']}"
            assert (
                listing["price"] < 1000000
            ), f"Unrealistic price: {listing['price']}"  # Sanity check

        # Print summary for manual verification
        print(f"\n✅ Successfully scraped {len(listings)} listings from CycleTrader")
        print(f"   Listings with price: {len(listings_with_price)}")
        print("\n📋 Sample listing:")
        print(f"   Title: {first_listing['title']}")
        print(f"   URL: {first_listing['url']}")
        if first_listing.get("price"):
            print(f"   Price: ${first_listing['price']:,.2f}")
        if first_listing.get("mileage"):
            print(f"   Mileage: {first_listing['mileage']:,} mi")
        if first_listing.get("location"):
            print(f"   Location: {first_listing['location']}")

    finally:
        scraper.close()


@pytest.mark.integration()
def testCycleTraderPagination():
    """
    Integration test: Verify pagination works.

    Tests that scraper can navigate multiple pages.
    """
    scraper = CycleTraderScraper()

    try:
        # Scrape 2 pages
        listings = scraper.scrape(make="Ducati", max_pages=2)

        # Should get more than one page worth of results
        # (assuming at least 10 results per page)
        assert len(listings) >= 10, f"Expected >10 listings from 2 pages, got {len(listings)}"

        # Verify all URLs are unique (no duplicates)
        urls = [listing["url"] for listing in listings]
        assert len(urls) == len(set(urls)), "Found duplicate listings"

        print(f"\n✅ Successfully scraped {len(listings)} listings across 2 pages")
        print(f"   All URLs unique: {len(urls)} listings")

    finally:
        scraper.close()


@pytest.mark.integration()
def testCycleTraderDataQuality():
    """
    Integration test: Verify data quality and completeness.

    Checks that scraped data meets quality standards.
    """
    scraper = CycleTraderScraper()

    try:
        listings = scraper.scrape(make="Ducati", model="Panigale V4", max_pages=1)

        assert len(listings) > 0, "No listings found"

        # Count fields present
        field_counts = {
            "title": 0,
            "price": 0,
            "mileage": 0,
            "location": 0,
            "url": 0,
        }

        for listing in listings:
            for field in field_counts:
                if listing.get(field):
                    field_counts[field] += 1

        total = len(listings)

        # Print data quality report
        print(f"\n📊 Data Quality Report ({total} listings):")
        for field, count in field_counts.items():
            percentage = (count / total) * 100
            print(f"   {field}: {count}/{total} ({percentage:.1f}%)")

        # Assertions for minimum data quality
        assert field_counts["url"] == total, "All listings must have URLs"
        assert field_counts["title"] >= total * 0.9, "At least 90% must have titles"
        assert field_counts["price"] >= total * 0.5, "At least 50% should have prices"

    finally:
        scraper.close()


if __name__ == "__main__":
    """
    Run integration tests manually.

    Usage:
        python tests/integration/testCycleTraderIntegration.py
    """
    print("Running CycleTrader integration tests...\n")

    # Run basic scrape test
    print("Test 1: Basic scraping")
    testCycleTraderRealScrape()

    print("\nTest 2: Pagination")
    testCycleTraderPagination()

    print("\nTest 3: Data quality")
    testCycleTraderDataQuality()

    print("\n✅ All integration tests passed!")
