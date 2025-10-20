"""
Data validation and normalization using Pydantic models.

This module provides Pydantic models for validating and normalizing
motorcycle listing data from various sources.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from src.utils.logger import getLogger

logger = getLogger(__name__)


class NormalizedListing(BaseModel):
    """
    Normalized motorcycle listing data.

    This model validates and normalizes data from various scraping sources
    into a consistent format for database storage.
    """

    # Required fields
    url: str = Field(..., description="Listing URL (unique identifier)")
    source: str = Field(..., description="Source of listing (cycletrader, facebook, etc.)")

    # Motorcycle details
    year: int | None = Field(None, ge=1900, le=2100, description="Year of manufacture")
    make: str | None = Field(None, min_length=1, max_length=100, description="Manufacturer")
    model: str | None = Field(None, min_length=1, max_length=200, description="Model name")

    # Pricing
    price: int | None = Field(None, ge=0, description="Listing price in USD")

    # Condition
    mileage: int | None = Field(None, ge=0, description="Mileage in miles")
    condition: str | None = Field(None, description="Condition (new, used, etc.)")
    titleStatus: str | None = Field(None, description="Title status (clean, salvage, etc.)")

    # Location
    city: str | None = Field(None, max_length=100, description="City")
    state: str | None = Field(None, max_length=2, description="State (2-letter code)")
    zipCode: str | None = Field(None, max_length=10, description="ZIP code")

    # Listing details
    title: str | None = Field(None, max_length=500, description="Listing title")
    description: str | None = Field(None, description="Listing description")

    # Seller info
    sellerName: str | None = Field(None, max_length=200, description="Seller name")
    sellerType: str | None = Field(None, description="Seller type (dealer, private)")

    # Images
    imageUrls: list[str] = Field(default_factory=list, description="List of image URLs")

    # Metadata
    scrapedAt: datetime = Field(
        default_factory=datetime.now, description="When listing was scraped"
    )

    @field_validator("url")
    @classmethod
    def validateUrl(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.strip()

    @field_validator("source")
    @classmethod
    def validateSource(cls, v: str) -> str:
        """Validate source is one of the known sources."""
        validSources = {"cycletrader", "facebook", "ebay", "craigslist"}
        vLower = v.lower().strip()
        if vLower not in validSources:
            logger.warning(f"Unknown source: {v}")
        return vLower

    @field_validator("make", "model", "city", "sellerName")
    @classmethod
    def cleanText(cls, v: str | None) -> str | None:
        """Clean text fields (strip whitespace, remove extra spaces)."""
        if v is None:
            return None
        # Strip and collapse multiple spaces
        cleaned = " ".join(v.strip().split())
        return cleaned if cleaned else None

    @field_validator("state")
    @classmethod
    def validateState(cls, v: str | None) -> str | None:
        """Validate state is 2-letter code."""
        if v is None:
            return None
        v = v.strip().upper()
        if len(v) != 2:
            raise ValueError(f"State must be 2-letter code, got: {v}")
        return v

    @field_validator("zipCode")
    @classmethod
    def validateZipCode(cls, v: str | None) -> str | None:
        """Validate ZIP code format."""
        if v is None:
            return None
        v = v.strip()
        # US ZIP codes: 12345 or 12345-6789
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError(f"Invalid ZIP code format: {v}")
        return v

    @field_validator("condition")
    @classmethod
    def normalizeCondition(cls, v: str | None) -> str | None:
        """Normalize condition to standard values."""
        if v is None:
            return None
        vLower = v.lower().strip()
        # Map various condition strings to standard values
        conditionMap = {
            "new": "new",
            "brand new": "new",
            "used": "used",
            "pre-owned": "used",
            "preowned": "used",
            "excellent": "excellent",
            "like new": "excellent",
            "good": "good",
            "fair": "fair",
            "poor": "poor",
        }
        return conditionMap.get(vLower, vLower)

    @field_validator("titleStatus")
    @classmethod
    def normalizeTitleStatus(cls, v: str | None) -> str | None:
        """Normalize title status to standard values."""
        if v is None:
            return None
        vLower = v.lower().strip()
        # Map various title status strings
        statusMap = {
            "clean": "clean",
            "clear": "clean",
            "salvage": "salvage",
            "rebuilt": "rebuilt",
            "reconstructed": "rebuilt",
            "lemon": "lemon",
            "flood": "flood",
        }
        return statusMap.get(vLower, vLower)

    @field_validator("sellerType")
    @classmethod
    def normalizeSellerType(cls, v: str | None) -> str | None:
        """Normalize seller type to standard values."""
        if v is None:
            return None
        vLower = v.lower().strip()
        if "dealer" in vLower:
            return "dealer"
        if "private" in vLower or "owner" in vLower:
            return "private"
        return vLower

    @model_validator(mode="after")
    def validateYearMakeModel(self) -> "NormalizedListing":
        """Validate that at least some identifying info is present."""
        # We should have at least a title or (make and model)
        if not self.title and not (self.make and self.model):
            raise ValueError("Listing must have either title or (make and model)")
        return self

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True
        validate_assignment = True


class ParsedTitle(BaseModel):
    """
    Parsed components from a listing title.

    Used as intermediate representation when parsing titles.
    """

    year: int | None = None
    make: str | None = None
    model: str | None = None
    rawTitle: str = Field(..., description="Original title")

    @field_validator("year")
    @classmethod
    def validateYear(cls, v: int | None) -> int | None:
        """Validate year is reasonable."""
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError(f"Year {v} is out of valid range (1900-2100)")
        return v


class ParsedLocation(BaseModel):
    """
    Parsed location components.

    Used as intermediate representation when parsing location strings.
    """

    city: str | None = None
    state: str | None = None
    zipCode: str | None = None
    rawLocation: str = Field(..., description="Original location string")

    @field_validator("state")
    @classmethod
    def validateState(cls, v: str | None) -> str | None:
        """Validate state is 2-letter code."""
        if v is None:
            return None
        v = v.strip().upper()
        if len(v) != 2:
            logger.warning(f"State must be 2-letter code, got: {v}")
            return None
        return v
