"""Temporary file management for converted content (slide images, etc.)."""

import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class TempManager:
    """Manages a temporary directory tree for converted files."""

    def __init__(self):
        self._base = Path(tempfile.mkdtemp(prefix="lobby_screen_"))
        logger.debug(f"Temp directory created: {self._base}")

    @property
    def base_dir(self) -> Path:
        return self._base

    def get_item_dir(self, item_id: str) -> Path:
        """Return a per-item temp directory, created on demand."""
        d = self._base / item_id
        d.mkdir(exist_ok=True)
        return d

    def cleanup_item(self, item_id: str):
        """Remove temp files for a specific item."""
        d = self._base / item_id
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    def cleanup(self):
        """Remove all temp files. Call on app exit."""
        if self._base.exists():
            shutil.rmtree(self._base, ignore_errors=True)
            logger.debug(f"Temp directory removed: {self._base}")
