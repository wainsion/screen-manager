"""Background content loader using QThreadPool for non-blocking content preparation."""

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, QThreadPool

from app.models.playlist import PlaylistItem, ContentType
from app.renderers.base import RenderedContent
from app.services.temp_manager import TempManager

logger = logging.getLogger(__name__)


class _LoadSignals(QObject):
    """Signals emitted by the load task (QRunnable can't have signals directly)."""
    ready = Signal(object, object)    # (PlaylistItem, RenderedContent)
    error = Signal(object, str)       # (PlaylistItem, error_message)


class _LoadTask(QRunnable):
    """Runnable that prepares content in a background thread."""

    def __init__(self, item: PlaylistItem, temp_manager: TempManager):
        super().__init__()
        self.signals = _LoadSignals()
        self._item = item
        self._temp_manager = temp_manager
        self.setAutoDelete(True)

    def run(self):
        try:
            content = self._prepare()
            self.signals.ready.emit(self._item, content)
        except Exception as e:
            logger.error(f"Content load failed for '{self._item.name}': {e}")
            self.signals.error.emit(self._item, str(e))

    def _prepare(self) -> RenderedContent:
        item = self._item
        source = item.source

        if item.content_type == ContentType.WEB:
            from app.renderers.web_renderer import prepare_web
            return prepare_web(source)

        elif item.content_type == ContentType.IMAGE:
            from app.renderers.image_renderer import prepare_image
            return prepare_image(source)

        elif item.content_type == ContentType.PDF:
            from app.renderers.pdf_renderer import prepare_pdf
            return prepare_pdf(source)

        elif item.content_type == ContentType.PPTX:
            from app.renderers.pptx_renderer import prepare_pptx
            temp_dir = self._temp_manager.get_item_dir(item.id)
            return prepare_pptx(source, temp_dir)

        elif item.content_type == ContentType.DOCX:
            from app.renderers.docx_renderer import prepare_docx
            return prepare_docx(source)

        else:
            raise ValueError(f"Unsupported content type: {item.content_type}")


class ContentLoaderWorker(QObject):
    """Manages background content loading via QThreadPool."""

    content_ready = Signal(object, object)  # (PlaylistItem, RenderedContent)
    error = Signal(object, str)             # (PlaylistItem, error_message)

    def __init__(self, temp_manager: TempManager = None, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._temp_manager = temp_manager or TempManager()

    @property
    def temp_manager(self) -> TempManager:
        return self._temp_manager

    def load(self, item: PlaylistItem):
        """Queue a content load task for the given playlist item."""
        task = _LoadTask(item, self._temp_manager)
        task.signals.ready.connect(self.content_ready.emit)
        task.signals.error.connect(self.error.emit)
        self._pool.start(task)
        logger.debug(f"Queued content load: {item.name} ({item.content_type.value})")
