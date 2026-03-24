"""Full-screen playback window for kiosk display mode."""

import logging

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QStackedWidget, QLabel, QVBoxLayout,
    QGraphicsOpacityEffect,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

logger = logging.getLogger(__name__)


class PlaybackWindow(QWidget):
    """Full-screen window that displays playlist content."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setStyleSheet("background-color: black;")

        # Stacked widget: index 0 = web view, index 1 = image label
        self._stack = QStackedWidget(self)

        # Web engine view for URLs, PDFs, HTML content
        self._web_view = QWebEngineView(self)
        self._web_view.setStyleSheet("background-color: black;")

        # Image label for images and PPTX slides
        self._image_label = QLabel(self)
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet("background-color: black;")
        self._image_label.setScaledContents(False)

        # Error label overlay
        self._error_label = QLabel(self)
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.setStyleSheet(
            "color: #ff6666; background-color: rgba(0,0,0,200); "
            "font-size: 16px; padding: 20px; border-radius: 8px;"
        )
        self._error_label.setVisible(False)

        self._stack.addWidget(self._web_view)    # index 0
        self._stack.addWidget(self._image_label)  # index 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._stack)

        # Fade transition effect
        self._opacity_effect = QGraphicsOpacityEffect(self._stack)
        self._opacity_effect.setOpacity(1.0)
        self._stack.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

    def show_web_content(self, url: QUrl):
        """Load a URL in the embedded web view."""
        self._error_label.setVisible(False)
        self._web_view.load(url)
        self._stack.setCurrentIndex(0)
        logger.debug(f"Displaying web content: {url.toString()}")

    def show_html(self, html: str):
        """Display HTML content directly in the web view."""
        self._error_label.setVisible(False)
        self._web_view.setHtml(html)
        self._stack.setCurrentIndex(0)
        logger.debug("Displaying HTML content")

    def show_image(self, pixmap: QPixmap, scale_mode: str = "fit"):
        """Display an image scaled to the window."""
        self._error_label.setVisible(False)
        scaled = self._scale_pixmap(pixmap, scale_mode)
        self._image_label.setPixmap(scaled)
        self._stack.setCurrentIndex(1)
        logger.debug(f"Displaying image ({pixmap.width()}x{pixmap.height()})")

    def show_error(self, message: str):
        """Show an error message overlaid on the current content."""
        self._error_label.setText(f"⚠ {message}")
        self._error_label.setVisible(True)
        self._error_label.raise_()
        # Position in center
        self._error_label.setGeometry(
            self.width() // 4, self.height() // 2 - 50,
            self.width() // 2, 100,
        )

    def fade_in(self, duration_ms: int = 400):
        """Play a fade-in transition."""
        self._fade_anim.stop()
        self._fade_anim.setDuration(duration_ms)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def _scale_pixmap(self, pixmap: QPixmap, scale_mode: str) -> QPixmap:
        """Scale a pixmap according to the specified mode."""
        target_w = self.width() or 1920
        target_h = self.height() or 1080

        if scale_mode == "stretch":
            return pixmap.scaled(target_w, target_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        elif scale_mode == "fill":
            return pixmap.scaled(target_w, target_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else:  # "fit" (default)
            return pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle hotkeys for exiting kiosk mode."""
        if event.key() == Qt.Key_Escape:
            self._exit_kiosk()
        elif (event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)
              and event.key() == Qt.Key_Q):
            self._exit_kiosk()
        else:
            super().keyPressEvent(event)

    def _exit_kiosk(self):
        """Exit full-screen kiosk mode."""
        logger.info("Exiting kiosk mode")
        self.closed.emit()

    def closeEvent(self, event):
        # Stop any web content loading
        self._web_view.stop()
        event.accept()
