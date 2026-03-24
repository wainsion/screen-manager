"""Dialog for adding or editing a playlist item."""

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QHBoxLayout, QFileDialog,
    QMessageBox, QLabel,
)

from app.models.playlist import PlaylistItem, ContentType, detect_content_type

logger = logging.getLogger(__name__)

FILE_FILTER = (
    "All Supported Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp "
    "*.pdf *.pptx *.docx);;"
    "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;"
    "PDF (*.pdf);;"
    "PowerPoint (*.pptx);;"
    "Word (*.docx);;"
    "All Files (*)"
)


class ItemEditorDialog(QDialog):
    """Add or edit a playlist item."""

    def __init__(self, item: PlaylistItem = None, parent=None):
        super().__init__(parent)
        self._editing = item is not None
        self._item = item or PlaylistItem()
        self.setWindowTitle("Edit Item" if self._editing else "Add Item")
        self.setMinimumWidth(550)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Display name for this item")
        layout.addRow("Name:", self._name_edit)

        # Source with browse button
        source_layout = QHBoxLayout()
        self._source_edit = QLineEdit()
        self._source_edit.setPlaceholderText("File path, UNC path, or URL")
        self._source_edit.textChanged.connect(self._on_source_changed)
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse)
        source_layout.addWidget(self._source_edit)
        source_layout.addWidget(browse_btn)
        layout.addRow("Source:", source_layout)

        # Content type
        self._type_combo = QComboBox()
        for ct in ContentType:
            self._type_combo.addItem(ct.value.upper(), ct)
        layout.addRow("Type:", self._type_combo)

        # Duration
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 3600)
        self._duration_spin.setSuffix(" seconds")
        self._duration_spin.setValue(15)
        layout.addRow("Duration:", self._duration_spin)

        # Scale mode
        self._scale_combo = QComboBox()
        self._scale_combo.addItem("Global Default", None)
        self._scale_combo.addItem("Fit", "fit")
        self._scale_combo.addItem("Fill", "fill")
        self._scale_combo.addItem("Stretch", "stretch")
        layout.addRow("Scale Mode:", self._scale_combo)

        # Slide advance (shown only for PPTX)
        self._slide_advance_spin = QSpinBox()
        self._slide_advance_spin.setRange(1, 300)
        self._slide_advance_spin.setSuffix(" seconds")
        self._slide_advance_spin.setValue(5)
        self._slide_advance_label = QLabel("Slide Advance:")
        layout.addRow(self._slide_advance_label, self._slide_advance_spin)

        # Enabled
        self._enabled_check = QCheckBox("Item is enabled")
        self._enabled_check.setChecked(True)
        layout.addRow("", self._enabled_check)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        # Initial visibility
        self._update_slide_advance_visibility()

    def _populate(self):
        """Fill fields from the existing item."""
        self._name_edit.setText(self._item.name)
        self._source_edit.setText(self._item.source)
        idx = self._type_combo.findData(self._item.content_type)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        self._duration_spin.setValue(self._item.duration_seconds)
        self._enabled_check.setChecked(self._item.enabled)
        self._slide_advance_spin.setValue(self._item.slide_advance_seconds)

        # Scale mode
        scale_idx = self._scale_combo.findData(self._item.scale_mode)
        if scale_idx >= 0:
            self._scale_combo.setCurrentIndex(scale_idx)

    def _on_source_changed(self, text: str):
        """Auto-detect content type when source changes."""
        ct = detect_content_type(text)
        idx = self._type_combo.findData(ct)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        self._update_slide_advance_visibility()

        # Auto-fill name from filename if name is empty
        if not self._name_edit.text().strip():
            if not text.lower().startswith("http"):
                name = Path(text).stem if text else ""
                self._name_edit.setText(name)

    def _update_slide_advance_visibility(self):
        is_pptx = self._type_combo.currentData() == ContentType.PPTX
        self._slide_advance_label.setVisible(is_pptx)
        self._slide_advance_spin.setVisible(is_pptx)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", FILE_FILTER
        )
        if path:
            self._source_edit.setText(path)

    def _accept(self):
        source = self._source_edit.text().strip()
        if not source:
            QMessageBox.warning(self, "Validation Error", "Source path or URL is required.")
            return

        # Validate file exists for non-web types
        ct = self._type_combo.currentData()
        if ct != ContentType.WEB:
            p = Path(source)
            if not p.exists():
                result = QMessageBox.warning(
                    self, "File Not Found",
                    f"File does not exist:\n{source}\n\nAdd anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if result == QMessageBox.No:
                    return

        self._item.name = self._name_edit.text().strip() or Path(source).stem
        self._item.source = source
        self._item.content_type = ct
        self._item.duration_seconds = self._duration_spin.value()
        self._item.enabled = self._enabled_check.isChecked()
        self._item.slide_advance_seconds = self._slide_advance_spin.value()
        self._item.scale_mode = self._scale_combo.currentData()

        self.accept()

    def get_item(self) -> PlaylistItem:
        """Return the configured playlist item."""
        return self._item
