"""Headless text-layout audit for BayanSafe.

Renders the UI panels that carry the most text - with deliberately
long/stress strings - and reports any text that:

  * runs off the 320x180 canvas, or
  * overlaps other text on the same panel.

It also writes PNG snapshots to ``tests/theme_previews/`` for eyeballing.
Run it from the project root with::

    venv\\Scripts\\python.exe -m tools.text_overlap_check

This is a development tool; the game does not import it.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
from pathlib import Path
from types import SimpleNamespace

import pygame

from src.core import settings
from src.core.session import GameSession
from src.core.decision_system import Decision
from src.states.main_menu import MainMenu
from src.states.world_map import WorldMap
from src.ui import theme
from src.ui.pause_menu import PauseMenu
from src.ui.legend_screen import LegendScreen
from src.story.base_level import BaseLevel

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "theme_previews"
W, H = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
CANVAS = pygame.Rect(0, 0, W, H)

# --- deliberately worst-case strings (longer than any real content) --------
LONG_DISASTER = "TYPHOON + SEVERE FLOODING + STORM SURGE (RED WARNING)"
LONG_OBJECTIVE = ("Evacuate every resident from the flooded lowland district "
                  "and escort them to the designated safe sanctuary")
LONG_HINT = ("Deep water is rising fast - never wade through it. Move to high "
             "ground and follow the marked evacuation route immediately.")
LONG_COUNTDOWN = "DEEP WATER RISING"
LONG_SPEAKER = "CAPTAIN REYES"
LONG_DIALOGUE = ("Over forty families have registered at the incident desk, and "
                 "the floodwater is still rising along the lowland road, so we "
                 "must move everyone to the ridge before nightfall.")
LONG_PROMPT = ("The water is rising quickly. What is the safest thing to do "
               "right now?")
LONG_OPTIONS = [
    {"text": "Wade straight through the deep water to save time", "safe": False},
    {"text": "Move to higher ground and wait for the rescue boat", "safe": True},
    {"text": "Drink the floodwater if you get thirsty", "safe": False},
    {"text": "Switch off the power and warn your neighbours", "safe": True},
]
LONG_LESSON = (
    "Under Red Rainfall Warnings, evacuation is mandatory and never optional "
    "for any household in the floodplain.\n"
    "Evacuation centers must maintain separate hygiene facilities, clean "
    "drinking water rations, and dedicated protection areas for vulnerable "
    "groups such as infants, elders and persons with disabilities.\n"
    "Boil all tap water or drink only sealed relief water during flood "
    "emergencies, and never wade through moving floodwater.\n"
    "Keep a go-bag with water, food, a flashlight, a radio and a first-aid "
    "kit ready before the storm arrives."
)
LONG_SOURCE = ("NDRRMC Evacuation Camp Coordination & Camp Management (CCCM) "
               "Guidelines")


# ---------------------------------------------------------------------------
# analysis helpers
# ---------------------------------------------------------------------------

def _queued_rects():
    """Snapshot the theme text queue as (rect, text) tuples."""
    out = []
    for font, text, _color, (x, y), _shadow in theme.TEXT_QUEUE:
        w, h = font.size(text)
        out.append((pygame.Rect(x, y, w, h), text))
    return out


def _overlaps(a, b):
    """True when two text rects overlap by at least 2px in each axis."""
    ix = min(a.right, b.right) - max(a.left, b.left)
    iy = min(a.bottom, b.bottom) - max(a.top, b.top)
    return ix >= 2 and iy >= 2


def check(name, surface, save=None):
    """Report out-of-bounds and overlapping text for whatever is queued."""
    rects = _queued_rects()
    problems = []
    for rect, text in rects:
        if not text.strip():
            continue
        if (rect.left < CANVAS.left or rect.top < CANVAS.top
                or rect.right > CANVAS.right or rect.bottom > CANVAS.bottom):
            problems.append(f"  OFF-SCREEN  {rect} {text!r}")
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            ra, ta = rects[i]
            rb, tb = rects[j]
            if not ta.strip() or not tb.strip():
                continue
            if _overlaps(ra, rb):
                problems.append(f"  OVERLAP  {ta!r} {ra}  <->  {tb!r} {rb}")
    if save:
        pygame.image.save(surface, str(OUT / save))
    status = "OK" if not problems else f"{len(problems)} problem(s)"
    print(f"[{status}] {name}")
    for p in problems:
        print(p)
    return problems


def fresh_surface():
    s = pygame.Surface((W, H))
    s.fill(theme.NIGHT)
    return s


# ---------------------------------------------------------------------------
# scenario drivers
# ---------------------------------------------------------------------------

def make_game():
    session = GameSession()
    session.character = json.loads(
        (ROOT / "data" / "characters.json").read_text(encoding="utf-8"))[0]
    session.save = lambda: None
    return SimpleNamespace(
        session=session,
        state_manager=SimpleNamespace(pop=lambda: None, change=lambda s: None,
                                      push=lambda s: None, stack=[]),
        ask_quit=lambda: None,
        to_canvas_pos=lambda pos: pos,
    )


def make_level(game):
    from src.story.prologue.level_3_severe_flooding import (
        PrologueLevel3SevereFlooding,
    )
    return PrologueLevel3SevereFlooding(game)


def run():
    pygame.init()
    pygame.display.set_mode((W * 4, H * 4))
    OUT.mkdir(parents=True, exist_ok=True)
    game = make_game()
    level = make_level(game)
    total = []

    # ---- HUD: longest disaster + objective + hint + countdown ------------
    level.disaster_type = LONG_DISASTER
    level.objectives = [LONG_OBJECTIVE]
    level.current_objective_idx = 0
    level.show_hint(LONG_HINT, 10.0)
    level.start_countdown(90, LONG_COUNTDOWN)
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    level._draw_hud(s)
    level._draw_hint(s)
    level._draw_countdown(s)
    total += check("HUD (long status/objective/hint/countdown)", s, "chk_hud.png")

    # ---- Dialogue box ----------------------------------------------------
    level.hint_timer = 0
    level.stop_countdown()
    level.active_dialogue = [LONG_DIALOGUE]
    level.dialogue_speaker = LONG_SPEAKER
    level.dialogue_idx = 0
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    level._draw_dialogue_box(s)
    total += check("Dialogue box (long line)", s, "chk_dialogue.png")

    # ---- Decision box ----------------------------------------------------
    level.active_dialogue = None
    dec = Decision(decision_id="chk", prompt=LONG_PROMPT,
                   options=LONG_OPTIONS, on_resolved=lambda o: None)
    level.decision_system.trigger_decision(dec)
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    level._draw_decision_box(s)
    total += check("Decision box (long prompt/options)", s, "chk_decision.png")

    # ---- Lesson modal ----------------------------------------------------
    level.decision_system.current_decision = None
    level.show_lesson_modal = True
    level.lesson_source = LONG_SOURCE
    level.lesson_text = LONG_LESSON
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    level._draw_lesson_modal(s)
    total += check("Lesson modal (long lesson)", s, "chk_lesson.png")

    # ---- NPC / interactable labels --------------------------------------
    level.show_lesson_modal = False
    level._drawn_label_rects = []
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    level._draw_interactables(s)
    total += check("Interactable labels", s, "chk_labels.png")

    # ---- Pause menu ------------------------------------------------------
    pause = PauseMenu(game)
    pause.show()
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    pause.draw(s)
    total += check("Pause menu", s, "chk_pause.png")

    # ---- Legend ----------------------------------------------------------
    legend = LegendScreen()
    legend.show()
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    legend.draw(s)
    total += check("Legend screen", s, "chk_legend.png")

    # ---- World map -------------------------------------------------------
    world_map = WorldMap(game)
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    world_map.draw(s)
    total += check("World map", s, "chk_worldmap.png")

    # ---- Main menu -------------------------------------------------------
    menu = MainMenu(game)
    menu.update(1.0)
    s = fresh_surface()
    theme.TEXT_QUEUE.clear()
    menu.draw(s)
    total += check("Main menu", s, "chk_menu.png")

    theme.TEXT_QUEUE.clear()
    pygame.quit()

    print()
    if total:
        print(f"AUDIT FOUND {len(total)} problem(s).")
        return 1
    print("AUDIT CLEAN: no off-screen or overlapping text detected.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
