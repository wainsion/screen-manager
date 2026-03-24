"""Renderer for PDF files using QWebEngineView's built-in PDF viewer."""

import logging
from pathlib import Path

from PySide6.QtCore import QUrl

from app.renderers.base import RenderedContent

logger = logging.getLogger(__name__)


def prepare_pdf(source: str) -> RenderedContent:
    """Prepare a PDF file for display via QWebEngineView."""
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {source}")
    url = QUrl.fromLocalFile(str(path.resolve()))
    logger.debug(f"Prepared PDF: {source}")
    return RenderedContent(kind="url", url=url)
