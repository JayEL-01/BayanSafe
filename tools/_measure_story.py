"""Temporary: measure the real worst-case text across every story level."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
from pathlib import Path
from types import SimpleNamespace
import pygame

from src.core import settings
from src.core.session import GameSession
from src.story.chapter_registry import STORY_SEQUENCE, LEVEL_MAP
from src.ui import theme
from src.ui import text_utils as tu

ROOT = Path(__file__).resolve().parents[1]
W = settings.INTERNAL_WIDTH


def make_game():
    s = GameSession()
    s.character = json.loads((ROOT / "data" / "characters.json").read_text(encoding="utf-8"))[0]
    s.save = lambda: None
    return SimpleNamespace(session=s, state_manager=SimpleNamespace(change=lambda x: None,
                          push=lambda x: None, pop=lambda: None, stack=[]),
                          ask_quit=lambda: None, to_canvas_pos=lambda p: p)


def main():
    pygame.init()
    pygame.display.set_mode((W * 4, settings.INTERNAL_HEIGHT * 4))
    theme._font_cache.clear()
    print("font tiny lh:", tu.line_height("tiny"), "small lh:", tu.line_height("small"))
    worst = {"disaster": ("", 0), "objective": ("", 0), "lesson": ("", 0),
             "lesson_lines": ("", 0), "source": ("", 0), "dialogue": ("", 0)}
    for ch, lvl in STORY_SEQUENCE:
        cls = LEVEL_MAP[(ch, lvl)]
        try:
            g = make_game()
            inst = cls(g)
        except Exception as e:
            print(f"  !! {ch}/{lvl}: {type(e).__name__}: {e}")
            continue
        dt = inst.disaster_type
        for o in inst.objectives:
            if tu.measure_text(o, "tiny")[0] > worst["objective"][1]:
                worst["objective"] = (o, tu.measure_text(o, "tiny")[0])
        if tu.measure_text(dt, "tiny")[0] > worst["disaster"][1]:
            worst["disaster"] = (dt, tu.measure_text(dt, "tiny")[0])
        if tu.measure_text(inst.lesson_source, "tiny")[0] > worst["source"][1]:
            worst["source"] = (inst.lesson_source, tu.measure_text(inst.lesson_source, "tiny")[0])
        # lesson: total wrapped lines at inner width used by modal (300 box -> inner 288, -4)
        lines = []
        for raw in inst.lesson_text.split("\n"):
            if raw.strip():
                lines.extend(tu.wrap_text(raw.strip(), "tiny", 288 - 4))
            else:
                lines.append("")
        if len(lines) > worst["lesson_lines"][1]:
            worst["lesson_lines"] = (inst.lesson_text, len(lines))
        # dialogue lines
        for npc in getattr(inst, "npcs", []):
            for line in getattr(npc, "dialogue", []):
                wpx = tu.measure_text(line, "tiny")[0]
                if wpx > worst["dialogue"][1]:
                    worst["dialogue"] = (line, wpx)
    for k, (s, n) in worst.items():
        if k in ("lesson", "lesson_lines"):
            print(f"WORST {k}: {n} wrapped lines")
        else:
            print(f"WORST {k}: {n}px :: {s[:90]!r}")
    print("\n--- legend descriptions (tiny) ---")
    from src.ui.legend_screen import LegendScreen
    for label, _c, desc in LegendScreen.LEGEND_ENTRIES:
        print(f"  label {tu.measure_text(label,'tiny')[0]:>3}px  desc {tu.measure_text(desc,'tiny')[0]:>3}px | {label} :: {desc}")

    print("\n--- pause menu ---")
    from src.ui.pause_menu import PauseMenu
    print("  option widths:", [(l, tu.measure_text(l, 'tiny')[0]) for l, _ in PauseMenu.MENU_OPTIONS])
    print("  footer width:", tu.measure_text("ESC: Resume  \u00b7  ENTER: Select", "tiny")[0])
    print("  title width small:", tu.measure_text("PAUSED", "small")[0])

    print("\n--- world map ---")
    from src.utils.data_loader import load_json
    wm = load_json("data/world_map.json")
    print("  title:", repr(wm.get("title")), tu.measure_text(str(wm.get("title")), "tiny")[0])
    for loc in wm.get("locations", []):
        print(f"  name {tu.measure_text(str(loc.get('name')),'small')[0]:>3}px label {tu.measure_text(str(loc.get('label')),'tiny')[0]:>3}px | {loc.get('name')} / {loc.get('label')}")
    print("  status widths:", [tu.measure_text(s, 'tiny')[0] for s in ("CURRENTLY EXPLORING", "STORY COMPLETE", "COMPLETED", "UNLOCKED", "LOCKED")])
    print("  hint widths:", [tu.measure_text(s, 'tiny')[0] for s in ("ENTER / CLICK: CONTINUE EXPLORING", "ENTER / CLICK AGAIN: REPLAY REGION", "ENTER / CLICK: EXPLORE REGION", "COMPLETE THE ACTIVE REGION TO UNLOCK")])
    print("  flash width:", tu.measure_text("LOCKED: SECURE THE REGION YOU ARE EXPLORING FIRST", "tiny")[0])

    print("\n--- main menu / footer ---")
    print("  continue msg:", tu.measure_text("Your story is complete. Start a new journey to play again.", "tiny")[0])
    print("  footer v0.1:", tu.measure_text("v0.1", "tiny")[0])
    pygame.quit()


if __name__ == "__main__":
    main()
