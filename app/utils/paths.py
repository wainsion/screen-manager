"""Application directory path helpers."""

import os
from pathlib import Path


def get_app_data_dir() -> Path:
    """Return the app's local data directory, creating it if needed."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    app_dir = base / "LobbyScreenManager"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_log_dir() -> Path:
    """Return the log directory, creating it if needed."""
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_config_dir() -> Path:
    """Return the config directory, creating it if needed."""
    config_dir = get_app_data_dir() / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_last_playlist_path() -> Path:
    """Return the path to the file that stores the last-used playlist path."""
    return get_config_dir() / "last_playlist.txt"
