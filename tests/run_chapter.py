"""Dev launcher: jump straight into one chapter/mission to test changes.

Quick use (from the project root):

    python tests/run_chapter.py                # uses CHAPTER / LEVEL below
    python tests/run_chapter.py 3              # chapter 3, first mission
    python tests/run_chapter.py chapter_2 level_3_typhoon
    python tests/run_chapter.py 1 --check      # headless load/render check
    python tests/run_chapter.py --list         # show every chapter and level

This file is intentionally not named ``test_*.py`` so ``unittest discover``
does not pick it up. A dev run never writes to your real campaign save or the
database, so it cannot overwrite actual progress.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Edit these for the fastest repeat run.
# ---------------------------------------------------------------------------
CHAPTER = "chapter_3"
LEVEL = None                 # None = the first mission in the chapter
CHARACTER_ID = "juan"        # "juan" or "maria"
# ---------------------------------------------------------------------------

from src.story.chapter_registry import (  # noqa: E402  (needs ROOT on sys.path)
    MISSION_INFO,
    STORY_SEQUENCE,
)


def _build_catalog():
    """Map each chapter to its levels, preserving story order."""
    order = []
    levels = {}
    for chapter_id, level_id in STORY_SEQUENCE:
        if chapter_id not in levels:
            order.append(chapter_id)
            levels[chapter_id] = []
        levels[chapter_id].append(level_id)
    return order, levels


CHAPTER_ORDER, LEVELS_BY_CHAPTER = _build_catalog()

MISSION_TITLES = {
    (mission["chapter_id"], mission["level_id"]): mission["title"]
    for mission in MISSION_INFO
}


def _normalize_chapter(value: str) -> str:
    key = str(value).strip().lower().replace("-", "_")
    if key in LEVELS_BY_CHAPTER:
        return key

    if key in ("0", "intro", "prologue", "prologue_0", "ch0", "chapter0",
               "chapter_0", "chapter_00"):
        return "prologue"
    if key in ("6", "final", "finale", "final_mission", "finalmission",
               "ch6", "chapter6", "chapter_6"):
        return "final_mission"

    number = key
    for prefix in ("chapter_", "chapter", "ch"):
        if number.startswith(prefix):
            number = number[len(prefix):]
            break
    if number.isdigit() and 0 <= int(number) < len(CHAPTER_ORDER):
        return CHAPTER_ORDER[int(number)]

    matches = [chapter for chapter in CHAPTER_ORDER if key and key in chapter]
    if len(matches) == 1:
        return matches[0]

    last_number = len(CHAPTER_ORDER) - 1
    raise SystemExit(
        f"Unknown chapter {value!r}.\n"
        f"Choose one of: {', '.join(CHAPTER_ORDER)} "
        f"(or 0-{last_number}, ch1, finale...)"
    )


def _normalize_level(chapter: str, value: str | None) -> str:
    levels = LEVELS_BY_CHAPTER[chapter]
    if value is None or not str(value).strip():
        return levels[0]

    key = str(value).strip().lower().replace("-", "_")
    if key in levels:
        return key

    if key.isdigit():
        number = int(key)
        # Prologue numbers include the tutorial: 0 = tutorial, 1-3 = missions.
        index = number if chapter == "prologue" else number - 1
        if 0 <= index < len(levels):
            return levels[index]

    matches = [level for level in levels if key and key in level]
    if len(matches) == 1:
        return matches[0]

    raise SystemExit(
        f"Unknown level {value!r} for {chapter}.\n"
        f"Choose one of: {', '.join(levels)}"
    )


def _say(*parts) -> None:
    text = " ".join(str(part) for part in parts)
    try:
        print(text)
    except UnicodeEncodeError:      # very old Windows consoles
        print(text.encode("ascii", "replace").decode("ascii"))


def _print_catalog() -> None:
    _say("BayanSafe story chapters\n")
    for chapter in CHAPTER_ORDER:
        _say(f"{chapter}:")
        for level in LEVELS_BY_CHAPTER[chapter]:
            title = MISSION_TITLES.get((chapter, level), "")
            _say(f"    {level:<30} {title}")
        _say("")


def _seed_session(game, chapter: str, character_id: str) -> None:
    """Give the game a usable session without touching real progress."""
    from src.core.score_system import ScoreSystem
    from src.utils.data_loader import load_json

    session = game.session
    session.reset()

    characters = load_json("data/characters.json")
    character = next((item for item in characters if item.get("id") == character_id), None)
    if character is None:
        ids = ", ".join(str(item.get("id")) for item in characters)
        raise SystemExit(f"Unknown character {character_id!r}. Choose one of: {ids}")

    session.character = character
    session.challenger_id = "DEV"
    session.challenger_name = "DEV"
    session.score_system = ScoreSystem()
    session.difficulty = "standard"

    # Treat everything before the selected chapter as finished so transitions
    # and map focus behave like a real campaign.
    index = CHAPTER_ORDER.index(chapter)
    session.completed = set(CHAPTER_ORDER[:index])
    session.unlocked = set(CHAPTER_ORDER[:index + 1])
    session.current_stage = chapter

    # No disk or database writes during a dev run.
    session.save = lambda: None
    session._sync_run_to_db = lambda *args, **kwargs: None
    session._sync_stage_to_db = lambda *args, **kwargs: None
    session._ensure_db_player = lambda: None
    session.db_player_id = None


def _play(chapter: str, level: str) -> int:
    from src.core.game import Game
    from src.states.world_map import WorldMap
    from src.story.chapter_registry import StoryLevelState

    game = Game()
    _seed_session(game, chapter, CHARACTER_ID)

    # Keep the world map beneath the mission so pause -> world map and
    # "return to title" from the game-over screen still have a screen to show.
    game.state_manager.push(WorldMap(game))
    state = StoryLevelState(game, chapter, level)
    game.state_manager.push(state)

    title = MISSION_TITLES.get((chapter, level), level)
    _say("")
    _say("BayanSafe dev run")
    _say(f"  Chapter : {chapter}")
    _say(f"  Level   : {level}")
    _say(f"  Title   : {title}")
    _say(f"  Hero    : {CHARACTER_ID}")
    _say("  Saving  : disabled (your real campaign is safe)")
    _say("  Controls: WASD/arrows move, E/Space talk, P/Esc pause, M map")
    _say("")

    game.run()
    return 0


def _check(chapter: str, level: str | None = None) -> int:
    """Headless smoke test: construct, update, and render the chapter's levels."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

    import pygame

    from src.core import settings
    from src.core.game import Game
    from src.story.chapter_registry import StoryLevelState

    pygame.init()
    game = Game()
    _seed_session(game, chapter, CHARACTER_ID)
    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    targets = [level] if level else LEVELS_BY_CHAPTER[chapter]
    failures = []
    _say(f"Checking chapter {chapter} ({len(targets)} mission(s))...")
    for target in targets:
        try:
            state = StoryLevelState(game, chapter, target)
            for _ in range(3):
                state.update(1 / 60)
            state.draw(surface)
        except Exception as exc:                      # noqa: BLE001
            failures.append((target, exc))
            _say(f"  FAIL  {target}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
        else:
            _say(f"  PASS  {target}")

    if failures:
        _say(f"\n{len(failures)} mission(s) failed.")
        pygame.quit()
        return 1

    _say("\nAll missions loaded, updated, and rendered.")
    pygame.quit()
    return 0


def main(argv=None) -> int:
    global CHARACTER_ID

    parser = argparse.ArgumentParser(
        description="Run one BayanSafe chapter/mission for manual testing.",
    )
    parser.add_argument(
        "chapter", nargs="?", default=CHAPTER,
        help=f"chapter id or number (default: {CHAPTER})",
    )
    parser.add_argument(
        "level", nargs="?", default=LEVEL,
        help="level id, number, or part of its name (default: first level)",
    )
    parser.add_argument(
        "--character", default=CHARACTER_ID, choices=("juan", "maria"),
        help="hero used for the test run",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="headless smoke test instead of opening the game window",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_levels",
        help="print every chapter and mission, then exit",
    )
    args = parser.parse_args(argv)

    CHARACTER_ID = args.character

    if args.list_levels:
        _print_catalog()
        return 0

    chapter = _normalize_chapter(args.chapter)
    level = _normalize_level(chapter, args.level)

    if args.check:
        return _check(chapter, level if args.level else None)
    return _play(chapter, level)


if __name__ == "__main__":
    raise SystemExit(main())
