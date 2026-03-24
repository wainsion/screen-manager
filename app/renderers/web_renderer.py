"""Renderer for web URLs."""

import logging

from PySide6.QtCore import QUrl

from app.renderers.base import RenderedContent

logger = logging.getLogger(__name__)


def prepare_web(source: str) -> RenderedContent:
    """Prepare a web URL for display in QWebEngineView."""
    url = QUrl(source)
    if not url.isValid():
        raise ValueError(f"Invalid URL: {source}")
    logger.debug(f"Prepared web URL: {source}")
    return RenderedContent(kind="url", url=url)
