"""Renderer for PowerPoint files — extracts slides to images using python-pptx + Pillow."""

import logging
from pathlib import Path

from PySide6.QtGui import QImage

from app.renderers.base import RenderedContent

logger = logging.getLogger(__name__)


def prepare_pptx(source: str, temp_dir: Path) -> RenderedContent:
    """
    Extract slides from a PPTX file and render them as images.

    Uses python-pptx to read the presentation and Pillow to render slides
    as PNG images. This is a best-effort renderer — complex shapes like
    charts, SmartArt, and animations are not supported.
    """
    from app.services.file_converter import pptx_to_images

    image_paths = pptx_to_images(source, temp_dir)
    if not image_paths:
        raise ValueError(f"No slides extracted from: {source}")

    images = []
    for p in image_paths:
        img = QImage(str(p))
        if img.isNull():
            logger.warning(f"Failed to load rendered slide: {p}")
            continue
        images.append(img)

    if not images:
        raise ValueError(f"All slides failed to render from: {source}")

    logger.debug(f"Prepared PPTX: {source} ({len(images)} slides)")
    return RenderedContent(kind="slideshow", images=images)
