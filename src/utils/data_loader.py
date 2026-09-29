import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # project root


def load_json(relative_path):
    with open(BASE_DIR / relative_path, "r", encoding="utf-8") as f:
        return json.load(f)