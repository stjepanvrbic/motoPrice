"""
Image handling utilities for URL validation, downloading, and metadata extraction.
"""

from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse

import requests
from PIL import Image

from .exceptions import ValidationError
from .logger import getLogger

logger = getLogger(__name__)


def validateImageUrl(url: str) -> bool:
    """
    Validate that a URL is a properly formatted image URL.

    Args:
        url: URL to validate

    Returns:
        True if valid image URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("Image URL must be a non-empty string")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"Image URL must use http or https protocol: {url}")

    if not parsed.netloc:
        raise ValidationError(f"Image URL must have a valid domain: {url}")

    validExtensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    path = parsed.path.lower()

    hasValidExtension = any(path.endswith(ext) for ext in validExtensions)

    if not hasValidExtension:
        logger.warning(f"Image URL does not have standard image extension: {url}")

    return True


def downloadImage(url: str, timeout: int = 10) -> bytes:
    """
    Download image from URL.

    Args:
        url: Image URL to download
        timeout: Request timeout in seconds

    Returns:
        Image data as bytes

    Raises:
        ValidationError: If URL is invalid
        requests.RequestException: If download fails
    """
    validateImageUrl(url)

    logger.info(f"Downloading image from {url}")

    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MotoPriceBot/1.0)"},
        )
        response.raise_for_status()

        contentType = response.headers.get("Content-Type", "")
        if not contentType.startswith("image/"):
            raise ValidationError(f"URL does not point to an image (Content-Type: {contentType})")

        return response.content

    except requests.RequestException as e:
        logger.error(f"Failed to download image from {url}: {e}")
        raise


def extractImageMetadata(imageData: bytes | BinaryIO) -> dict:
    """
    Extract metadata from image data.

    Args:
        imageData: Image data as bytes or file-like object

    Returns:
        Dictionary with metadata:
            - width: Image width in pixels
            - height: Image height in pixels
            - format: Image format (JPEG, PNG, etc.)
            - mode: Color mode (RGB, RGBA, etc.)
            - size_bytes: Size in bytes
    """
    # Calculate size before converting to BytesIO
    if isinstance(imageData, bytes):
        sizeBytes = len(imageData)
        imageData = BytesIO(imageData)
    else:
        # For file-like objects, seek to end to get size
        currentPos = imageData.tell()
        imageData.seek(0, 2)  # Seek to end
        sizeBytes = imageData.tell()
        imageData.seek(currentPos)  # Restore original position

    try:
        with Image.open(imageData) as img:
            metadata = {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_bytes": sizeBytes,
            }

            logger.debug(f"Extracted image metadata: {metadata}")
            return metadata

    except Exception as e:
        logger.error(f"Failed to extract image metadata: {e}")
        raise ValidationError(f"Invalid image data: {e}") from e


def saveImage(imageData: bytes, savePath: str | Path) -> Path:
    """
    Save image data to file.

    Args:
        imageData: Image data as bytes
        savePath: Path to save image

    Returns:
        Path object of saved file

    Raises:
        IOError: If file save fails
    """
    savePath = Path(savePath)

    savePath.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(savePath, "wb") as f:
            f.write(imageData)

        logger.info(f"Saved image to {savePath}")
        return savePath

    except OSError as e:
        logger.error(f"Failed to save image to {savePath}: {e}")
        raise


def downloadAndSaveImage(url: str, savePath: str | Path, timeout: int = 10) -> tuple[Path, dict]:
    """
    Download image and save to file with metadata extraction.

    Args:
        url: Image URL to download
        savePath: Path to save image
        timeout: Request timeout in seconds

    Returns:
        Tuple of (saved_path, metadata)

    Raises:
        ValidationError: If URL or image is invalid
        requests.RequestException: If download fails
        IOError: If file save fails
    """
    imageData = downloadImage(url, timeout)

    metadata = extractImageMetadata(imageData)

    savedPath = saveImage(imageData, savePath)

    return (savedPath, metadata)
