"""Tiny settings store saved alongside the user's campaign save."""
import json
from src.core.save_data import SAVE_DIR, SAVE_PATH
PATH = SAVE_DIR / "prefs.json"

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
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps(_data, indent=2), encoding="utf-8")
    except OSError:
        pass


def has_save():
    """True only when a valid campaign save exists."""
    from src.core.save_data import load_save
    return SAVE_PATH.exists() and load_save() is not None
