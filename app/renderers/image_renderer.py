"""Renderer for image files (PNG, JPG, BMP, GIF, WebP)."""

import logging

from PySide6.QtGui import QImage

from app.renderers.base import RenderedContent

logger = logging.getLogger(__name__)


def prepare_image(source: str) -> RenderedContent:
    """Load an image file into a QImage (thread-safe)."""
    image = QImage(source)
    if image.isNull():
        raise ValueError(f"Failed to load image: {source}")
    logger.debug(f"Loaded image: {source} ({image.width()}x{image.height()})")
    return RenderedContent(kind="pixmap", image=image)
