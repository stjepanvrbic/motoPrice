"""
Tests for price analysis module.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analysis.priceAnalyzer import PriceAnalyzer, analyzePriceForListing
from src.database import operations as ops
from src.database.base import Base


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


@pytest.fixture(scope="function")
def sampleListings(testSession):
    """Create sample motorcycle listings for testing."""
    # Create a motorcycle
    motorcycle = ops.createMotorcycle(
        testSession,
        make="Ducati",
        model="Panigale V4",
        year=2022,
        displacementCc=1103,
        category="Sport",
    )
    testSession.commit()

    # Create listings with various prices
    prices = [25000, 26000, 27000, 28000, 29000, 30000, 31000, 32000, 33000, 34000]

    listings = []
    for i, price in enumerate(prices):
        listing = ops.createListing(
            testSession,
            motorcycleId=motorcycle.id,
            source="test",
            url=f"https://test.com/listing-{i}",
            title=f"2022 Ducati Panigale V4 - ${price}",
            price=price,
            mileage=5000 + (i * 1000),
            locationCity="Test City",
            locationState="CA",
            description="Test listing",
        )
        listings.append(listing)

    testSession.commit()
    return listings


class TestPriceAnalyzer:
    """Test suite for PriceAnalyzer class."""

    def testInitialization(self, testSession):
        """Test analyzer initialization."""
        analyzer = PriceAnalyzer(testSession)
        assert analyzer.session == testSession

    def testGetMarketStatsSuccess(self, testSession, sampleListings):
        """Test getting market stats with sufficient data."""
        analyzer = PriceAnalyzer(testSession)
        stats = analyzer.getMarketStats("Ducati", "Panigale V4", 2022)

        assert stats is not None
        assert stats.make == "Ducati"
        assert stats.model == "Panigale V4"
        assert stats.year == 2022
        assert stats.sampleSize == 10
        assert stats.average == 29500.0  # Mean of 25k-34k
        assert stats.median == 29500.0  # Median of 25k-34k
        assert stats.minimum == 25000.0
        assert stats.maximum == 34000.0
        assert stats.standardDeviation > 0

    def testGetMarketStatsInsufficientData(self, testSession):
        """Test market stats returns None when insufficient data."""
        analyzer = PriceAnalyzer(testSession)
        # No listings for this motorcycle
        stats = analyzer.getMarketStats("Honda", "CBR1000RR", 2023)
        assert stats is None

    def testGetMarketStatsWithMileageRange(self, testSession, sampleListings):
        """Test market stats with mileage filtering."""
        analyzer = PriceAnalyzer(testSession)
        # Filter to only low mileage bikes (first 7 listings: 5k-11k miles)
        stats = analyzer.getMarketStats("Ducati", "Panigale V4", 2022, mileageRange=(4000, 11000))

        assert stats is not None
        assert stats.sampleSize == 7  # First 7 listings match (5k-11k miles)
        assert stats.average == 28000.0  # Mean of first 7: 25k, 26k, 27k, 28k, 29k, 30k, 31k

    def testAnalyzeListingSuccess(self, testSession, sampleListings):
        """Test analyzing a listing price."""
        analyzer = PriceAnalyzer(testSession)

        # Test listing priced at $25k (lowest in sample, 15.3% below average of 29.5k)
        analysis = analyzer.analyzeListing(25000, "Ducati", "Panigale V4", 2022)

        assert analysis is not None
        assert analysis.listingPrice == 25000
        assert analysis.marketAverage == 29500.0
        assert analysis.sampleSize == 10
        assert analysis.deviationFromAverage < -15  # More than 15% below
        assert analysis.priceScore > 90  # Excellent deal (10-20% below)

    def testAnalyzeListingInsufficientData(self, testSession):
        """Test analyzing listing with no market data."""
        analyzer = PriceAnalyzer(testSession)
        analysis = analyzer.analyzeListing(20000, "Kawasaki", "Ninja H2", 2024)
        assert analysis is None

    def testCalculatePriceScore20PercentBelow(self, testSession):
        """Test price score for listing 20%+ below market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(-20)
        assert score == 100.0

        score = analyzer._calculatePriceScore(-25)
        assert score == 100.0

    def testCalculatePriceScore10To20PercentBelow(self, testSession):
        """Test price score for listing 10-20% below market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(-15)
        assert 90.0 <= score <= 100.0

        score = analyzer._calculatePriceScore(-10)
        assert score == 90.0

    def testCalculatePriceScore5To10PercentBelow(self, testSession):
        """Test price score for listing 5-10% below market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(-7.5)
        assert 80.0 <= score <= 90.0

        # -5 is the boundary, should return 80.0 or start of  within-5% range (70.0)
        score = analyzer._calculatePriceScore(-5.01)
        assert score > 80.0

    def testCalculatePriceScoreWithin5Percent(self, testSession):
        """Test price score for listing within 5% of market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(0)
        assert score == 70.0

        score = analyzer._calculatePriceScore(5)
        assert score == 70.0

        score = analyzer._calculatePriceScore(-5)
        assert score == 70.0  # Upper bound of within-5% range

    def testCalculatePriceScore5To10PercentAbove(self, testSession):
        """Test price score for listing 5-10% above market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(7.5)
        assert 60.0 <= score <= 70.0

        score = analyzer._calculatePriceScore(10)
        assert score == 60.0

    def testCalculatePriceScore10To20PercentAbove(self, testSession):
        """Test price score for listing 10-20% above market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(15)
        assert 40.0 <= score <= 60.0

        score = analyzer._calculatePriceScore(19.99)
        assert score > 40.0

    def testCalculatePriceScore20PercentAbove(self, testSession):
        """Test price score for listing 20%+ above market."""
        analyzer = PriceAnalyzer(testSession)
        score = analyzer._calculatePriceScore(20)
        assert score == 20.0

        score = analyzer._calculatePriceScore(30)
        assert score < 20.0

        score = analyzer._calculatePriceScore(50)
        assert score < 10.0

    def testInterpretScoreExceptional(self, testSession):
        """Test interpretation for exceptional deals."""
        analyzer = PriceAnalyzer(testSession)
        interp = analyzer._interpretScore(96, -22)
        assert "Exceptional" in interp
        assert "22" in interp

    def testInterpretScoreExcellent(self, testSession):
        """Test interpretation for excellent deals."""
        analyzer = PriceAnalyzer(testSession)
        interp = analyzer._interpretScore(88, -15)
        assert "Excellent" in interp

    def testInterpretScoreGood(self, testSession):
        """Test interpretation for good deals."""
        analyzer = PriceAnalyzer(testSession)
        interp = analyzer._interpretScore(78, -7)
        assert "Good" in interp

    def testInterpretScoreFair(self, testSession):
        """Test interpretation for fair deals."""
        analyzer = PriceAnalyzer(testSession)
        interp = analyzer._interpretScore(68, 2)
        assert "Fair" in interp

    def testInterpretScoreHigh(self, testSession):
        """Test interpretation for overpriced listings."""
        analyzer = PriceAnalyzer(testSession)
        interp = analyzer._interpretScore(45, 15)
        assert "High" in interp or "Above" in interp

    def testInterpretScoreVeryHigh(self, testSession):
        """Test interpretation for very overpriced listings."""
        analyzer = PriceAnalyzer(testSession)
        interp = analyzer._interpretScore(25, 35)
        assert "Very high" in interp or "high" in interp.lower()

    def testAnalyzePriceForListingSuccess(self, testSession, sampleListings):
        """Test convenience function for analyzing listing by ID."""
        listing = sampleListings[0]  # First listing (cheapest, ~15% below average)
        analysis = analyzePriceForListing(testSession, listing.id)

        assert analysis is not None
        assert analysis.listingPrice == listing.price
        assert analysis.priceScore >= 85  # Should be excellent deal (10-20% below)

    def testAnalyzePriceForListingNotFound(self, testSession):
        """Test analyzing non-existent listing."""
        analysis = analyzePriceForListing(testSession, 99999)
        assert analysis is None

    def testPercentileCalculations(self, testSession, sampleListings):
        """Test that percentile calculations are accurate."""
        analyzer = PriceAnalyzer(testSession)
        stats = analyzer.getMarketStats("Ducati", "Panigale V4", 2022)

        assert stats is not None
        # With prices 25k-34k, 25th percentile should be around 26.75k-27.25k
        assert 26000 <= stats.percentile25 <= 28000
        # 75th percentile should be around 31.75k-32.25k
        assert 31000 <= stats.percentile75 <= 33000

    def testMileageAdjustedComparison(self, testSession, sampleListings):
        """Test price analysis with mileage adjustment."""
        analyzer = PriceAnalyzer(testSession)

        # Analyze listing with 6000 miles (should compare to similar mileage bikes)
        analysis = analyzer.analyzeListing(27000, "Ducati", "Panigale V4", 2022, mileage=6000)

        assert analysis is not None
        # Market average should be based on similar mileage bikes
        # (mileage range 1000-11000, which includes first few listings)
        assert analysis.marketAverage < 29500  # Lower than overall average

    def testEdgeCaseVeryFewListings(self, testSession):
        """Test behavior with fewer than 5 listings."""
        # Create motorcycle with only 3 listings
        motorcycle = ops.createMotorcycle(
            testSession,
            make="BMW",
            model="S1000RR",
            year=2023,
            displacementCc=999,
            category="Sport",
        )
        testSession.commit()

        for i in range(3):
            ops.createListing(
                testSession,
                motorcycleId=motorcycle.id,
                source="test",
                url=f"https://test.com/bmw-{i}",
                title=f"BMW S1000RR - ${20000 + i * 1000}",
                price=20000 + (i * 1000),
                mileage=5000,
            )
        testSession.commit()

        analyzer = PriceAnalyzer(testSession)
        stats = analyzer.getMarketStats("BMW", "S1000RR", 2023)

        # Should return None (insufficient data)
        assert stats is None

    def testDeviationCalculations(self, testSession, sampleListings):
        """Test deviation percentage calculations."""
        analyzer = PriceAnalyzer(testSession)

        # Market average is 29500
        # Test listing at 25000 should be -15.25% deviation
        analysis = analyzer.analyzeListing(25000, "Ducati", "Panigale V4", 2022)

        assert analysis is not None
        expectedDeviation = ((25000 - 29500) / 29500) * 100  # -15.25%
        assert abs(analysis.deviationFromAverage - expectedDeviation) < 0.1
