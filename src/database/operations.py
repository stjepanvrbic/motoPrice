"""
Database CRUD operations for all models.
"""

from datetime import date, datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from .models import Evaluation, Image, Listing, Motorcycle, PriceHistory

# ============================================================================
# Motorcycle Operations
# ============================================================================


def createMotorcycle(
    session: Session,
    make: str,
    model: str,
    year: int,
    displacementCc: int | None = None,
    category: str | None = None,
    msrp: float | None = None,
    specs: dict | None = None,
) -> Motorcycle:
    """Create a new motorcycle record."""
    motorcycle = Motorcycle(
        make=make,
        model=model,
        year=year,
        displacementCc=displacementCc,
        category=category,
        msrp=msrp,
        specs=specs,
    )
    session.add(motorcycle)
    session.flush()
    return motorcycle


def getMotorcycleById(session: Session, motorcycleId: int) -> Motorcycle | None:
    """Get motorcycle by ID."""
    return session.get(Motorcycle, motorcycleId)


def findMotorcycle(session: Session, make: str, model: str, year: int) -> Motorcycle | None:
    """Find motorcycle by make, model, and year."""
    stmt = select(Motorcycle).where(
        and_(Motorcycle.make == make, Motorcycle.model == model, Motorcycle.year == year)
    )
    return session.execute(stmt).scalar_one_or_none()


def getOrCreateMotorcycle(
    session: Session, make: str, model: str, year: int, **kwargs
) -> Motorcycle:
    """Get existing motorcycle or create new one."""
    motorcycle = findMotorcycle(session, make, model, year)
    if motorcycle is None:
        motorcycle = createMotorcycle(session, make, model, year, **kwargs)
    return motorcycle


# ============================================================================
# Listing Operations
# ============================================================================


def createListing(session: Session, source: str, url: str, **kwargs) -> Listing:
    """Create a new listing record."""
    listing = Listing(source=source, url=url, **kwargs)
    session.add(listing)
    session.flush()
    return listing


def getListingById(session: Session, listingId: int) -> Listing | None:
    """Get listing by ID."""
    return session.get(Listing, listingId)


def getListingByUrl(session: Session, url: str) -> Listing | None:
    """Get listing by URL."""
    stmt = select(Listing).where(Listing.url == url)
    return session.execute(stmt).scalar_one_or_none()


def updateListing(session: Session, listing: Listing, **kwargs) -> Listing:
    """Update listing fields."""
    for key, value in kwargs.items():
        if hasattr(listing, key):
            setattr(listing, key, value)
    listing.updatedAt = datetime.now()
    session.flush()
    return listing


def getListingsByMotorcycle(
    session: Session, motorcycleId: int, activeOnly: bool = True
) -> list[Listing]:
    """Get all listings for a motorcycle."""
    stmt = select(Listing).where(Listing.motorcycleId == motorcycleId)
    if activeOnly:
        stmt = stmt.where(Listing.isActive == True)  # noqa: E712
    return list(session.execute(stmt).scalars())


def searchListings(
    session: Session,
    make: str | None = None,
    model: str | None = None,
    yearMin: int | None = None,
    yearMax: int | None = None,
    priceMin: float | None = None,
    priceMax: float | None = None,
    mileageMax: int | None = None,
    source: str | None = None,
    activeOnly: bool = True,
    limit: int = 100,
) -> list[Listing]:
    """Search listings with filters."""
    stmt = select(Listing)

    filters = []
    if activeOnly:
        filters.append(Listing.isActive == True)  # noqa: E712
    if yearMin:
        filters.append(Listing.year >= yearMin)
    if yearMax:
        filters.append(Listing.year <= yearMax)
    if priceMin:
        filters.append(Listing.price >= priceMin)
    if priceMax:
        filters.append(Listing.price <= priceMax)
    if mileageMax:
        filters.append(Listing.mileage <= mileageMax)
    if source:
        filters.append(Listing.source == source)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Join with motorcycle for make/model filtering
    if make or model:
        stmt = stmt.join(Listing.motorcycle)
        if make:
            stmt = stmt.where(Motorcycle.make == make)
        if model:
            stmt = stmt.where(Motorcycle.model == model)

    stmt = stmt.order_by(desc(Listing.scrapedAt)).limit(limit)
    return list(session.execute(stmt).scalars())


# ============================================================================
# Image Operations
# ============================================================================


def createImage(
    session: Session, listingId: int, url: str, position: int = 0, aiAnalysis: dict | None = None
) -> Image:
    """Create a new image record."""
    image = Image(listingId=listingId, url=url, position=position, aiAnalysis=aiAnalysis)
    session.add(image)
    session.flush()
    return image


def getImagesByListing(session: Session, listingId: int) -> list[Image]:
    """Get all images for a listing, ordered by position."""
    stmt = select(Image).where(Image.listingId == listingId).order_by(Image.position)
    return list(session.execute(stmt).scalars())


def updateImageAnalysis(session: Session, imageId: int, aiAnalysis: dict) -> Image | None:
    """Update image AI analysis."""
    image = session.get(Image, imageId)
    if image:
        image.aiAnalysis = aiAnalysis
        image.analyzedAt = datetime.now()
        session.flush()
    return image


# ============================================================================
# Price History Operations
# ============================================================================


def createPriceHistory(
    session: Session,
    motorcycleId: int,
    date: date,
    avgPrice: float | None = None,
    medianPrice: float | None = None,
    minPrice: float | None = None,
    maxPrice: float | None = None,
    sampleSize: int | None = None,
) -> PriceHistory:
    """Create a price history record."""
    priceHistory = PriceHistory(
        motorcycleId=motorcycleId,
        date=date,
        avgPrice=avgPrice,
        medianPrice=medianPrice,
        minPrice=minPrice,
        maxPrice=maxPrice,
        sampleSize=sampleSize,
    )
    session.add(priceHistory)
    session.flush()
    return priceHistory


def getPriceHistory(
    session: Session,
    motorcycleId: int,
    startDate: date | None = None,
    endDate: date | None = None,
) -> list[PriceHistory]:
    """Get price history for a motorcycle within date range."""
    stmt = select(PriceHistory).where(PriceHistory.motorcycleId == motorcycleId)

    if startDate:
        stmt = stmt.where(PriceHistory.date >= startDate)
    if endDate:
        stmt = stmt.where(PriceHistory.date <= endDate)

    stmt = stmt.order_by(PriceHistory.date)
    return list(session.execute(stmt).scalars())


# ============================================================================
# Evaluation Operations
# ============================================================================


def createEvaluation(
    session: Session,
    listingId: int,
    overallScore: float,
    letterGrade: str,
    priceScore: float | None = None,
    mileageScore: float | None = None,
    qualityScore: float | None = None,
    conditionScore: float | None = None,
    redFlags: dict | None = None,
    recommendations: str | None = None,
    comparableListings: dict | None = None,
) -> Evaluation:
    """Create an evaluation record."""
    evaluation = Evaluation(
        listingId=listingId,
        overallScore=overallScore,
        letterGrade=letterGrade,
        priceScore=priceScore,
        mileageScore=mileageScore,
        qualityScore=qualityScore,
        conditionScore=conditionScore,
        redFlags=redFlags,
        recommendations=recommendations,
        comparableListings=comparableListings,
    )
    session.add(evaluation)
    session.flush()
    return evaluation


def getEvaluationByListing(session: Session, listingId: int) -> Evaluation | None:
    """Get most recent evaluation for a listing."""
    stmt = (
        select(Evaluation)
        .where(Evaluation.listingId == listingId)
        .order_by(desc(Evaluation.evaluatedAt))
    )
    return session.execute(stmt).scalars().first()


def getTopListings(session: Session, minScore: float = 80.0, limit: int = 20) -> list[Evaluation]:
    """Get top-rated listings."""
    stmt = (
        select(Evaluation)
        .where(Evaluation.overallScore >= minScore)
        .order_by(desc(Evaluation.overallScore))
        .limit(limit)
    )
    return list(session.execute(stmt).scalars())


# ============================================================================
# Bulk Operations
# ============================================================================


def bulkCreateListings(session: Session, listings: list[dict]) -> int:
    """
    Bulk insert listings.

    Args:
        session: Database session
        listings: List of listing dictionaries

    Returns:
        Number of listings inserted
    """
    listingObjects = [Listing(**data) for data in listings]
    session.bulk_save_objects(listingObjects)
    session.flush()
    return len(listingObjects)


def deactivateOldListings(session: Session, daysSinceUpdate: int = 30) -> int:
    """
    Mark listings as inactive if not updated recently.

    Args:
        session: Database session
        daysSinceUpdate: Days since last update

    Returns:
        Number of listings deactivated
    """
    from datetime import timedelta

    cutoffDate = datetime.now() - timedelta(days=daysSinceUpdate)
    stmt = select(Listing).where(
        and_(Listing.isActive == True, Listing.updatedAt < cutoffDate)  # noqa: E712
    )
    listings = list(session.execute(stmt).scalars())

    for listing in listings:
        listing.isActive = False

    session.flush()
    return len(listings)
