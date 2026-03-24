"""Playlist data model with JSON serialization."""

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Supported content types for playlist items."""
    WEB = "web"
    IMAGE = "image"
    PDF = "pdf"
    PPTX = "pptx"
    DOCX = "docx"


# Map file extensions to content types
EXTENSION_MAP = {
    ".png": ContentType.IMAGE,
    ".jpg": ContentType.IMAGE,
    ".jpeg": ContentType.IMAGE,
    ".bmp": ContentType.IMAGE,
    ".gif": ContentType.IMAGE,
    ".webp": ContentType.IMAGE,
    ".pdf": ContentType.PDF,
    ".pptx": ContentType.PPTX,
    ".docx": ContentType.DOCX,
}


def detect_content_type(source: str) -> ContentType:
    """Auto-detect content type from source path or URL."""
    lower = source.lower().strip()
    if lower.startswith("http://") or lower.startswith("https://"):
        return ContentType.WEB
    ext = Path(lower).suffix
    return EXTENSION_MAP.get(ext, ContentType.WEB)


@dataclass
class PlaylistItem:
    """A single content item in the playlist."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    content_type: ContentType = ContentType.WEB
    source: str = ""
    duration_seconds: int = 15
    enabled: bool = True
    slide_advance_seconds: int = 5
    scale_mode: Optional[str] = None  # None = use global default

    def to_dict(self) -> dict:
        d = asdict(self)
        d["content_type"] = self.content_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PlaylistItem":
        data = dict(data)  # shallow copy
        data["content_type"] = ContentType(data.get("content_type", "web"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class GlobalSettings:
    """Global playlist settings."""
    default_duration_seconds: int = 15
    default_scale_mode: str = "fit"
    loop: bool = True
    keep_screen_awake: bool = True
    refresh_web_on_show: bool = False
    auto_start: bool = False
    transition_delay_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GlobalSettings":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Playlist:
    """Complete playlist with items and settings."""
    schema_version: int = 1
    name: str = "Untitled Playlist"
    global_settings: GlobalSettings = field(default_factory=GlobalSettings)
    items: list[PlaylistItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "global_settings": self.global_settings.to_dict(),
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Playlist":
        gs = GlobalSettings.from_dict(data.get("global_settings", {}))
        items = [PlaylistItem.from_dict(i) for i in data.get("items", [])]
        return cls(
            schema_version=data.get("schema_version", 1),
            name=data.get("name", "Untitled Playlist"),
            global_settings=gs,
            items=items,
        )

    def save(self, path: Path):
        """Save playlist to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Playlist saved to {path}")

    @classmethod
    def load(cls, path: Path) -> "Playlist":
        """Load playlist from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        from app.models.schema import validate_playlist_dict
        errors = validate_playlist_dict(data)
        if errors:
            raise ValueError(f"Playlist validation failed: {'; '.join(errors)}")
        logger.info(f"Playlist loaded from {path}")
        return cls.from_dict(data)
