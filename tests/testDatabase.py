"""
Tests for database models, connection, and operations.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import operations as ops
from src.database.base import Base
from src.database.connection import DatabaseManager
from src.database.models import Motorcycle


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
def sampleMotorcycle(testSession):
    """Create sample motorcycle for testing."""
    motorcycle = ops.createMotorcycle(
        testSession,
        make="Ducati",
        model="Panigale V4",
        year=2022,
        displacementCc=1103,
        category="Sport",
        msrp=28395.00,
        specs={"hp": 214, "weight": 195},
    )
    testSession.commit()
    return motorcycle


@pytest.fixture(scope="function")
def sampleListing(testSession, sampleMotorcycle):
    """Create sample listing for testing."""
    listing = ops.createListing(
        testSession,
        motorcycleId=sampleMotorcycle.id,
        source="CycleTrader",
        url="https://cycletrader.com/listing/123",
        title="2022 Ducati Panigale V4",
        price=24999.00,
        mileage=1500,
        year=2022,
        locationCity="Los Angeles",
        locationState="CA",
        locationZip="90001",
        description="Clean bike, never dropped",
        sellerType="Private",
        titleStatus="Clean",
        condition="Excellent",
    )
    testSession.commit()
    return listing


# ============================================================================
# Model Tests
# ============================================================================


def testMotorcycleModel(sampleMotorcycle):
    """Motorcycle model creation and relationships."""
    assert sampleMotorcycle.id is not None
    assert sampleMotorcycle.make == "Ducati"
    assert sampleMotorcycle.model == "Panigale V4"
    assert sampleMotorcycle.year == 2022
    assert sampleMotorcycle.displacementCc == 1103
    assert sampleMotorcycle.specs["hp"] == 214
    assert sampleMotorcycle.createdAt is not None


def testListingModel(sampleListing):
    """Listing model creation and relationships."""
    assert sampleListing.id is not None
    assert sampleListing.source == "CycleTrader"
    assert sampleListing.price == 24999.00
    assert sampleListing.mileage == 1500
    assert sampleListing.motorcycle is not None
    assert sampleListing.motorcycle.make == "Ducati"
    assert sampleListing.isActive is True


def testImageModel(testSession, sampleListing):
    """Image model creation."""
    image = ops.createImage(
        testSession, listingId=sampleListing.id, url="https://example.com/image1.jpg", position=1
    )
    testSession.commit()

    assert image.id is not None
    assert image.listingId == sampleListing.id
    assert image.url == "https://example.com/image1.jpg"
    assert image.position == 1


def testPriceHistoryModel(testSession, sampleMotorcycle):
    """PriceHistory model creation."""
    priceHistory = ops.createPriceHistory(
        testSession,
        motorcycleId=sampleMotorcycle.id,
        date=date.today(),
        avgPrice=25000.00,
        medianPrice=24500.00,
        minPrice=22000.00,
        maxPrice=28000.00,
        sampleSize=50,
    )
    testSession.commit()

    assert priceHistory.id is not None
    assert priceHistory.motorcycleId == sampleMotorcycle.id
    assert priceHistory.avgPrice == 25000.00
    assert priceHistory.sampleSize == 50


def testEvaluationModel(testSession, sampleListing):
    """Evaluation model creation."""
    evaluation = ops.createEvaluation(
        testSession,
        listingId=sampleListing.id,
        overallScore=85.5,
        letterGrade="B+",
        priceScore=90.0,
        mileageScore=95.0,
        qualityScore=75.0,
        conditionScore=80.0,
        redFlags={"issues": []},
        recommendations="Good deal, consider buying",
    )
    testSession.commit()

    assert evaluation.id is not None
    assert evaluation.listingId == sampleListing.id
    assert evaluation.overallScore == 85.5
    assert evaluation.letterGrade == "B+"


# ============================================================================
# Motorcycle Operations Tests
# ============================================================================


def testCreateMotorcycle(testSession):
    """Creating motorcycle."""
    motorcycle = ops.createMotorcycle(testSession, make="Honda", model="CBR1000RR", year=2023)
    testSession.commit()

    assert motorcycle.id is not None
    assert motorcycle.make == "Honda"
    assert motorcycle.model == "CBR1000RR"


def testGetMotorcycleById(testSession, sampleMotorcycle):
    """Getting motorcycle by ID."""
    motorcycle = ops.getMotorcycleById(testSession, sampleMotorcycle.id)
    assert motorcycle is not None
    assert motorcycle.id == sampleMotorcycle.id
    assert motorcycle.make == "Ducati"


def testFindMotorcycle(testSession, sampleMotorcycle):
    """Finding motorcycle by make, model, year."""
    motorcycle = ops.findMotorcycle(testSession, "Ducati", "Panigale V4", 2022)
    assert motorcycle is not None
    assert motorcycle.id == sampleMotorcycle.id


def testGetOrCreateMotorcycle(testSession):
    """Get or create motorcycle."""
    # First call creates
    moto1 = ops.getOrCreateMotorcycle(testSession, "Yamaha", "R1", 2023, displacementCc=998)
    testSession.commit()

    # Second call retrieves existing
    moto2 = ops.getOrCreateMotorcycle(testSession, "Yamaha", "R1", 2023)

    assert moto1.id == moto2.id


# ============================================================================
# Listing Operations Tests
# ============================================================================


def testCreateListing(testSession, sampleMotorcycle):
    """Creating listing."""
    listing = ops.createListing(
        testSession,
        motorcycleId=sampleMotorcycle.id,
        source="Facebook",
        url="https://facebook.com/marketplace/123",
        price=23000.00,
    )
    testSession.commit()

    assert listing.id is not None
    assert listing.source == "Facebook"


def testGetListingByUrl(testSession, sampleListing):
    """Getting listing by URL."""
    listing = ops.getListingByUrl(testSession, "https://cycletrader.com/listing/123")
    assert listing is not None
    assert listing.id == sampleListing.id


def testUpdateListing(testSession, sampleListing):
    """Updating listing."""
    updated = ops.updateListing(testSession, sampleListing, price=23500.00, mileage=2000)
    testSession.commit()

    assert updated.price == 23500.00
    assert updated.mileage == 2000


def testGetListingsByMotorcycle(testSession, sampleMotorcycle):
    """Getting listings by motorcycle."""
    # Create second listing
    ops.createListing(
        testSession,
        motorcycleId=sampleMotorcycle.id,
        source="eBay",
        url="https://ebay.com/item/456",
        price=26000.00,
    )
    testSession.commit()

    listings = ops.getListingsByMotorcycle(testSession, sampleMotorcycle.id)
    assert len(listings) >= 1


def testSearchListings(testSession, sampleListing):
    """Searching listings with filters."""
    results = ops.searchListings(testSession, make="Ducati", priceMin=20000.00, priceMax=30000.00)
    assert len(results) >= 1
    assert all(listing.price >= 20000 for listing in results)
    assert all(listing.price <= 30000 for listing in results)


# ============================================================================
# Image Operations Tests
# ============================================================================


def testGetImagesByListing(testSession, sampleListing):
    """Getting images by listing."""
    ops.createImage(testSession, sampleListing.id, "url1.jpg", position=1)
    ops.createImage(testSession, sampleListing.id, "url2.jpg", position=2)
    testSession.commit()

    images = ops.getImagesByListing(testSession, sampleListing.id)
    assert len(images) == 2
    assert images[0].position == 1
    assert images[1].position == 2


def testUpdateImageAnalysis(testSession, sampleListing):
    """Updating image AI analysis."""
    image = ops.createImage(testSession, sampleListing.id, "url.jpg")
    testSession.commit()

    analysis = {"condition": "excellent", "damage": []}
    updated = ops.updateImageAnalysis(testSession, image.id, analysis)
    testSession.commit()

    assert updated.aiAnalysis == analysis
    assert updated.analyzedAt is not None


# ============================================================================
# Price History Operations Tests
# ============================================================================


def testGetPriceHistory(testSession, sampleMotorcycle):
    """Getting price history."""
    today = date.today()
    ops.createPriceHistory(testSession, sampleMotorcycle.id, today, avgPrice=25000.00)
    testSession.commit()

    history = ops.getPriceHistory(testSession, sampleMotorcycle.id)
    assert len(history) >= 1
    assert history[0].avgPrice == 25000.00


# ============================================================================
# Evaluation Operations Tests
# ============================================================================


def testGetEvaluationByListing(testSession, sampleListing):
    """Getting evaluation by listing."""
    ops.createEvaluation(testSession, sampleListing.id, overallScore=85.0, letterGrade="B")
    testSession.commit()

    evaluation = ops.getEvaluationByListing(testSession, sampleListing.id)
    assert evaluation is not None
    assert evaluation.overallScore == 85.0


def testGetTopListings(testSession, sampleListing):
    """Getting top-rated listings."""
    ops.createEvaluation(testSession, sampleListing.id, overallScore=95.0, letterGrade="A")
    testSession.commit()

    topListings = ops.getTopListings(testSession, minScore=90.0)
    assert len(topListings) >= 1
    assert all(e.overallScore >= 90.0 for e in topListings)


# ============================================================================
# Bulk Operations Tests
# ============================================================================


def testBulkCreateListings(testSession, sampleMotorcycle):
    """Bulk creating listings."""
    listingsData = [
        {
            "motorcycleId": sampleMotorcycle.id,
            "source": "CycleTrader",
            "url": f"https://cycletrader.com/{i}",
            "price": 25000.00 + (i * 100),
        }
        for i in range(10)
    ]

    count = ops.bulkCreateListings(testSession, listingsData)
    testSession.commit()

    assert count == 10


def testUpsertListingCreate(testSession, sampleMotorcycle):
    """Upsert creates new listing when URL doesn't exist."""
    url = "https://cycletrader.com/new-listing"
    listing, wasCreated = ops.upsertListing(
        testSession,
        url=url,
        motorcycleId=sampleMotorcycle.id,
        source="CycleTrader",
        price=25000.00,
        mileage=1000,
    )
    testSession.commit()

    assert wasCreated is True
    assert listing.url == url
    assert listing.price == 25000.00
    assert listing.mileage == 1000


def testUpsertListingUpdate(testSession, sampleListing):
    """Upsert updates existing listing when URL exists."""
    originalUpdatedAt = sampleListing.updatedAt

    import time

    time.sleep(0.01)  # Ensure timestamp difference

    listing, wasCreated = ops.upsertListing(
        testSession, url=sampleListing.url, price=30000.00, mileage=2000
    )
    testSession.commit()

    assert wasCreated is False
    assert listing.id == sampleListing.id
    assert listing.price == 30000.00
    assert listing.mileage == 2000
    assert listing.updatedAt > originalUpdatedAt


def testBulkUpsertListingsWithDeduplication(testSession, sampleMotorcycle):
    """Bulk upsert handles both new and existing listings."""
    ops.createListing(
        testSession,
        motorcycleId=sampleMotorcycle.id,
        source="CycleTrader",
        url="https://cycletrader.com/existing",
        price=20000.00,
    )
    testSession.commit()

    listingsData = [
        {
            "motorcycleId": sampleMotorcycle.id,
            "source": "CycleTrader",
            "url": "https://cycletrader.com/existing",
            "price": 22000.00,
        },
        {
            "motorcycleId": sampleMotorcycle.id,
            "source": "CycleTrader",
            "url": "https://cycletrader.com/new1",
            "price": 25000.00,
        },
        {
            "motorcycleId": sampleMotorcycle.id,
            "source": "CycleTrader",
            "url": "https://cycletrader.com/new2",
            "price": 26000.00,
        },
    ]

    result = ops.bulkUpsertListings(testSession, listingsData)
    testSession.commit()

    assert result["created"] == 2
    assert result["updated"] == 1
    assert result["total"] == 3

    updatedListing = ops.getListingByUrl(testSession, "https://cycletrader.com/existing")
    assert updatedListing.price == 22000.00


def testBulkInsertPerformance(testSession, sampleMotorcycle):
    """Bulk insert 1000 records in under 10 seconds."""
    import time

    listingsData = [
        {
            "motorcycleId": sampleMotorcycle.id,
            "source": "CycleTrader",
            "url": f"https://cycletrader.com/perf-{i}",
            "price": 25000.00,
        }
        for i in range(1000)
    ]

    startTime = time.time()
    count = ops.bulkCreateListings(testSession, listingsData)
    testSession.commit()
    endTime = time.time()

    elapsed = endTime - startTime

    assert count == 1000
    assert elapsed < 10.0, f"Bulk insert took {elapsed:.2f}s, should be < 10s"


def testDeduplicationSameUrlTwice(testSession, sampleMotorcycle):
    """Inserting same URL twice via upsert doesn't create duplicates."""
    url = "https://cycletrader.com/duplicate-test"

    listing1, created1 = ops.upsertListing(
        testSession,
        url=url,
        motorcycleId=sampleMotorcycle.id,
        source="CycleTrader",
        price=20000.00,
    )
    testSession.commit()

    listing2, created2 = ops.upsertListing(testSession, url=url, price=22000.00, mileage=1500)
    testSession.commit()

    assert created1 is True
    assert created2 is False
    assert listing1.id == listing2.id
    assert listing2.price == 22000.00
    assert listing2.mileage == 1500

    allWithUrl = testSession.query(ops.Listing).filter_by(url=url).all()
    assert len(allWithUrl) == 1


def testTransactionRollbackOnError(testSession, sampleMotorcycle):
    """Transaction rolls back on error."""
    initialCount = testSession.query(ops.Listing).count()

    try:
        ops.createListing(
            testSession,
            motorcycleId=sampleMotorcycle.id,
            source="CycleTrader",
            url="https://cycletrader.com/rollback-test-1",
            price=25000.00,
        )

        # Create listing with duplicate URL to trigger IntegrityError
        ops.createListing(
            testSession,
            motorcycleId=sampleMotorcycle.id,
            source="CycleTrader",
            url="https://cycletrader.com/rollback-test-1",  # Same URL
            price=30000.00,
        )

        testSession.commit()
    except Exception:
        testSession.rollback()

    # After rollback, count should be same as before
    finalCount = testSession.query(ops.Listing).count()
    assert (
        finalCount == initialCount
    ), "Rollback should have removed all listings from failed transaction"


def testTimestampTracking(testSession, sampleListing):
    """Timestamps are tracked correctly."""
    import time

    originalScrapedAt = sampleListing.scrapedAt
    originalUpdatedAt = sampleListing.updatedAt

    assert originalScrapedAt is not None
    assert originalUpdatedAt is not None

    time.sleep(0.01)

    ops.updateListing(testSession, sampleListing, price=30000.00)
    testSession.commit()

    assert sampleListing.scrapedAt == originalScrapedAt
    assert sampleListing.updatedAt > originalUpdatedAt


# ============================================================================
# Connection Manager Tests
# ============================================================================


def testDatabaseManagerInitialization():
    """Database manager initialization."""
    dbManager = DatabaseManager("sqlite:///:memory:")
    assert dbManager.engine is not None
    assert dbManager.SessionFactory is not None
    dbManager.dispose()


def testGetSessionContextManager():
    """Session context manager."""
    dbManager = DatabaseManager("sqlite:///:memory:")
    dbManager.createTables()

    with dbManager.getSession() as session:
        motorcycle = Motorcycle(make="Test", model="Bike", year=2023)
        session.add(motorcycle)

    # Verify data persisted
    with dbManager.getSession() as session:
        result = session.query(Motorcycle).filter_by(make="Test").first()
        assert result is not None
        assert result.model == "Bike"

    dbManager.dispose()


def testSessionRollbackOnError():
    """Session rollback on error."""
    dbManager = DatabaseManager("sqlite:///:memory:")
    dbManager.createTables()

    try:
        with dbManager.getSession() as session:
            motorcycle = Motorcycle(make="Test", model="Bike", year=2023)
            session.add(motorcycle)
            raise ValueError("Test error")
    except ValueError:
        pass

    # Verify rollback occurred
    with dbManager.getSession() as session:
        count = session.query(Motorcycle).count()
        assert count == 0

    dbManager.dispose()


# ============================================================================
# Foreign Key Constraint Tests
# ============================================================================


def testListingMotorcycleForeignKey(testSession, sampleMotorcycle):
    """Listing references valid motorcycle."""
    listing = ops.createListing(
        testSession, motorcycleId=sampleMotorcycle.id, source="Test", url="https://test.com/1"
    )
    testSession.commit()

    assert listing.motorcycle.id == sampleMotorcycle.id
    assert listing.motorcycle.make == "Ducati"


def testCascadeDeleteListingImages(testSession, sampleListing):
    """Deleting listing cascades to images."""
    ops.createImage(testSession, sampleListing.id, "url1.jpg")
    ops.createImage(testSession, sampleListing.id, "url2.jpg")
    testSession.commit()

    listingId = sampleListing.id

    testSession.delete(sampleListing)
    testSession.commit()

    # Verify images deleted
    images = ops.getImagesByListing(testSession, listingId)
    assert len(images) == 0
