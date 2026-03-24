"""Renderer for Word documents — converts to styled HTML."""

import logging

from app.renderers.base import RenderedContent

logger = logging.getLogger(__name__)


def prepare_docx(source: str) -> RenderedContent:
    """
    Convert a DOCX file to styled HTML for display in QWebEngineView.

    Uses python-docx to parse headings, paragraphs, runs, and tables,
    then generates a self-contained HTML document with embedded CSS.
    """
    from app.services.file_converter import docx_to_html

    html = docx_to_html(source)
    logger.debug(f"Prepared DOCX: {source}")
    return RenderedContent(kind="html", html=html)
