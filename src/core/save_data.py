"""Atomic, versioned local campaign save shared by the desktop game and future adapters."""
import json
import os
import sys
from pathlib import Path


def _user_data_dir():
    """Store saves outside the install folder so packaged/read-only installs work."""
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "BayanSafe"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "BayanSafe"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "BayanSafe"


SAVE_DIR = _user_data_dir()
SAVE_PATH = SAVE_DIR / "progress.json"


def write_save(data):
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        temporary = SAVE_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(temporary, SAVE_PATH)
        return True
    except OSError:
        return False


def load_save():
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and data.get("version") in (1, 2, 3) else None
    except (OSError, ValueError, TypeError):
        return None


def delete_save():
    try:
        SAVE_PATH.unlink(missing_ok=True)
    except OSError:
        pass
