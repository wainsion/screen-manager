"""Base renderer types and RenderedContent data container."""

from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QPixmap


@dataclass
class RenderedContent:
    """
    Container for content prepared by a renderer.

    kind values:
        "url"       — display via QWebEngineView.load(url)
        "pixmap"    — display via QLabel.setPixmap()
        "html"      — display via QWebEngineView.setHtml()
        "slideshow" — display images sequentially in QLabel
    """
    kind: str
    url: Optional[QUrl] = None
    image: Optional[QImage] = None
    images: list[QImage] = field(default_factory=list)
    html: Optional[str] = None

    def get_pixmap(self) -> QPixmap:
        """Convert the stored QImage to a QPixmap (must be called on GUI thread)."""
        if self.image is not None:
            return QPixmap.fromImage(self.image)
        return QPixmap()

    def get_pixmaps(self) -> list[QPixmap]:
        """Convert all stored QImages to QPixmaps (must be called on GUI thread)."""
        return [QPixmap.fromImage(img) for img in self.images]
