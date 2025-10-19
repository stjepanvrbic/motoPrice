"""
Data normalization utilities for motorcycle listings.

This module provides functions to normalize and parse various data fields
from scraped listings into standardized formats.
"""

import re
from typing import Any

from src.utils.logger import getLogger
from src.utils.validators import ParsedLocation, ParsedTitle

logger = getLogger(__name__)


# Common motorcycle makes for better parsing accuracy
KNOWN_MAKES = {
    "ducati",
    "yamaha",
    "honda",
    "suzuki",
    "kawasaki",
    "harley-davidson",
    "harley davidson",
    "bmw",
    "ktm",
    "triumph",
    "aprilia",
    "mv agusta",
    "indian",
    "victory",
    "buell",
    "can-am",
    "husqvarna",
    "beta",
    "gas gas",
    "sherco",
}


def normalizePrice(priceText: str | int | None) -> int | None:
    """
    Normalize price from various formats to integer cents.

    Handles formats like:
    - "$15,000"
    - "15000"
    - "$15k"
    - "15K"
    - "$15,000 OBO"
    - "Call for price" -> None

    Args:
        priceText: Price in various formats

    Returns:
        Price as integer (dollars) or None if parsing fails
    """
    if priceText is None:
        return None

    # Already an int
    if isinstance(priceText, int):
        return priceText if priceText >= 0 else None

    try:
        # Convert to string and lowercase
        text = str(priceText).lower().strip()

        # Handle special cases
        if any(x in text for x in ["call", "contact", "n/a", "na", "unknown"]):
            return None

        # Remove common words
        text = re.sub(r"\b(obo|or best offer|firm|usd|dollars?)\b", "", text, flags=re.IGNORECASE)

        # Remove currency symbols and commas
        text = re.sub(r"[$,]", "", text)

        # Handle "k" suffix (e.g., "15k" = 15000)
        if "k" in text:
            match = re.search(r"(\d+(?:\.\d+)?)\s*k", text)
            if match:
                return int(float(match.group(1)) * 1000)

        # Extract first number
        match = re.search(r"\d+", text)
        if match:
            price = int(match.group())
            # Sanity check - motorcycle prices typically between $500 and $500,000
            if 500 <= price <= 500000:
                return price
            # If price is too low, might be missing zeros (e.g., "15" instead of "15000")
            if price < 500:
                return None
            return price

        return None

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse price '{priceText}': {e}")
        return None


def normalizeMileage(mileageText: str | int | None) -> int | None:
    """
    Normalize mileage from various formats to integer miles.

    Handles formats like:
    - "5,000 mi"
    - "5000 miles"
    - "5k miles"
    - "5K"
    - "12,345"

    Args:
        mileageText: Mileage in various formats

    Returns:
        Mileage as integer (miles) or None if parsing fails
    """
    if mileageText is None:
        return None

    # Already an int
    if isinstance(mileageText, int):
        return mileageText if mileageText >= 0 else None

    try:
        # Convert to string
        text = str(mileageText).strip()

        # Remove commas
        text = re.sub(r",", "", text)

        # Handle "k" suffix first (before removing text)
        if "k" in text.lower():
            match = re.search(r"(\d+(?:\.\d+)?)\s*k", text, flags=re.IGNORECASE)
            if match:
                return int(float(match.group(1)) * 1000)

        # Remove "mi" or "miles" etc.
        text = re.sub(r"\s*(mi|miles|kilometers|km)\s*", "", text, flags=re.IGNORECASE)

        # Extract first number
        match = re.search(r"\d+", text)
        if match:
            mileage = int(match.group())
            # Sanity check - reasonable mileage range
            if 0 <= mileage <= 999999:
                return mileage
            return None

        return None

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse mileage '{mileageText}': {e}")
        return None


def parseTitle(title: str) -> ParsedTitle:
    """
    Parse motorcycle year, make, and model from title.

    This uses pattern matching and known makes to extract structured data
    from unstructured title strings.

    Examples:
    - "2022 Ducati Panigale V4" -> {year: 2022, make: "Ducati", model: "Panigale V4"}
    - "Ducati Panigale V4 2021" -> {year: 2021, make: "Ducati", model: "Panigale V4"}
    - "2020 Yamaha YZF-R1" -> {year: 2020, make: "Yamaha", model: "YZF-R1"}

    Args:
        title: Listing title

    Returns:
        ParsedTitle with extracted components
    """
    if not title:
        return ParsedTitle(rawTitle="")

    result = ParsedTitle(rawTitle=title)

    # Extract year (4-digit number between 1900-2099)
    yearMatch = re.search(r"\b(19\d{2}|20\d{2})\b", title)
    if yearMatch:
        result.year = int(yearMatch.group(1))

    # Try to find make by checking against known makes
    titleLower = title.lower()
    foundMake = None
    for make in KNOWN_MAKES:
        # Use word boundaries for better matching
        pattern = r"\b" + re.escape(make) + r"\b"
        if re.search(pattern, titleLower):
            foundMake = make
            break

    if foundMake:
        # Capitalize make properly
        if foundMake in ["bmw", "ktm"]:
            result.make = foundMake.upper()
        elif "harley" in foundMake:
            result.make = "Harley-Davidson"
        elif "mv" in foundMake:
            result.make = "MV Agusta"
        elif "can-am" in foundMake:
            result.make = "Can-Am"
        else:
            result.make = foundMake.title()

        # Try to extract model (text after make)
        # Find position of make in title
        makePattern = re.compile(re.escape(foundMake), re.IGNORECASE)
        makeMatch = makePattern.search(title)

        if makeMatch:
            # Get text after make
            afterMake = title[makeMatch.end() :].strip()

            # Remove year if it appears after make
            afterMake = re.sub(r"\b(19\d{2}|20\d{2})\b", "", afterMake).strip()

            # Remove common words/symbols at the start
            afterMake = re.sub(r"^[-:\s]+", "", afterMake)

            # Model is typically the next few words (up to 5 words or until special chars)
            modelMatch = re.match(r"^([A-Za-z0-9\s\-\.]{1,50})", afterMake)
            if modelMatch:
                model = modelMatch.group(1).strip()
                # Clean up model
                model = re.sub(r"\s+", " ", model)  # Collapse spaces
                if model:
                    result.model = model

    return result


def parseLocation(locationText: str) -> ParsedLocation:
    """
    Parse city, state, and ZIP code from location string.

    Handles formats like:
    - "Los Angeles, CA"
    - "Los Angeles, CA 90001"
    - "90001"
    - "CA"
    - "Los Angeles, California"

    Args:
        locationText: Location string

    Returns:
        ParsedLocation with extracted components
    """
    if not locationText:
        return ParsedLocation(rawLocation="")

    result = ParsedLocation(rawLocation=locationText)
    text = locationText.strip()

    # Extract ZIP code (5 digits or 5+4 format)
    zipMatch = re.search(r"\b(\d{5}(?:-\d{4})?)\b", text)
    if zipMatch:
        result.zipCode = zipMatch.group(1)
        # Remove ZIP from text for further parsing
        text = text.replace(zipMatch.group(0), "").strip()

    # Extract state (2-letter code)
    stateMatch = re.search(r"\b([A-Z]{2})\b", text)
    if stateMatch:
        result.state = stateMatch.group(1)
        # Remove state from text
        text = text.replace(stateMatch.group(0), "").strip()

    # What's left is likely the city (remove commas, extra whitespace)
    text = re.sub(r"[,\s]+", " ", text).strip()
    if text:
        result.city = text

    return result


def cleanText(text: str | None, maxLength: int | None = None) -> str | None:
    """
    Clean text by removing extra whitespace, normalizing Unicode, etc.

    Args:
        text: Text to clean
        maxLength: Maximum length (truncate if longer)

    Returns:
        Cleaned text or None
    """
    if text is None:
        return None

    # Strip and collapse whitespace
    cleaned = " ".join(str(text).strip().split())

    # Truncate if needed
    if maxLength and len(cleaned) > maxLength:
        cleaned = cleaned[:maxLength].strip()

    return cleaned if cleaned else None


def normalizeListing(rawData: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a raw listing dictionary.

    This is a convenience function that applies all normalization
    functions to a raw listing dict from a scraper.

    Args:
        rawData: Raw listing data from scraper

    Returns:
        Normalized listing data ready for validation
    """
    normalized: dict[str, Any] = {}

    # Direct copies
    for field in ["url", "source", "description", "sellerName", "sellerType"]:
        if field in rawData:
            normalized[field] = rawData[field]

    # Normalize price
    if "price" in rawData:
        normalized["price"] = normalizePrice(rawData["price"])

    # Normalize mileage
    if "mileage" in rawData:
        normalized["mileage"] = normalizeMileage(rawData["mileage"])

    # Parse title
    if "title" in rawData and rawData["title"]:
        normalized["title"] = cleanText(rawData["title"], maxLength=500)
        parsed = parseTitle(rawData["title"])

        # Use parsed values if not explicitly provided
        if "year" not in rawData and parsed.year:
            normalized["year"] = parsed.year
        if "make" not in rawData and parsed.make:
            normalized["make"] = parsed.make
        if "model" not in rawData and parsed.model:
            normalized["model"] = parsed.model

    # Use explicit year/make/model if provided
    if "year" in rawData:
        normalized["year"] = rawData["year"]
    if "make" in rawData:
        normalized["make"] = rawData["make"]
    if "model" in rawData:
        normalized["model"] = rawData["model"]

    # Parse location
    if "location" in rawData and rawData["location"]:
        parsed = parseLocation(rawData["location"])
        if parsed.city:
            normalized["city"] = parsed.city
        if parsed.state:
            normalized["state"] = parsed.state
        if parsed.zipCode:
            normalized["zipCode"] = parsed.zipCode

    # Direct field mapping with cleaning
    if "condition" in rawData:
        normalized["condition"] = cleanText(rawData["condition"])
    if "titleStatus" in rawData:
        normalized["titleStatus"] = cleanText(rawData["titleStatus"])

    # Image URLs
    if "images" in rawData:
        normalized["imageUrls"] = rawData["images"]
    elif "imageUrl" in rawData and rawData["imageUrl"]:
        normalized["imageUrls"] = [rawData["imageUrl"]]
    else:
        normalized["imageUrls"] = []

    return normalized
