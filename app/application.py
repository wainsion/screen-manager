"""QApplication subclass with global setup."""

# QWebEngineWidgets must be imported before QApplication is created
import PySide6.QtWebEngineWidgets  # noqa: F401

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app import APP_NAME, APP_ORG


class LobbyScreenApp(QApplication):
    """Application instance with global configuration."""

    def __init__(self, argv: list[str]):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setOrganizationName(APP_ORG)
        self.setStyle("Fusion")  # Consistent cross-platform look

        # Set a clean default font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
