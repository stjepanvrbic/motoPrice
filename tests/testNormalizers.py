"""
Unit tests for data normalization utilities.
"""

from src.utils.normalizers import (
    cleanText,
    normalizeListing,
    normalizeMileage,
    normalizePrice,
    parseLocation,
    parseTitle,
)


class TestNormalizePrice:
    """Test price normalization."""

    def testValidPrices(self):
        """Test parsing valid price formats."""
        testCases = [
            ("$15,000", 15000),
            ("15000", 15000),
            ("$15k", 15000),
            ("15K", 15000),
            ("$20,500", 20500),
            ("$15,000 OBO", 15000),
            ("$15,000 or best offer", 15000),
            ("15000 USD", 15000),
            (15000, 15000),  # Already int
            ("$1,500", 1500),
            ("$125,000", 125000),
        ]

        for priceText, expected in testCases:
            result = normalizePrice(priceText)
            assert result == expected, f"Failed for {priceText}: got {result}, expected {expected}"

    def testInvalidPrices(self):
        """Test handling invalid prices."""
        testCases = [
            None,
            "",
            "Call for price",
            "Contact seller",
            "N/A",
            "Unknown",
            "abc",
            "$100",  # Too low
            (-1000),  # Negative
        ]

        for priceText in testCases:
            result = normalizePrice(priceText)
            assert result is None, f"Expected None for {priceText}, got {result}"

    def testEdgeCases(self):
        """Test edge cases."""
        # Minimum valid price
        assert normalizePrice("$500") == 500
        assert normalizePrice("$499") is None  # Too low

        # Maximum reasonable price
        assert normalizePrice("$500,000") == 500000

        # With extra text
        assert normalizePrice("Price: $15,000 FIRM") == 15000


class TestNormalizeMileage:
    """Test mileage normalization."""

    def testValidMileage(self):
        """Test parsing valid mileage formats."""
        testCases = [
            ("5,000 mi", 5000),
            ("5000 miles", 5000),
            ("5k miles", 5000),
            ("5K", 5000),
            ("12,345", 12345),
            ("0 miles", 0),
            ("123", 123),
            (5000, 5000),  # Already int
            ("2.5k mi", 2500),
        ]

        for mileageText, expected in testCases:
            result = normalizeMileage(mileageText)
            assert (
                result == expected
            ), f"Failed for {mileageText}: got {result}, expected {expected}"

    def testInvalidMileage(self):
        """Test handling invalid mileage."""
        testCases = [
            None,
            "",
            "N/A",
            "Unknown",
            "abc",
            (-100),  # Negative
        ]

        for mileageText in testCases:
            result = normalizeMileage(mileageText)
            assert result is None, f"Expected None for {mileageText}, got {result}"


class TestParseTitle:
    """Test title parsing."""

    def testFullTitles(self):
        """Test parsing complete titles with year, make, model."""
        testCases = [
            ("2022 Ducati Panigale V4", 2022, "Ducati", "Panigale V4"),
            ("2021 Yamaha YZF-R1", 2021, "Yamaha", "YZF-R1"),
            ("2020 Honda CBR1000RR", 2020, "Honda", "CBR1000RR"),
            ("2019 Kawasaki Ninja ZX-10R", 2019, "Kawasaki", "Ninja ZX-10R"),
            ("2023 BMW S1000RR", 2023, "BMW", "S1000RR"),
            ("2022 Harley-Davidson Street Glide", 2022, "Harley-Davidson", "Street Glide"),
        ]

        for title, expectedYear, expectedMake, expectedModel in testCases:
            result = parseTitle(title)
            assert (
                result.year == expectedYear
            ), f"Year mismatch for '{title}': got {result.year}, expected {expectedYear}"
            assert (
                result.make == expectedMake
            ), f"Make mismatch for '{title}': got {result.make}, expected {expectedMake}"
            assert expectedModel in result.model, (
                f"Model mismatch for '{title}': got {result.model}, expected to contain "
                f"{expectedModel}"
            )

    def testYearAtEnd(self):
        """Test parsing titles with year at the end."""
        result = parseTitle("Ducati Panigale V4 2021")
        assert result.year == 2021
        assert result.make == "Ducati"
        assert "Panigale V4" in result.model

    def testNoYear(self):
        """Test parsing titles without year."""
        result = parseTitle("Ducati Panigale V4")
        assert result.year is None
        assert result.make == "Ducati"
        assert result.model is not None

    def testUnknownMake(self):
        """Test parsing titles with unknown make."""
        result = parseTitle("2022 RandomBrand Model X")
        assert result.year == 2022
        assert result.make is None  # Unknown make

    def testEmptyTitle(self):
        """Test parsing empty title."""
        result = parseTitle("")
        assert result.year is None
        assert result.make is None
        assert result.model is None


class TestParseLocation:
    """Test location parsing."""

    def testCityState(self):
        """Test parsing city and state."""
        testCases = [
            ("Los Angeles, CA", "Los Angeles", "CA", None),
            ("New York, NY", "New York", "NY", None),
            ("Miami, FL", "Miami", "FL", None),
        ]

        for location, expectedCity, expectedState, expectedZip in testCases:
            result = parseLocation(location)
            assert result.city == expectedCity, f"City mismatch for '{location}'"
            assert result.state == expectedState, f"State mismatch for '{location}'"
            assert result.zipCode == expectedZip, f"ZIP mismatch for '{location}'"

    def testCityStateZip(self):
        """Test parsing city, state, and ZIP."""
        testCases = [
            ("Los Angeles, CA 90001", "Los Angeles", "CA", "90001"),
            ("New York, NY 10001", "New York", "NY", "10001"),
            ("Miami, FL 33101-1234", "Miami", "FL", "33101-1234"),
        ]

        for location, expectedCity, expectedState, expectedZip in testCases:
            result = parseLocation(location)
            assert result.city == expectedCity, f"City mismatch for '{location}'"
            assert result.state == expectedState, f"State mismatch for '{location}'"
            assert result.zipCode == expectedZip, f"ZIP mismatch for '{location}'"

    def testZipOnly(self):
        """Test parsing ZIP code only."""
        result = parseLocation("90001")
        assert result.zipCode == "90001"
        assert result.state is None
        assert result.city is None

    def testStateOnly(self):
        """Test parsing state only."""
        result = parseLocation("CA")
        assert result.state == "CA"
        assert result.city is None
        assert result.zipCode is None

    def testEmptyLocation(self):
        """Test parsing empty location."""
        result = parseLocation("")
        assert result.city is None
        assert result.state is None
        assert result.zipCode is None


class TestCleanText:
    """Test text cleaning."""

    def testBasicCleaning(self):
        """Test basic text cleaning."""
        assert cleanText("  Hello  World  ") == "Hello World"
        assert cleanText("Multiple   spaces") == "Multiple spaces"
        assert cleanText("\n\tTabs and newlines\n") == "Tabs and newlines"

    def testMaxLength(self):
        """Test truncation with maxLength."""
        longText = "This is a very long text that should be truncated"
        result = cleanText(longText, maxLength=20)
        assert len(result) <= 20
        assert result == "This is a very long"

    def testNone(self):
        """Test None input."""
        assert cleanText(None) is None

    def testEmpty(self):
        """Test empty string."""
        assert cleanText("") is None
        assert cleanText("   ") is None


class TestNormalizeListing:
    """Test complete listing normalization."""

    def testFullListing(self):
        """Test normalizing a complete listing."""
        rawData = {
            "url": "https://example.com/listing/123",
            "source": "cycletrader",
            "title": "2022 Ducati Panigale V4",
            "price": "$18,500",
            "mileage": "1,200 mi",
            "location": "Los Angeles, CA 90001",
            "description": "Beautiful bike in excellent condition",
            "condition": "Used",
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        }

        normalized = normalizeListing(rawData)

        assert normalized["url"] == "https://example.com/listing/123"
        assert normalized["source"] == "cycletrader"
        assert normalized["price"] == 18500
        assert normalized["mileage"] == 1200
        assert normalized["year"] == 2022
        assert normalized["make"] == "Ducati"
        assert "Panigale V4" in normalized["model"]
        assert normalized["city"] == "Los Angeles"
        assert normalized["state"] == "CA"
        assert normalized["zipCode"] == "90001"
        assert len(normalized["imageUrls"]) == 2

    def testMinimalListing(self):
        """Test normalizing minimal listing."""
        rawData = {
            "url": "https://example.com/listing/456",
            "source": "facebook",
            "title": "Motorcycle for sale",
        }

        normalized = normalizeListing(rawData)

        assert normalized["url"] == "https://example.com/listing/456"
        assert normalized["source"] == "facebook"
        assert normalized["title"] == "Motorcycle for sale"
        assert normalized.get("year") is None
        assert normalized.get("make") is None
        assert normalized["imageUrls"] == []

    def testSingleImageUrl(self):
        """Test normalizing listing with single image URL."""
        rawData = {
            "url": "https://example.com/listing/789",
            "source": "facebook",
            "title": "2021 Yamaha R1",
            "imageUrl": "https://example.com/image.jpg",
        }

        normalized = normalizeListing(rawData)

        assert normalized["imageUrls"] == ["https://example.com/image.jpg"]

    def testExplicitYearMakeModel(self):
        """Test that explicit year/make/model override parsed values."""
        rawData = {
            "url": "https://example.com/listing/999",
            "source": "cycletrader",
            "title": "2020 Honda CBR1000RR",  # Title says 2020 Honda
            "year": 2021,  # But explicit values say 2021 Yamaha
            "make": "Yamaha",
            "model": "YZF-R1",
        }

        normalized = normalizeListing(rawData)

        # Explicit values should win
        assert normalized["year"] == 2021
        assert normalized["make"] == "Yamaha"
        assert normalized["model"] == "YZF-R1"
