"""Main application window — playlist editor with toolbar and status bar."""

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QWidget, QVBoxLayout, QLabel, QHBoxLayout,
)

from app import APP_NAME, APP_VERSION
from app.models.playlist import Playlist, PlaylistItem, ContentType
from app.ui.playlist_table import PlaylistTableModel, PlaylistTableView
from app.ui.item_editor_dialog import ItemEditorDialog
from app.ui.settings_panel import GlobalSettingsDialog
from app.utils.paths import get_last_playlist_path

logger = logging.getLogger(__name__)

PLAYLIST_FILTER = "Lobby Playlists (*.lsm.json);;JSON Files (*.json);;All Files (*)"


class MainWindow(QMainWindow):
    """Main editor window for managing the playlist."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 550)
        self.resize(1050, 650)

        self._playlist = Playlist()
        self._playlist_path: Path | None = None
        self._modified = False

        # Playback state
        self._playback_window = None
        self._playback_engine = None
        self._is_playing = False

        self._build_ui()
        self._create_actions()
        self._create_toolbar()
        self._create_menubar()
        self._create_statusbar()

        # Try loading last playlist
        self._try_load_last_playlist()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)

        # Playlist table
        self._table_model = PlaylistTableModel(self._playlist.items)
        self._table_view = PlaylistTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.apply_column_widths()
        self._table_view.doubleClicked.connect(self._edit_selected_item)
        layout.addWidget(self._table_view)

        # Now-playing info bar
        info_bar = QHBoxLayout()
        self._now_playing_label = QLabel("Ready")
        self._now_playing_label.setStyleSheet(
            "font-weight: bold; padding: 4px; color: #555;"
        )
        info_bar.addWidget(self._now_playing_label)
        info_bar.addStretch()
        self._item_count_label = QLabel("0 items")
        self._item_count_label.setStyleSheet("color: #888; padding: 4px;")
        info_bar.addWidget(self._item_count_label)
        layout.addLayout(info_bar)

        self.setCentralWidget(central)
        self._update_item_count()

    def _create_actions(self):
        self._act_add_file = QAction("Add File", self)
        self._act_add_file.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self._act_add_file.triggered.connect(self._add_file_item)

        self._act_add_url = QAction("Add URL", self)
        self._act_add_url.setShortcut(QKeySequence("Ctrl+U"))
        self._act_add_url.triggered.connect(self._add_url_item)

        self._act_remove = QAction("Remove", self)
        self._act_remove.setShortcut(QKeySequence.Delete)
        self._act_remove.triggered.connect(self._remove_selected_item)

        self._act_edit = QAction("Edit", self)
        self._act_edit.setShortcut(QKeySequence("Ctrl+E"))
        self._act_edit.triggered.connect(self._edit_selected_item)

        self._act_move_up = QAction("Move Up", self)
        self._act_move_up.setShortcut(QKeySequence("Ctrl+Up"))
        self._act_move_up.triggered.connect(lambda: self._move_item(-1))

        self._act_move_down = QAction("Move Down", self)
        self._act_move_down.setShortcut(QKeySequence("Ctrl+Down"))
        self._act_move_down.triggered.connect(lambda: self._move_item(1))

        self._act_settings = QAction("Settings", self)
        self._act_settings.triggered.connect(self._open_settings)

        self._act_play = QAction("Start Playback", self)
        self._act_play.setShortcut(QKeySequence("F5"))
        self._act_play.triggered.connect(self._start_playback)

        self._act_stop = QAction("Stop Playback", self)
        self._act_stop.setShortcut(QKeySequence("Shift+F5"))
        self._act_stop.triggered.connect(self._stop_playback)
        self._act_stop.setEnabled(False)

        self._act_save = QAction("Save Playlist", self)
        self._act_save.setShortcut(QKeySequence.Save)
        self._act_save.triggered.connect(self._save_playlist)

        self._act_save_as = QAction("Save As...", self)
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_save_as.triggered.connect(self._save_playlist_as)

        self._act_open = QAction("Open Playlist", self)
        self._act_open.setShortcut(QKeySequence.Open)
        self._act_open.triggered.connect(self._open_playlist)

        self._act_new = QAction("New Playlist", self)
        self._act_new.setShortcut(QKeySequence.New)
        self._act_new.triggered.connect(self._new_playlist)

    def _create_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        tb.addAction(self._act_add_file)
        tb.addAction(self._act_add_url)
        tb.addSeparator()
        tb.addAction(self._act_edit)
        tb.addAction(self._act_remove)
        tb.addSeparator()
        tb.addAction(self._act_move_up)
        tb.addAction(self._act_move_down)
        tb.addSeparator()
        tb.addAction(self._act_play)
        tb.addAction(self._act_stop)
        tb.addSeparator()
        tb.addAction(self._act_settings)

        self.addToolBar(tb)

    def _create_menubar(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_menu.addAction(self._act_new)
        file_menu.addAction(self._act_open)
        file_menu.addSeparator()
        file_menu.addAction(self._act_save)
        file_menu.addAction(self._act_save_as)
        file_menu.addSeparator()
        quit_act = file_menu.addAction("Exit")
        quit_act.setShortcut(QKeySequence("Alt+F4"))
        quit_act.triggered.connect(self.close)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self._act_add_file)
        edit_menu.addAction(self._act_add_url)
        edit_menu.addAction(self._act_edit)
        edit_menu.addAction(self._act_remove)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act_move_up)
        edit_menu.addAction(self._act_move_down)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act_settings)

        playback_menu = menu.addMenu("&Playback")
        playback_menu.addAction(self._act_play)
        playback_menu.addAction(self._act_stop)

    def _create_statusbar(self):
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ── Item actions ──────────────────────────────────────────────

    def _add_file_item(self):
        dlg = ItemEditorDialog(parent=self)
        if dlg.exec() == ItemEditorDialog.Accepted:
            self._table_model.add_item(dlg.get_item())
            self._mark_modified()

    def _add_url_item(self):
        item = PlaylistItem(content_type=ContentType.WEB)
        dlg = ItemEditorDialog(item, parent=self)
        if dlg.exec() == ItemEditorDialog.Accepted:
            self._table_model.add_item(dlg.get_item())
            self._mark_modified()

    def _remove_selected_item(self):
        row = self._selected_row()
        if row is not None:
            self._table_model.remove_item(row)
            self._mark_modified()

    def _edit_selected_item(self):
        row = self._selected_row()
        if row is None:
            return
        item = self._table_model.get_item(row)
        if item is None:
            return
        # Edit a copy so cancel doesn't mutate
        import copy
        item_copy = copy.deepcopy(item)
        dlg = ItemEditorDialog(item_copy, parent=self)
        if dlg.exec() == ItemEditorDialog.Accepted:
            self._table_model.update_item(row, dlg.get_item())
            self._mark_modified()

    def _move_item(self, direction: int):
        row = self._selected_row()
        if row is not None:
            new_row = self._table_model.move_item(row, direction)
            self._table_view.selectRow(new_row)
            self._mark_modified()

    def _selected_row(self) -> int | None:
        indexes = self._table_view.selectionModel().selectedRows()
        if indexes:
            return indexes[0].row()
        return None

    # ── Playlist I/O ──────────────────────────────────────────────

    def _new_playlist(self):
        if not self._confirm_discard():
            return
        self._playlist = Playlist()
        self._playlist_path = None
        self._table_model.set_items(self._playlist.items)
        self._modified = False
        self._update_title()
        self._update_item_count()
        self._status_bar.showMessage("New playlist created")

    def _open_playlist(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open Playlist", "", PLAYLIST_FILTER)
        if not path:
            return
        self._load_playlist_file(Path(path))

    def _load_playlist_file(self, path: Path):
        try:
            self._playlist = Playlist.load(path)
            self._playlist_path = path
            self._table_model.set_items(self._playlist.items)
            self._modified = False
            self._update_title()
            self._update_item_count()
            self._save_last_playlist_path(path)
            self._status_bar.showMessage(f"Loaded: {path.name}")
            logger.info(f"Loaded playlist: {path}")

            # Auto-start if configured
            if self._playlist.global_settings.auto_start and not self._is_playing:
                self._start_playback()
        except Exception as e:
            logger.error(f"Failed to load playlist: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load playlist:\n{e}")

    def _save_playlist(self):
        if self._playlist_path:
            self._do_save(self._playlist_path)
        else:
            self._save_playlist_as()

    def _save_playlist_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Playlist", "playlist.lsm.json", PLAYLIST_FILTER
        )
        if path:
            self._do_save(Path(path))

    def _do_save(self, path: Path):
        try:
            self._playlist.items = self._table_model.items
            self._playlist.save(path)
            self._playlist_path = path
            self._modified = False
            self._update_title()
            self._save_last_playlist_path(path)
            self._status_bar.showMessage(f"Saved: {path.name}")
        except Exception as e:
            logger.error(f"Failed to save playlist: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save playlist:\n{e}")

    # ── Settings ──────────────────────────────────────────────────

    def _open_settings(self):
        dlg = GlobalSettingsDialog(self._playlist.global_settings, parent=self)
        if dlg.exec() == GlobalSettingsDialog.Accepted:
            self._playlist.global_settings = dlg.get_settings()
            self._mark_modified()
            self._status_bar.showMessage("Settings updated")

    # ── Playback ──────────────────────────────────────────────────

    def _start_playback(self):
        enabled_items = [i for i in self._table_model.items if i.enabled]
        if not enabled_items:
            QMessageBox.information(
                self, "No Items", "Add at least one enabled item to the playlist."
            )
            return

        self._is_playing = True
        self._act_play.setEnabled(False)
        self._act_stop.setEnabled(True)
        self._status_bar.showMessage("Starting playback...")

        # Import here to avoid circular imports at module load
        from app.ui.playback_window import PlaybackWindow
        from app.engine.playback_engine import PlaybackEngine

        self._playback_window = PlaybackWindow()
        self._playlist.items = self._table_model.items
        self._playback_engine = PlaybackEngine(
            self._playlist, self._playback_window
        )
        self._playback_engine.item_changed.connect(self._on_item_changed)
        self._playback_engine.playback_finished.connect(self._stop_playback)
        self._playback_engine.error_occurred.connect(self._on_playback_error)
        self._playback_window.closed.connect(self._stop_playback)
        self._playback_window.showFullScreen()
        self._playback_engine.start()

    def _stop_playback(self):
        if self._playback_engine:
            self._playback_engine.stop()
            self._playback_engine = None
        if self._playback_window:
            self._playback_window.close()
            self._playback_window.deleteLater()
            self._playback_window = None

        self._is_playing = False
        self._act_play.setEnabled(True)
        self._act_stop.setEnabled(False)
        self._now_playing_label.setText("Ready")
        self._status_bar.showMessage("Playback stopped")
        logger.info("Playback stopped")

    def _on_item_changed(self, index: int, total: int, item_name: str):
        self._now_playing_label.setText(f"Playing: {item_name}")
        self._status_bar.showMessage(f"Item {index + 1}/{total}: {item_name}")

    def _on_playback_error(self, msg: str):
        self._status_bar.showMessage(f"Error: {msg}")
        logger.warning(f"Playback error: {msg}")

    # ── Helpers ───────────────────────────────────────────────────

    def _mark_modified(self):
        self._modified = True
        self._update_title()
        self._update_item_count()

    def _update_title(self):
        name = self._playlist.name
        path_str = f" — {self._playlist_path.name}" if self._playlist_path else ""
        mod = " *" if self._modified else ""
        self.setWindowTitle(f"{APP_NAME}{path_str}{mod}")

    def _update_item_count(self):
        count = len(self._table_model.items)
        enabled = sum(1 for i in self._table_model.items if i.enabled)
        self._item_count_label.setText(f"{enabled}/{count} items enabled")

    def _confirm_discard(self) -> bool:
        if not self._modified:
            return True
        result = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Discard them?",
            QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        return result == QMessageBox.Discard

    def _try_load_last_playlist(self):
        try:
            last_path_file = get_last_playlist_path()
            if last_path_file.exists():
                stored = last_path_file.read_text(encoding="utf-8").strip()
                p = Path(stored)
                if p.exists():
                    self._load_playlist_file(p)
        except Exception as e:
            logger.debug(f"Could not load last playlist: {e}")

    def _save_last_playlist_path(self, path: Path):
        try:
            get_last_playlist_path().write_text(
                str(path.resolve()), encoding="utf-8"
            )
        except Exception as e:
            logger.debug(f"Could not save last playlist path: {e}")

    def closeEvent(self, event):
        if self._is_playing:
            self._stop_playback()
        if self._modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if result == QMessageBox.Save:
                self._save_playlist()
                event.accept()
            elif result == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        event.accept()
