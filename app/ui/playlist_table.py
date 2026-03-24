"""Playlist table model and view for the main editor."""

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView

from app.models.playlist import PlaylistItem

logger = logging.getLogger(__name__)

COLUMNS = ["", "Name", "Type", "Source", "Duration", "Enabled"]


class PlaylistTableModel(QAbstractTableModel):
    """Table model backed by a list of PlaylistItem objects."""

    def __init__(self, items: list[PlaylistItem] = None, parent=None):
        super().__init__(parent)
        self._items: list[PlaylistItem] = items or []

    @property
    def items(self) -> list[PlaylistItem]:
        return self._items

    def set_items(self, items: list[PlaylistItem]):
        """Replace all items and refresh the view."""
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None

        item = self._items[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return str(index.row() + 1)
            elif col == 1:
                return item.name or "(unnamed)"
            elif col == 2:
                return item.content_type.value.upper()
            elif col == 3:
                # Show filename for local paths, full URL for web
                if item.content_type.value == "web":
                    return item.source
                return Path(item.source).name if item.source else ""
            elif col == 4:
                return f"{item.duration_seconds}s"
            elif col == 5:
                return "Yes" if item.enabled else "No"

        if role == Qt.ToolTipRole and col == 3:
            return item.source

        if role == Qt.TextAlignmentRole:
            if col in (0, 4, 5):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def flags(self, index: QModelIndex):
        base = super().flags(index)
        return base | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def add_item(self, item: PlaylistItem):
        """Append a new item to the end of the list."""
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()

    def remove_item(self, row: int):
        """Remove item at the given row index."""
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()

    def move_item(self, from_row: int, direction: int):
        """Move item up (direction=-1) or down (direction=1)."""
        to_row = from_row + direction
        if 0 <= to_row < len(self._items):
            self.beginResetModel()
            self._items[from_row], self._items[to_row] = (
                self._items[to_row],
                self._items[from_row],
            )
            self.endResetModel()
            return to_row
        return from_row

    def get_item(self, row: int) -> PlaylistItem | None:
        """Return the item at the given row, or None."""
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def update_item(self, row: int, item: PlaylistItem):
        """Replace item at the given row."""
        if 0 <= row < len(self._items):
            self._items[row] = item
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, self.columnCount() - 1),
            )


class PlaylistTableView(QTableView):
    """Pre-configured table view for the playlist."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

    def apply_column_widths(self):
        """Set sensible default column widths after model is set."""
        header = self.horizontalHeader()
        header.resizeSection(0, 40)   # #
        header.resizeSection(1, 200)  # Name
        header.resizeSection(2, 70)   # Type
        header.resizeSection(3, 300)  # Source
        header.resizeSection(4, 70)   # Duration
        header.resizeSection(5, 70)   # Enabled
