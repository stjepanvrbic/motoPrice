"""
SQLAlchemy database models for motoPrice.
"""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

# Use JSONB for PostgreSQL, fallback to JSON for other databases
try:
    JSONType = JSONB
except Exception:
    JSONType = JSON


class Motorcycle(Base):
    """Reference data for motorcycle specifications."""

    __tablename__ = "motorcycles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    displacementCc = Column("displacement_cc", Integer)
    category = Column(String(50))  # Sport, Cruiser, Touring, etc.
    msrp = Column(Numeric(10, 2))
    specs = Column(JSON().with_variant(JSONB, "postgresql"))  # Additional specs (weight, HP, etc.)
    createdAt = Column("created_at", TIMESTAMP, server_default=func.now(), nullable=False)
    updatedAt = Column(
        "updated_at", TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    listings = relationship("Listing", back_populates="motorcycle")
    priceHistory = relationship("PriceHistory", back_populates="motorcycle")

    # Indexes
    __table_args__ = (Index("idx_motorcycle_make_model_year", "make", "model", "year"),)

    def __repr__(self):
        return f"<Motorcycle(id={self.id}, make='{self.make}', model='{self.model}', year={self.year})>"


class Listing(Base):
    """Scraped motorcycle listings."""

    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    motorcycleId = Column("motorcycle_id", Integer, ForeignKey("motorcycles.id"))
    source = Column(String(50), nullable=False)  # CycleTrader, Facebook, eBay
    url = Column(Text, unique=True, nullable=False)
    title = Column(Text)
    price = Column(Numeric(10, 2))
    mileage = Column(Integer)
    year = Column(Integer)  # Denormalized for queries
    locationCity = Column("location_city", String(100))
    locationState = Column("location_state", String(50))
    locationZip = Column("location_zip", String(10))
    description = Column(Text)
    sellerType = Column("seller_type", String(50))  # Private, Dealer
    titleStatus = Column("title_status", String(50))  # Clean, Salvage, Rebuilt
    condition = Column(String(50))  # Excellent, Good, Fair, Poor
    modifications = Column(Text)
    isActive = Column("is_active", Boolean, default=True)
    scrapedAt = Column("scraped_at", TIMESTAMP, server_default=func.now(), nullable=False)
    updatedAt = Column(
        "updated_at", TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    listingMetadata = Column(
        "metadata", JSON().with_variant(JSONB, "postgresql")
    )  # Additional unstructured data

    # Relationships
    motorcycle = relationship("Motorcycle", back_populates="listings")
    images = relationship("Image", back_populates="listing", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="listing", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_listing_source", "source"),
        Index("idx_listing_year_make", "year", "motorcycle_id"),
        Index("idx_listing_price", "price"),
        Index("idx_listing_active", "is_active"),
        Index("idx_listing_scraped_at", "scraped_at"),
    )

    def __repr__(self):
        return f"<Listing(id={self.id}, source='{self.source}', price={self.price}, url='{self.url[:50]}...')>"


class Image(Base):
    """Listing images and AI analysis results."""

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listingId = Column("listing_id", Integer, ForeignKey("listings.id"), nullable=False)
    url = Column(Text, nullable=False)
    position = Column(Integer, default=0)  # Order in listing
    aiAnalysis = Column(
        "ai_analysis", JSON().with_variant(JSONB, "postgresql")
    )  # GPT-4 Vision analysis results
    analyzedAt = Column("analyzed_at", TIMESTAMP)
    createdAt = Column("created_at", TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    listing = relationship("Listing", back_populates="images")

    # Indexes
    __table_args__ = (Index("idx_image_listing", "listing_id"),)

    def __repr__(self):
        return f"<Image(id={self.id}, listing_id={self.listingId}, position={self.position})>"


class PriceHistory(Base):
    """Historical price tracking."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    motorcycleId = Column("motorcycle_id", Integer, ForeignKey("motorcycles.id"), nullable=False)
    avgPrice = Column("avg_price", Numeric(10, 2))
    medianPrice = Column("median_price", Numeric(10, 2))
    minPrice = Column("min_price", Numeric(10, 2))
    maxPrice = Column("max_price", Numeric(10, 2))
    sampleSize = Column("sample_size", Integer)
    date = Column(Date, nullable=False)
    createdAt = Column("created_at", TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    motorcycle = relationship("Motorcycle", back_populates="priceHistory")

    # Indexes
    __table_args__ = (Index("idx_price_history_motorcycle_date", "motorcycle_id", "date"),)

    def __repr__(self):
        return f"<PriceHistory(id={self.id}, motorcycle_id={self.motorcycleId}, date={self.date}, avg={self.avgPrice})>"


class Evaluation(Base):
    """Listing evaluation scores and breakdown."""

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listingId = Column("listing_id", Integer, ForeignKey("listings.id"), nullable=False)
    overallScore = Column("overall_score", Numeric(5, 2))  # 0-100
    letterGrade = Column("letter_grade", String(2))  # A+, A, A-, B+, etc.
    priceScore = Column("price_score", Numeric(5, 2))  # 0-100
    mileageScore = Column("mileage_score", Numeric(5, 2))  # 0-100
    qualityScore = Column("quality_score", Numeric(5, 2))  # 0-100
    conditionScore = Column("condition_score", Numeric(5, 2))  # 0-100
    redFlags = Column(
        "red_flags", JSON().with_variant(JSONB, "postgresql")
    )  # Array of detected issues
    recommendations = Column(Text)
    comparableListings = Column(
        "comparable_listings", JSON().with_variant(JSONB, "postgresql")
    )  # Similar listings
    evaluatedAt = Column("evaluated_at", TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    listing = relationship("Listing", back_populates="evaluations")

    # Indexes
    __table_args__ = (
        Index("idx_evaluation_listing", "listing_id"),
        Index("idx_evaluation_score", "overall_score"),
    )

    def __repr__(self):
        return f"<Evaluation(id={self.id}, listing_id={self.listingId}, grade='{self.letterGrade}', score={self.overallScore})>"
