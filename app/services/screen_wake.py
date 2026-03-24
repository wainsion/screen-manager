"""Keep screen awake using Windows SetThreadExecutionState API."""

import ctypes
import logging

logger = logging.getLogger(__name__)

# Windows API constants for SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class ScreenWake:
    """Prevents Windows from sleeping or turning off the display."""

    _active = False

    @classmethod
    def prevent_sleep(cls):
        """Tell Windows to keep the display on and prevent sleep."""
        if cls._active:
            return
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            cls._active = True
            logger.info("Screen wake: preventing sleep")
        except Exception as e:
            logger.error(f"Failed to set screen wake: {e}")

    @classmethod
    def allow_sleep(cls):
        """Restore normal Windows sleep/display-off behavior."""
        if not cls._active:
            return
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            cls._active = False
            logger.info("Screen wake: allowing sleep")
        except Exception as e:
            logger.error(f"Failed to restore sleep state: {e}")
