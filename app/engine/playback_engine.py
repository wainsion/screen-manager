"""Playback engine — cycles through playlist items using QTimer."""

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from app.models.playlist import Playlist, PlaylistItem
from app.renderers.base import RenderedContent
from app.engine.content_loader import ContentLoaderWorker
from app.services.screen_wake import ScreenWake
from app.ui.playback_window import PlaybackWindow

logger = logging.getLogger(__name__)


class PlaybackEngine(QObject):
    """
    Drives playlist playback by cycling through items on a timer.

    Signals:
        item_changed(index, total, name): emitted when a new item starts
        playback_finished(): emitted when non-looping playlist ends
        error_occurred(message): emitted on content load errors
    """

    item_changed = Signal(int, int, str)
    playback_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, playlist: Playlist, window: PlaybackWindow, parent=None):
        super().__init__(parent)
        self._playlist = playlist
        self._window = window
        self._settings = playlist.global_settings

        # Build the play order (enabled items only)
        self._play_order: list[PlaylistItem] = []
        self._current_index = -1
        self._is_playing = False

        # Main item timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._advance)

        # Sub-slide timer for PPTX slideshows
        self._slide_timer = QTimer(self)
        self._slide_timer.timeout.connect(self._advance_slide)
        self._current_slides: list = []
        self._current_slide_index = 0
        self._current_scale_mode = "fit"

        # Content loader
        self._loader = ContentLoaderWorker()
        self._loader.content_ready.connect(self._on_content_ready)
        self._loader.error.connect(self._on_content_error)

        # Track pending item to handle out-of-order signals
        self._pending_item_id: str | None = None

    def start(self):
        """Start or restart playback from the beginning."""
        self._build_play_order()
        if not self._play_order:
            logger.warning("No enabled items to play")
            self.playback_finished.emit()
            return

        self._is_playing = True
        self._current_index = -1

        if self._settings.keep_screen_awake:
            ScreenWake.prevent_sleep()

        logger.info(f"Playback started ({len(self._play_order)} items)")
        self._advance()

    def stop(self):
        """Stop playback and clean up."""
        self._is_playing = False
        self._timer.stop()
        self._slide_timer.stop()
        ScreenWake.allow_sleep()
        self._loader.temp_manager.cleanup()
        logger.info("Playback stopped")

    def _build_play_order(self):
        """Build the list of enabled items in playlist order."""
        self._play_order = [item for item in self._playlist.items if item.enabled]

    def _advance(self):
        """Move to the next item in the playlist."""
        if not self._is_playing:
            return

        self._slide_timer.stop()
        self._current_index += 1

        if self._current_index >= len(self._play_order):
            if self._settings.loop:
                self._current_index = 0
            else:
                logger.info("Playlist finished (no loop)")
                self._is_playing = False
                self.playback_finished.emit()
                return

        item = self._play_order[self._current_index]
        self._pending_item_id = item.id
        total = len(self._play_order)

        self.item_changed.emit(self._current_index, total, item.name)
        logger.info(f"Playing [{self._current_index + 1}/{total}]: {item.name}")

        # Request content loading in background
        self._loader.load(item)

    def _on_content_ready(self, item: PlaylistItem, content: RenderedContent):
        """Handle content that has been prepared by the loader."""
        if not self._is_playing:
            return

        # Ignore stale results from previously skipped items
        if item.id != self._pending_item_id:
            return

        duration = item.duration_seconds or self._settings.default_duration_seconds
        scale_mode = item.scale_mode or self._settings.default_scale_mode
        self._current_scale_mode = scale_mode

        # Apply transition
        if self._settings.transition_delay_ms > 0:
            self._window.fade_in(self._settings.transition_delay_ms)

        # Display the content
        if content.kind == "url":
            self._window.show_web_content(content.url)
        elif content.kind == "pixmap":
            pixmap = content.get_pixmap()
            self._window.show_image(pixmap, scale_mode)
        elif content.kind == "html":
            self._window.show_html(content.html)
        elif content.kind == "slideshow":
            self._current_slides = content.get_pixmaps()
            self._current_slide_index = 0
            if self._current_slides:
                self._window.show_image(self._current_slides[0], scale_mode)
                if len(self._current_slides) > 1:
                    advance_ms = item.slide_advance_seconds * 1000
                    self._slide_timer.start(advance_ms)

        # Schedule advance to next item
        self._timer.start(duration * 1000)

    def _on_content_error(self, item: PlaylistItem, error_msg: str):
        """Handle content loading failure — skip to next after brief delay."""
        if not self._is_playing:
            return

        if item.id != self._pending_item_id:
            return

        logger.error(f"Content error for '{item.name}': {error_msg}")
        self.error_occurred.emit(f"{item.name}: {error_msg}")
        self._window.show_error(f"Failed to load: {item.name}\n{error_msg}")

        # Skip to next item after 2 seconds
        self._timer.start(2000)

    def _advance_slide(self):
        """Cycle through PPTX slides within the current item's duration."""
        if not self._current_slides:
            self._slide_timer.stop()
            return

        self._current_slide_index += 1
        if self._current_slide_index >= len(self._current_slides):
            self._current_slide_index = 0

        self._window.show_image(
            self._current_slides[self._current_slide_index],
            self._current_scale_mode,
        )
