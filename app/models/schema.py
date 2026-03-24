"""Playlist JSON schema validation."""

CURRENT_SCHEMA_VERSION = 1


def validate_playlist_dict(data: dict) -> list[str]:
    """Validate a playlist dictionary. Returns a list of error strings (empty = valid)."""
    errors = []

    if not isinstance(data, dict):
        return ["Root element must be a JSON object"]

    version = data.get("schema_version")
    if version is None:
        errors.append("Missing 'schema_version'")
    elif not isinstance(version, int):
        errors.append("'schema_version' must be an integer")
    elif version > CURRENT_SCHEMA_VERSION:
        errors.append(
            f"Schema version {version} is newer than supported ({CURRENT_SCHEMA_VERSION}). "
            "Please update Lobby Screen Manager."
        )

    gs = data.get("global_settings")
    if gs is not None and not isinstance(gs, dict):
        errors.append("'global_settings' must be a JSON object")

    items = data.get("items")
    if items is not None:
        if not isinstance(items, list):
            errors.append("'items' must be a JSON array")
        else:
            valid_types = {"web", "image", "pdf", "pptx", "docx"}
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"Item {i}: must be a JSON object")
                    continue
                if not item.get("source"):
                    errors.append(f"Item {i}: missing 'source'")
                ct = item.get("content_type", "web")
                if ct not in valid_types:
                    errors.append(f"Item {i}: invalid content_type '{ct}'")
                dur = item.get("duration_seconds")
                if dur is not None and (not isinstance(dur, (int, float)) or dur <= 0):
                    errors.append(f"Item {i}: duration_seconds must be positive")

    return errors
