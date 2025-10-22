"""
Tests for image handling utilities.
"""

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from PIL import Image

from src.database import operations as ops
from src.utils.exceptions import ValidationError
from src.utils.images import (
    downloadAndSaveImage,
    downloadImage,
    extractImageMetadata,
    saveImage,
    validateImageUrl,
)

# ============================================================================
# URL Validation Tests
# ============================================================================


def testValidateImageUrlValid():
    """Validate properly formatted image URLs."""
    validUrls = [
        "https://example.com/image.jpg",
        "http://example.com/photo.png",
        "https://cdn.example.com/images/bike.jpeg",
        "https://example.com/path/to/image.gif",
        "https://example.com/image.webp",
    ]

    for url in validUrls:
        assert validateImageUrl(url) is True


def testValidateImageUrlInvalidProtocol():
    """Reject URLs with invalid protocols."""
    with pytest.raises(ValidationError, match="must use http or https"):
        validateImageUrl("ftp://example.com/image.jpg")


def testValidateImageUrlNoDomain():
    """Reject URLs without domain."""
    with pytest.raises(ValidationError, match="must have a valid domain"):
        validateImageUrl("https:///image.jpg")


def testValidateImageUrlEmpty():
    """Reject empty URLs."""
    with pytest.raises(ValidationError, match="must be a non-empty string"):
        validateImageUrl("")


def testValidateImageUrlNone():
    """Reject None as URL."""
    with pytest.raises(ValidationError, match="must be a non-empty string"):
        validateImageUrl(None)


def testValidateImageUrlNoExtension():
    """Warn about URLs without standard image extensions but still pass."""
    url = "https://example.com/image"
    assert validateImageUrl(url) is True


# ============================================================================
# Image Download Tests
# ============================================================================


@patch("src.utils.images.requests.get")
def testDownloadImageSuccess(mockGet):
    """Download image successfully."""
    mockResponse = Mock()
    mockResponse.content = b"fake image data"
    mockResponse.headers = {"Content-Type": "image/jpeg"}
    mockResponse.raise_for_status = Mock()
    mockGet.return_value = mockResponse

    url = "https://example.com/test.jpg"
    data = downloadImage(url)

    assert data == b"fake image data"
    mockGet.assert_called_once()
    args, kwargs = mockGet.call_args
    assert args[0] == url
    assert kwargs["timeout"] == 10


@patch("src.utils.images.requests.get")
def testDownloadImageInvalidContentType(mockGet):
    """Reject downloads with non-image content type."""
    mockResponse = Mock()
    mockResponse.content = b"<html>not an image</html>"
    mockResponse.headers = {"Content-Type": "text/html"}
    mockResponse.raise_for_status = Mock()
    mockGet.return_value = mockResponse

    url = "https://example.com/notimage.jpg"

    with pytest.raises(ValidationError, match="does not point to an image"):
        downloadImage(url)


@patch("src.utils.images.requests.get")
def testDownloadImageRequestException(mockGet):
    """Handle network errors during download."""
    mockGet.side_effect = requests.RequestException("Network error")

    url = "https://example.com/test.jpg"

    with pytest.raises(requests.RequestException, match="Network error"):
        downloadImage(url)


@patch("src.utils.images.requests.get")
def testDownloadImageCustomTimeout(mockGet):
    """Use custom timeout for download."""
    mockResponse = Mock()
    mockResponse.content = b"fake image data"
    mockResponse.headers = {"Content-Type": "image/png"}
    mockResponse.raise_for_status = Mock()
    mockGet.return_value = mockResponse

    url = "https://example.com/test.png"
    downloadImage(url, timeout=30)

    args, kwargs = mockGet.call_args
    assert kwargs["timeout"] == 30


# ============================================================================
# Metadata Extraction Tests
# ============================================================================


def testExtractImageMetadataFromBytes():
    """Extract metadata from image bytes."""
    img = Image.new("RGB", (800, 600), color="red")
    imgBytes = BytesIO()
    img.save(imgBytes, format="PNG")
    imgBytes.seek(0)

    metadata = extractImageMetadata(imgBytes.getvalue())

    assert metadata["width"] == 800
    assert metadata["height"] == 600
    assert metadata["format"] == "PNG"
    assert metadata["mode"] == "RGB"
    assert metadata["size_bytes"] > 0


def testExtractImageMetadataFromBytesIO():
    """Extract metadata from BytesIO object."""
    img = Image.new("RGBA", (1024, 768), color="blue")
    imgBytes = BytesIO()
    img.save(imgBytes, format="PNG")
    imgBytes.seek(0)

    metadata = extractImageMetadata(imgBytes)

    assert metadata["width"] == 1024
    assert metadata["height"] == 768
    assert metadata["format"] == "PNG"
    assert metadata["mode"] == "RGBA"


def testExtractImageMetadataInvalidData():
    """Reject invalid image data."""
    invalidData = b"not an image"

    with pytest.raises(ValidationError, match="Invalid image data"):
        extractImageMetadata(invalidData)


def testExtractImageMetadataJPEG():
    """Extract metadata from JPEG image."""
    img = Image.new("RGB", (640, 480), color="green")
    imgBytes = BytesIO()
    img.save(imgBytes, format="JPEG")
    imgBytes.seek(0)

    metadata = extractImageMetadata(imgBytes.getvalue())

    assert metadata["width"] == 640
    assert metadata["height"] == 480
    assert metadata["format"] == "JPEG"
    assert metadata["mode"] == "RGB"


# ============================================================================
# Image Save Tests
# ============================================================================


def testSaveImage():
    """Save image to file."""
    img = Image.new("RGB", (100, 100), color="yellow")
    imgBytes = BytesIO()
    img.save(imgBytes, format="PNG")
    imgBytes.seek(0)
    imageData = imgBytes.getvalue()

    with tempfile.TemporaryDirectory() as tmpDir:
        savePath = Path(tmpDir) / "test.png"
        result = saveImage(imageData, savePath)

        assert result == savePath
        assert savePath.exists()
        assert savePath.read_bytes() == imageData


def testSaveImageCreatesDirectories():
    """Save image creates parent directories."""
    img = Image.new("RGB", (100, 100), color="purple")
    imgBytes = BytesIO()
    img.save(imgBytes, format="PNG")
    imgBytes.seek(0)
    imageData = imgBytes.getvalue()

    with tempfile.TemporaryDirectory() as tmpDir:
        savePath = Path(tmpDir) / "subdir" / "nested" / "test.png"
        result = saveImage(imageData, savePath)

        assert result == savePath
        assert savePath.exists()
        assert savePath.parent.exists()


def testSaveImageAsString():
    """Save image with string path."""
    img = Image.new("RGB", (50, 50), color="orange")
    imgBytes = BytesIO()
    img.save(imgBytes, format="PNG")
    imgBytes.seek(0)
    imageData = imgBytes.getvalue()

    with tempfile.TemporaryDirectory() as tmpDir:
        savePathStr = str(Path(tmpDir) / "test.png")
        result = saveImage(imageData, savePathStr)

        assert isinstance(result, Path)
        assert result.exists()


# ============================================================================
# Download and Save Combined Tests
# ============================================================================


@patch("src.utils.images.requests.get")
def testDownloadAndSaveImage(mockGet):
    """Download and save image with metadata."""
    img = Image.new("RGB", (200, 150), color="cyan")
    imgBytes = BytesIO()
    img.save(imgBytes, format="JPEG")
    imgBytes.seek(0)
    imageData = imgBytes.getvalue()

    mockResponse = Mock()
    mockResponse.content = imageData
    mockResponse.headers = {"Content-Type": "image/jpeg"}
    mockResponse.raise_for_status = Mock()
    mockGet.return_value = mockResponse

    with tempfile.TemporaryDirectory() as tmpDir:
        savePath = Path(tmpDir) / "downloaded.jpg"
        url = "https://example.com/bike.jpg"

        resultPath, metadata = downloadAndSaveImage(url, savePath)

        assert resultPath == savePath
        assert savePath.exists()
        assert metadata["width"] == 200
        assert metadata["height"] == 150
        assert metadata["format"] == "JPEG"


# ============================================================================
# Database Integration Tests
# ============================================================================


def testImageDatabaseStorage(testSession, sampleListing):
    """Store image URLs in database."""
    imageUrls = [
        "https://example.com/bike1.jpg",
        "https://example.com/bike2.png",
        "https://example.com/bike3.jpg",
    ]

    for i, url in enumerate(imageUrls):
        ops.createImage(testSession, listingId=sampleListing.id, url=url, position=i)

    testSession.commit()

    images = ops.getImagesByListing(testSession, sampleListing.id)

    assert len(images) == 3
    assert [img.url for img in images] == imageUrls
    assert [img.position for img in images] == [0, 1, 2]


def testImageMetadataInDatabase(testSession, sampleListing):
    """Store image metadata in database via aiAnalysis field."""
    metadata = {"width": 1920, "height": 1080, "format": "JPEG", "size_bytes": 245678}

    image = ops.createImage(
        testSession,
        listingId=sampleListing.id,
        url="https://example.com/bike.jpg",
        position=0,
        aiAnalysis=metadata,
    )
    testSession.commit()

    retrieved = testSession.get(ops.Image, image.id)

    assert retrieved.aiAnalysis["width"] == 1920
    assert retrieved.aiAnalysis["height"] == 1080
    assert retrieved.aiAnalysis["format"] == "JPEG"


def testInvalidImageUrl(testSession, sampleListing):
    """Validate URL before storing in database."""
    invalidUrl = "not-a-url"

    with pytest.raises(ValidationError):
        validateImageUrl(invalidUrl)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def testSession(testEngine):
    """Create test database session."""
    from sqlalchemy.orm import sessionmaker

    SessionFactory = sessionmaker(bind=testEngine)
    session = SessionFactory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def testEngine():
    """Create in-memory SQLite engine for testing."""
    from sqlalchemy import create_engine

    from src.database.base import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


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
    )
    testSession.commit()
    return listing
