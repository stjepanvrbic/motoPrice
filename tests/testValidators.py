"""
Unit tests for Pydantic validators.
"""

import pytest
from pydantic import ValidationError

from src.utils.validators import NormalizedListing, ParsedLocation, ParsedTitle


class TestNormalizedListing:
    """Test NormalizedListing Pydantic model."""

    def testValidListing(self):
        """Test creating valid listing."""
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            year=2022,
            make="Ducati",
            model="Panigale V4",
            price=18500,
            mileage=1200,
            city="Los Angeles",
            state="CA",
            zipCode="90001",
            title="2022 Ducati Panigale V4",
        )

        assert listing.url == "https://example.com/listing/123"
        assert listing.source == "cycletrader"
        assert listing.year == 2022
        assert listing.make == "Ducati"
        assert listing.model == "Panigale V4"
        assert listing.price == 18500
        assert listing.mileage == 1200
        assert listing.city == "Los Angeles"
        assert listing.state == "CA"
        assert listing.zipCode == "90001"

    def testMinimalListing(self):
        """Test creating minimal valid listing."""
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="facebook",
            title="Motorcycle for sale",
        )

        assert listing.url == "https://example.com/listing/123"
        assert listing.source == "facebook"
        assert listing.title == "Motorcycle for sale"
        assert listing.year is None
        assert listing.make is None

    def testInvalidUrl(self):
        """Test that invalid URL raises error."""
        with pytest.raises(ValidationError, match="URL must start"):
            NormalizedListing(
                url="not-a-valid-url",
                source="cycletrader",
                title="Test",
            )

    def testMissingRequiredFields(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                # Missing source
            )

    def testYearValidation(self):
        """Test year validation."""
        # Valid year
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            year=2022,
        )
        assert listing.year == 2022

        # Year too old
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                year=1899,
            )

        # Year too new
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                year=2101,
            )

    def testPriceValidation(self):
        """Test price validation."""
        # Valid price
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            price=15000,
        )
        assert listing.price == 15000

        # Negative price should fail
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                price=-100,
            )

    def testMileageValidation(self):
        """Test mileage validation."""
        # Valid mileage
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            mileage=5000,
        )
        assert listing.mileage == 5000

        # Negative mileage should fail
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                mileage=-100,
            )

    def testStateValidation(self):
        """Test state validation."""
        # Valid state
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            state="CA",
        )
        assert listing.state == "CA"

        # Lowercase state should be uppercased
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            state="ca",
        )
        assert listing.state == "CA"

        # Invalid state (too long)
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                state="CAL",
            )

    def testZipCodeValidation(self):
        """Test ZIP code validation."""
        # Valid ZIP (5 digits)
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            zipCode="90001",
        )
        assert listing.zipCode == "90001"

        # Valid ZIP (5+4 format)
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            zipCode="90001-1234",
        )
        assert listing.zipCode == "90001-1234"

        # Invalid ZIP
        with pytest.raises(ValidationError):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                zipCode="123",  # Too short
            )

    def testConditionNormalization(self):
        """Test condition normalization."""
        testCases = [
            ("New", "new"),
            ("BRAND NEW", "new"),
            ("Used", "used"),
            ("Pre-Owned", "used"),
            ("Excellent", "excellent"),
            ("Like New", "excellent"),
        ]

        for input_val, expected in testCases:
            listing = NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                condition=input_val,
            )
            assert listing.condition == expected

    def testTitleStatusNormalization(self):
        """Test title status normalization."""
        testCases = [
            ("Clean", "clean"),
            ("CLEAR", "clean"),
            ("Salvage", "salvage"),
            ("Rebuilt", "rebuilt"),
            ("Reconstructed", "rebuilt"),
        ]

        for input_val, expected in testCases:
            listing = NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                titleStatus=input_val,
            )
            assert listing.titleStatus == expected

    def testSellerTypeNormalization(self):
        """Test seller type normalization."""
        testCases = [
            ("Dealer", "dealer"),
            ("Private Party", "private"),
            ("Owner", "private"),
        ]

        for input_val, expected in testCases:
            listing = NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                title="Test",
                sellerType=input_val,
            )
            assert listing.sellerType == expected

    def testTextCleaning(self):
        """Test that text fields are cleaned."""
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="Test",
            make="  Ducati  ",  # Extra spaces
            model="Panigale   V4",  # Multiple spaces
            city="  Los  Angeles  ",
        )

        assert listing.make == "Ducati"
        assert listing.model == "Panigale V4"
        assert listing.city == "Los Angeles"

    def testYearMakeModelValidation(self):
        """Test that listing must have title or (make and model)."""
        # Valid: has title
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            title="2022 Ducati Panigale V4",
        )
        assert listing.title is not None

        # Valid: has make and model
        listing = NormalizedListing(
            url="https://example.com/listing/123",
            source="cycletrader",
            make="Ducati",
            model="Panigale V4",
        )
        assert listing.make == "Ducati"
        assert listing.model == "Panigale V4"

        # Invalid: has neither title nor (make and model)
        with pytest.raises(ValidationError, match="title or \\(make and model\\)"):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
            )

        # Invalid: has make but not model
        with pytest.raises(ValidationError, match="title or \\(make and model\\)"):
            NormalizedListing(
                url="https://example.com/listing/123",
                source="cycletrader",
                make="Ducati",
            )


class TestParsedTitle:
    """Test ParsedTitle model."""

    def testValidParsedTitle(self):
        """Test creating valid ParsedTitle."""
        parsed = ParsedTitle(
            year=2022,
            make="Ducati",
            model="Panigale V4",
            rawTitle="2022 Ducati Panigale V4",
        )

        assert parsed.year == 2022
        assert parsed.make == "Ducati"
        assert parsed.model == "Panigale V4"

    def testInvalidYear(self):
        """Test that invalid year raises error."""
        with pytest.raises(ValidationError, match="out of valid range"):
            ParsedTitle(
                year=1850,  # Too old
                rawTitle="1850 Motorcycle",
            )


class TestParsedLocation:
    """Test ParsedLocation model."""

    def testValidParsedLocation(self):
        """Test creating valid ParsedLocation."""
        parsed = ParsedLocation(
            city="Los Angeles",
            state="CA",
            zipCode="90001",
            rawLocation="Los Angeles, CA 90001",
        )

        assert parsed.city == "Los Angeles"
        assert parsed.state == "CA"
        assert parsed.zipCode == "90001"

    def testStateNormalization(self):
        """Test state is uppercased."""
        parsed = ParsedLocation(
            state="ca",
            rawLocation="CA",
        )

        assert parsed.state == "CA"

    def testInvalidState(self):
        """Test that invalid state is set to None with warning."""
        # Should not raise error, just log warning and return None
        parsed = ParsedLocation(
            state="CAL",  # Too long
            rawLocation="CAL",
        )

        assert parsed.state is None
