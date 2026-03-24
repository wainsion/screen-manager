"""Global settings dialog for playlist-wide configuration."""

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox,
    QComboBox, QCheckBox, QGroupBox, QVBoxLayout,
)

from app.models.playlist import GlobalSettings


class GlobalSettingsDialog(QDialog):
    """Edit global playlist settings."""

    def __init__(self, settings: GlobalSettings, parent=None):
        super().__init__(parent)
        self._settings = GlobalSettings(**settings.__dict__)  # work on a copy
        self.setWindowTitle("Playlist Settings")
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)

        # Playback group
        playback_group = QGroupBox("Playback")
        form1 = QFormLayout()

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 3600)
        self._duration_spin.setSuffix(" seconds")
        self._duration_spin.setValue(self._settings.default_duration_seconds)
        form1.addRow("Default Duration:", self._duration_spin)

        self._scale_combo = QComboBox()
        for mode in ("fit", "fill", "stretch"):
            self._scale_combo.addItem(mode.capitalize(), mode)
        idx = self._scale_combo.findData(self._settings.default_scale_mode)
        if idx >= 0:
            self._scale_combo.setCurrentIndex(idx)
        form1.addRow("Default Scale:", self._scale_combo)

        self._transition_spin = QSpinBox()
        self._transition_spin.setRange(0, 5000)
        self._transition_spin.setSuffix(" ms")
        self._transition_spin.setValue(self._settings.transition_delay_ms)
        form1.addRow("Transition Delay:", self._transition_spin)

        self._loop_check = QCheckBox("Loop playlist continuously")
        self._loop_check.setChecked(self._settings.loop)
        form1.addRow(self._loop_check)

        playback_group.setLayout(form1)
        outer.addWidget(playback_group)

        # Display group
        display_group = QGroupBox("Display")
        form2 = QFormLayout()

        self._awake_check = QCheckBox("Keep screen awake during playback")
        self._awake_check.setChecked(self._settings.keep_screen_awake)
        form2.addRow(self._awake_check)

        self._refresh_check = QCheckBox("Refresh web pages each time shown")
        self._refresh_check.setChecked(self._settings.refresh_web_on_show)
        form2.addRow(self._refresh_check)

        display_group.setLayout(form2)
        outer.addWidget(display_group)

        # Startup group
        startup_group = QGroupBox("Startup")
        form3 = QFormLayout()

        self._auto_start_check = QCheckBox("Auto-start playback on app launch")
        self._auto_start_check.setChecked(self._settings.auto_start)
        form3.addRow(self._auto_start_check)

        startup_group.setLayout(form3)
        outer.addWidget(startup_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _accept(self):
        self._settings.default_duration_seconds = self._duration_spin.value()
        self._settings.default_scale_mode = self._scale_combo.currentData()
        self._settings.transition_delay_ms = self._transition_spin.value()
        self._settings.loop = self._loop_check.isChecked()
        self._settings.keep_screen_awake = self._awake_check.isChecked()
        self._settings.refresh_web_on_show = self._refresh_check.isChecked()
        self._settings.auto_start = self._auto_start_check.isChecked()
        self.accept()

    def get_settings(self) -> GlobalSettings:
        """Return the edited settings."""
        return self._settings
