"""
Lobby Screen Manager — Entry Point 

A Windows desktop application for corporate lobby displays.
Cycles through mixed content (web, images, PDFs, Office docs) on a playlist.

Usage:
    python main.py
"""

import sys
import atexit
import logging
from pathlib import Path

from app.utils.logging_config import configure_logging
from app.services.screen_wake import ScreenWake


def main():
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Lobby Screen Manager starting")

    # Ensure screen wake is restored on exit no matter what
    atexit.register(ScreenWake.allow_sleep)

    from app.application import LobbyScreenApp
    from app.ui.main_window import MainWindow

    app = LobbyScreenApp(sys.argv)

    # Load stylesheet
    try:
        qss_path = Path(__file__).parent / "resources" / "styles" / "main.qss"
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
            logger.debug("Stylesheet loaded")
    except Exception as e:
        logger.warning(f"Could not load stylesheet: {e}")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    logger.info(f"Application exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
