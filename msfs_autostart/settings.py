from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .i18n import SUPPORTED_LANGUAGES


def settings_path() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local) if local else Path.home() / "AppData" / "Local"
    return base / "MSFS Autostart Manager" / "settings.json"


def load_language() -> str | None:
    path = settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    language = data.get("language") if isinstance(data, dict) else None
    return language if language in SUPPORTED_LANGUAGES else None


def save_language(language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix="settings-", suffix=".json", dir=path.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        temp_path.write_text(json.dumps({"language": language}, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
