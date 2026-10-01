"""Tiny settings store (language, sound) saved to prefs.json next to main.py."""
import json

from src.utils.data_loader import BASE_DIR

PATH = BASE_DIR / "prefs.json"
SAVE_DIR = BASE_DIR / "saves"          # change this if your save files live elsewhere

_DEFAULTS = {"language": "en", "sfx": True}
_data = dict(_DEFAULTS)

try:
    if PATH.exists():
        _data.update(json.loads(PATH.read_text(encoding="utf-8")))
except (OSError, ValueError):
    pass


def get(key):
    return _data.get(key, _DEFAULTS.get(key))


def put(key, value):
    _data[key] = value
    try:
        PATH.write_text(json.dumps(_data, indent=2), encoding="utf-8")
    except OSError:
        pass


def has_save():
    """True if at least one .json save exists in SAVE_DIR."""
    try:
        return SAVE_DIR.exists() and any(SAVE_DIR.glob("*.json"))
    except OSError:
        return False