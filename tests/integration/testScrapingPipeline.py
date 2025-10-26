"""
End-to-end integration tests for the complete scraping pipeline.

Tests the full workflow: scrape → normalize → database insert → verify data integrity.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import operations as ops
from src.database.base import Base
from src.scrapers.cycletrader import CycleTraderScraper
from src.utils.normalizers import normalizeListing


@pytest.fixture(scope="function")
def testEngine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def testSession(testEngine):
    """Create test database session."""
    SessionFactory = sessionmaker(bind=testEngine)
    session = SessionFactory()
    yield session
    session.rollback()
    session.close()


@pytest.mark.integration()
class TestScrapingPipeline:
    """End-to-end tests for complete scraping pipeline."""

    def testCycleTraderScrapeToDatabaseFlow(self, testSession):
        """
        Test complete flow: scrape CycleTrader → normalize → insert to database.

        This tests the integration of:
        - CycleTraderScraper.scrapeListings()
        - normalizeListing() for data validation
        - upsertListing() for database insertion
        - Data integrity throughout the pipeline
        """
        # Step 1: Scrape real listings from CycleTrader
        scraper = CycleTraderScraper()
        searchUrl = scraper.buildSearchUrl(make="Ducati", model="Panigale V4", maxResults=5)

        rawListings = scraper.scrapeSearchResults(searchUrl, max_pages=1)[:5]

        # Verify scraping worked
        assert len(rawListings) > 0, "Should scrape at least one listing"
        assert len(rawListings) <= 5, "Limited to 5 listings"

        # Step 2: Normalize and insert each listing
        insertedCount = 0
        for rawListing in rawListings:
            # Normalize the raw scraped data
            normalized = normalizeListing(
                source="CycleTrader",
                rawData=rawListing,
            )

            # Verify normalization worked
            assert normalized.url is not None, "Normalized listing must have URL"
            assert normalized.year is not None, "Normalized listing must have year"
            assert normalized.make is not None, "Normalized listing must have make"
            assert normalized.model is not None, "Normalized listing must have model"

            # Get or create motorcycle
            motorcycle = ops.getOrCreateMotorcycle(
                testSession,
                make=normalized.make,
                model=normalized.model,
                year=normalized.year,
            )
            testSession.flush()

            # Insert listing into database using upsert (deduplication)
            listing, wasCreated = ops.upsertListing(
                testSession,
                url=normalized.url,
                source=normalized.source,
                motorcycleId=motorcycle.id,
                title=normalized.title,
                price=normalized.price,
                mileage=normalized.mileage,
                year=normalized.year,
                locationCity=normalized.locationCity,
                locationState=normalized.locationState,
                locationZip=normalized.locationZip,
                description=normalized.description,
                sellerType=normalized.sellerType,
                condition=normalized.condition,
            )

            if wasCreated:
                insertedCount += 1

            # Store images if present
            if normalized.imageUrls:
                for position, imageUrl in enumerate(normalized.imageUrls):
                    ops.createImage(
                        testSession,
                        listingId=listing.id,
                        url=imageUrl,
                        position=position,
                    )

        testSession.commit()

        # Step 3: Verify data integrity in database
        assert insertedCount > 0, "Should have inserted at least one new listing"

        # Verify motorcycles were created
        motorcycles = testSession.query(ops.Motorcycle).all()
        assert len(motorcycles) > 0, "Should have created motorcycle records"

        # Verify listings were created
        listings = testSession.query(ops.Listing).all()
        assert len(listings) == insertedCount, f"Should have {insertedCount} listings in database"

        # Verify all listings have required fields
        for listing in listings:
            assert listing.url is not None, "Listing must have URL"
            assert listing.source == "CycleTrader", "Listing must have correct source"
            assert listing.motorcycle is not None, "Listing must have motorcycle relationship"
            assert listing.year is not None, "Listing must have year"
            assert listing.scrapedAt is not None, "Listing must have scrapedAt timestamp"

        # Verify images were stored (if any listings had images)
        images = testSession.query(ops.Image).all()
        if images:
            assert len(images) > 0, "Should have image records if listings had images"
            for image in images:
                assert image.url is not None, "Image must have URL"
                assert image.listing is not None, "Image must have listing relationship"

    def testDeduplicationOnRepeatScrape(self, testSession):
        """
        Test that re-scraping same listings doesn't create duplicates.

        Tests:
        - First scrape creates new listings
        - Second scrape updates existing listings
        - No duplicate URLs in database
        """
        scraper = CycleTraderScraper()
        searchUrl = scraper.buildSearchUrl(make="Ducati", model="Panigale V4", maxResults=3)

        # First scrape
        rawListings1 = scraper.scrapeSearchResults(searchUrl, max_pages=1)[:3]
        for rawListing in rawListings1:
            normalized = normalizeListing(source="CycleTrader", rawData=rawListing)
            motorcycle = ops.getOrCreateMotorcycle(
                testSession, make=normalized.make, model=normalized.model, year=normalized.year
            )
            ops.upsertListing(
                testSession,
                url=normalized.url,
                source=normalized.source,
                motorcycleId=motorcycle.id,
                title=normalized.title,
            )
        testSession.commit()

        initialListingCount = testSession.query(ops.Listing).count()

        # Second scrape (same search)
        rawListings2 = scraper.scrapeSearchResults(searchUrl, max_pages=1)[:3]
        for rawListing in rawListings2:
            normalized = normalizeListing(source="CycleTrader", rawData=rawListing)
            motorcycle = ops.getOrCreateMotorcycle(
                testSession, make=normalized.make, model=normalized.model, year=normalized.year
            )
            ops.upsertListing(
                testSession,
                url=normalized.url,
                source=normalized.source,
                motorcycleId=motorcycle.id,
                title=normalized.title,
            )
        testSession.commit()

        finalListingCount = testSession.query(ops.Listing).count()

        # Verify no duplicates were created
        assert finalListingCount == initialListingCount, "Re-scraping should not create duplicates"

        # Verify no duplicate URLs exist
        urls = [listing.url for listing in testSession.query(ops.Listing).all()]
        assert len(urls) == len(set(urls)), "All listing URLs should be unique"

    def testDataValidityAfterNormalization(self, testSession):
        """
        Test that normalized data meets quality standards.

        Verifies:
        - Required fields are present
        - Data types are correct
        - Values are within expected ranges
        """
        scraper = CycleTraderScraper()
        searchUrl = scraper.buildSearchUrl(make="Ducati", model="Panigale V4", maxResults=5)

        rawListings = scraper.scrapeSearchResults(searchUrl, max_pages=1)[:5]

        for rawListing in rawListings:
            normalized = normalizeListing(source="CycleTrader", rawData=rawListing)

            # Required fields
            assert normalized.url, "Must have URL"
            assert normalized.source == "CycleTrader", "Must have correct source"
            assert normalized.year, "Must have year"
            assert normalized.make, "Must have make"
            assert normalized.model, "Must have model"

            # Data types
            assert isinstance(normalized.year, int), "Year must be integer"
            if normalized.price:
                assert isinstance(normalized.price, int | float), "Price must be numeric"
                assert normalized.price > 0, "Price must be positive"
            if normalized.mileage:
                assert isinstance(normalized.mileage, int), "Mileage must be integer"
                assert normalized.mileage >= 0, "Mileage must be non-negative"

            # Value ranges
            currentYear = 2025
            assert (
                1900 <= normalized.year <= currentYear
            ), f"Year {normalized.year} must be reasonable"
            if normalized.price:
                assert (
                    100 <= normalized.price <= 1000000
                ), f"Price {normalized.price} must be in reasonable range"

    def testPriceAnalysisOnScrapedData(self, testSession):
        """
        Test price analysis integration with scraped data.

        Verifies that price analysis module works with real scraped listings.
        """
        from src.analysis.priceAnalyzer import PriceAnalyzer

        # Scrape listings
        scraper = CycleTraderScraper()
        searchUrl = scraper.buildSearchUrl(make="Ducati", model="Panigale V4", maxResults=10)
        rawListings = scraper.scrapeSearchResults(searchUrl, max_pages=1)[:10]

        # Insert into database
        for rawListing in rawListings:
            normalized = normalizeListing(source="CycleTrader", rawData=rawListing)
            motorcycle = ops.getOrCreateMotorcycle(
                testSession, make=normalized.make, model=normalized.model, year=normalized.year
            )
            ops.upsertListing(
                testSession,
                url=normalized.url,
                source=normalized.source,
                motorcycleId=motorcycle.id,
                price=normalized.price,
                mileage=normalized.mileage,
                year=normalized.year,
            )
        testSession.commit()

        # Test price analysis on scraped data
        analyzer = PriceAnalyzer(testSession)
        listings = testSession.query(ops.Listing).filter(ops.Listing.price.isnot(None)).all()

        if len(listings) >= 5:
            # Analyze first listing with price
            testListing = listings[0]
            motorcycle = testListing.motorcycle

            stats = analyzer.getMarketStats(motorcycle.make, motorcycle.model, motorcycle.year)

            assert stats is not None, "Should get market stats with enough data"
            assert stats.sampleSize >= 5, "Should have at least 5 listings"
            assert stats.average > 0, "Average price should be positive"
            assert stats.median > 0, "Median price should be positive"

            # Analyze specific listing
            analysis = analyzer.analyzeListing(testListing.id)

            assert analysis is not None, "Should get price analysis"
            assert 0 <= analysis.priceScore <= 100, "Price score should be 0-100"
            assert analysis.listingPrice == testListing.price, "Should match listing price"
