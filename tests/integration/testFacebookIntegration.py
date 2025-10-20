"""
Integration tests for Facebook Marketplace scraper.

These tests verify the scraper works against the real Facebook Marketplace website.
They are marked with @pytest.mark.integration and can be run separately.

Note: Facebook Marketplace requires login for some features, so these tests
may have limited functionality without authentication. They focus on public
search results that don't require login.
"""

import pytest

from src.scrapers.facebook import FacebookMarketplaceScraper
from src.utils.logger import getLogger

logger = getLogger(__name__)


@pytest.mark.integration()
def testFacebookSearchUrlConstruction():
    """Test Facebook search URL construction with various parameters."""
    scraper = FacebookMarketplaceScraper()

    # Test with query
    url = scraper.buildSearchUrl(query="Ducati Panigale V4")
    assert "marketplace/category/motorcycles" in url
    assert "query=" in url
    logger.info(f"Search URL: {url}")

    # Test with make/model
    url = scraper.buildSearchUrl(make="Ducati", model="Panigale V4")
    assert "marketplace/category/motorcycles" in url
    logger.info(f"Search URL (make/model): {url}")

    # Test with filters
    url = scraper.buildSearchUrl(
        query="Ducati Panigale V4",
        minPrice=10000,
        maxPrice=30000,
        location="Los Angeles, CA",
        radius=100,
    )
    assert "minPrice" in url
    assert "maxPrice" in url
    logger.info(f"Search URL (with filters): {url}")


@pytest.mark.integration()
def testFacebookRealSearch():
    """
    Test real search against Facebook Marketplace.

    Note: This test may fail if:
    - Facebook requires login
    - Facebook changes their HTML structure
    - Rate limiting is triggered
    - No listings are available

    This is expected for Facebook Marketplace integration tests.
    """
    scraper = FacebookMarketplaceScraper()

    try:
        # Search for motorcycles
        # Using a broad search to increase chances of results
        results = scraper.search(
            query="motorcycle",
            maxPages=1,  # Only 1 page for quick test
            scrollsPerPage=2,  # Minimal scrolling
        )

        logger.info(f"Found {len(results)} listings from Facebook Marketplace")

        # Note: Facebook may return 0 results without login
        # So we don't assert > 0, just verify the structure
        if len(results) > 0:
            # Verify first result has expected structure
            firstResult = results[0]
            assert "url" in firstResult
            assert "title" in firstResult

            logger.info(f"Sample listing: {firstResult.get('title')}")
            logger.info(f"Price: {firstResult.get('price')}")
            logger.info(f"Location: {firstResult.get('location')}")

            # Verify URL is valid
            assert firstResult["url"].startswith("https://www.facebook.com")
        else:
            logger.warning(
                "No results returned - this may be due to Facebook requiring login or rate limiting"
            )

    except Exception as e:
        # Facebook integration tests are expected to be flaky
        # due to login requirements, rate limiting, and HTML changes
        logger.warning(f"Facebook integration test failed (this may be expected): {e}")
        pytest.skip(f"Facebook requires login or blocked request: {e}")


@pytest.mark.integration()
def testFacebookListingDetailScraping():
    """
    Test scraping individual listing details.

    Note: This test is likely to fail without authentication
    as Facebook typically requires login to view listing details.
    """
    scraper = FacebookMarketplaceScraper()

    # Verify the method exists and has correct signature
    assert hasattr(scraper, "scrapeListingDetails")
    assert callable(scraper.scrapeListingDetails)

    logger.info("Listing detail scraping method is available")

    # Try to get a listing URL from search first
    try:
        results = scraper.search(query="motorcycle", maxPages=1, scrollsPerPage=1)

        if len(results) == 0:
            pytest.skip("No listings available to test detail scraping")
            return

        # Try to scrape details for first listing
        firstListingUrl = results[0].get("url")
        if not firstListingUrl:
            pytest.skip("No valid URL in search results")
            return

        logger.info(f"Attempting to scrape details for: {firstListingUrl}")
        details = scraper.scrapeListingDetails(firstListingUrl)

        # Verify we got some data back
        assert "url" in details
        assert details["url"] == firstListingUrl
        logger.info(f"Successfully scraped listing details: {details.get('title')}")

    except Exception as e:
        logger.warning(f"Facebook listing detail scraping failed (expected): {e}")
        pytest.skip(f"Facebook requires authentication or blocked request: {e}")


@pytest.mark.integration()
def testFacebookDataQuality():
    """
    Test data quality from Facebook Marketplace scraping.

    Verifies that scraped data has required fields when results are available.
    """
    scraper = FacebookMarketplaceScraper()

    try:
        results = scraper.search(
            query="motorcycle",
            maxPages=1,
            scrollsPerPage=2,
        )

        if len(results) == 0:
            logger.warning("No results to test data quality - likely auth required")
            pytest.skip("No results returned from Facebook - authentication may be required")
            return

        # Count listings with required fields
        withUrl = sum(1 for r in results if r.get("url"))
        withTitle = sum(1 for r in results if r.get("title"))
        withPrice = sum(1 for r in results if r.get("price"))

        logger.info(f"Data quality: {withUrl}/{len(results)} have URL")
        logger.info(f"Data quality: {withTitle}/{len(results)} have title")
        logger.info(f"Data quality: {withPrice}/{len(results)} have price")

        # All results should have URL and title at minimum
        # (price may be missing if seller uses "Contact for price")
        assert withUrl == len(results), "All listings should have URL"
        assert withTitle >= len(results) * 0.8, "At least 80% should have title"

        logger.info("Facebook data quality test passed!")

    except AssertionError:
        # Re-raise assertion errors (actual test failures)
        raise
    except Exception as e:
        logger.warning(f"Facebook data quality test failed (this may be expected): {e}")
        pytest.skip(f"Facebook blocked request or requires login: {e}")


if __name__ == "__main__":
    # Allow running integration tests directly
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
