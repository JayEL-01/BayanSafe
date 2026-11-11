"""Audit helper: measure story text widths against their UI boxes.

Not part of the game. Run headless:
    python tools/audit_text_overflow.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.ui import theme  # noqa: E402
from src.story.chapter_registry import LEVEL_MAP, STORY_SEQUENCE  # noqa: E402


class FakeSession:
    pass


class FakeGame:
    def __init__(self):
        self.session = FakeSession()


def width(text, size="tiny"):
    return theme.get_font(size).size(text)[0]


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    game = FakeGame()

    # Box limits (canvas pixels), from base_level.py
    LESSON_BOX_W = 290 - 20          # lesson modal inner width
    DECISION_BOX_W = 280 - 16        # decision box inner width
    OBJ_PANEL_W = 220 - 8            # objective HUD panel inner width

    overflows = {
        "lesson": [],
        "prompt": [],
        "option": [],
        "objective": [],
    }

    for ch, lvl in STORY_SEQUENCE:
        cls = LEVEL_MAP[(ch, lvl)]
        level = cls(game)
        for i, line in enumerate(level.lesson_text.split("\n")):
            w = width(line.strip())
            if w > LESSON_BOX_W:
                overflows["lesson"].append((f"{ch}/{lvl}", i + 1, w, line.strip()[:60]))
        for obj in level.objectives:
            w = width(f"OBJ: {obj}")
            if w > OBJ_PANEL_W:
                overflows["objective"].append((f"{ch}/{lvl}", w, obj[:60]))
        # Decisions live inside on_npc_interacted; collect prompts from the Decision objects
        for npc in level.npcs:
            pass  # prompts are built lazily; measured below via module scan

    # Decision prompts/options: instantiate each level's decision by scanning source
    import inspect  # noqa: E402
    for ch, lvl in STORY_SEQUENCE:
        cls = LEVEL_MAP[(ch, lvl)]
        src = inspect.getsource(cls)
        import re
        for m in re.finditer(r'"prompt":\s*"([^"]+)"', src):
            w = width(m.group(1))
            if w > DECISION_BOX_W:
                overflows["prompt"].append((f"{ch}/{lvl}", w, m.group(1)[:60]))
        for m in re.finditer(r'"text":\s*\n?\s*"([^"]+)"', src):
            w = width("> " + m.group(1))
            if w > DECISION_BOX_W:
                overflows["option"].append((f"{ch}/{lvl}", w, m.group(1)[:60]))

    print(f"Lesson-modal inner width limit: {LESSON_BOX_W}px, decision box: {DECISION_BOX_W}px, obj panel: {OBJ_PANEL_W}px")
    for kind, rows in overflows.items():
        print(f"\n== {kind} overflows: {len(rows)} ==")
        for row in rows[:15]:
            print(f"  {row}")


if __name__ == "__main__":
    main()
