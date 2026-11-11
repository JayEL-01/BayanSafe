"""Chapter and Level Registry for BayanSafe.

Orchestrates linear and chapter-select progression through the complete
canonical story, connecting levels to the game engine state manager.
"""

from typing import Dict, Tuple, Type, Optional, List
import pygame

from src.states.base_state import BaseState

from src.story.prologue.level_0_tutorial import PrologueTutorialLevel
from src.story.prologue.level_1_typhoon import PrologueLevel1Typhoon
from src.story.prologue.level_2_flash_flood import PrologueLevel2FlashFlood
from src.story.prologue.level_3_severe_flooding import PrologueLevel3SevereFlooding

from src.story.chapter_1.level_1_earthquake import Chapter1Level1Earthquake
from src.story.chapter_1.level_2_landslide import Chapter1Level2Landslide
from src.story.chapter_1.level_3_calm_wave import Chapter1Level3CalmWave
from src.story.chapter_1.level_4_tsunami import Chapter1Level4Tsunami

from src.story.chapter_2.level_1_fire import Chapter2Level1Fire
from src.story.chapter_2.level_2_earthquake import Chapter2Level2Earthquake
from src.story.chapter_2.level_3_typhoon import Chapter2Level3Typhoon
from src.story.chapter_2.level_4_flash_flood import Chapter2Level4FlashFlood

from src.story.chapter_3.level_1_flash_flood import Chapter3Level1FlashFlood
from src.story.chapter_3.level_2_typhoon import Chapter3Level2Typhoon
from src.story.chapter_3.level_3_severe_flooding import Chapter3Level3SevereFlooding
from src.story.chapter_3.level_4_fire_tsunami import Chapter3Level4FireTsunami

from src.story.chapter_4.level_1_typhoon import Chapter4Level1Typhoon
from src.story.chapter_4.level_2_flash_flood import Chapter4Level2FlashFlood
from src.story.chapter_4.level_3_landslide import Chapter4Level3Landslide
from src.story.chapter_4.level_4_earthquake_volcano import Chapter4Level4EarthquakeVolcano

from src.story.chapter_5.level_1_earthquake_landslide import Chapter5Level1EarthquakeLandslide
from src.story.chapter_5.level_2_volcano import Chapter5Level2Volcano
from src.story.chapter_5.level_3_flash_fire import Chapter5Level3FlashFire
from src.story.chapter_5.level_4_typhoon_severe_flood import Chapter5Level4TyphoonSevereFlood

from src.story.final_mission.shutdown_machine import FinalMissionShutdownMachine

from src.story.endings.ending_1_complete_victory import Ending1CompleteVictoryState
from src.story.endings.ending_2_partial_victory import Ending2PartialVictoryState
from src.story.endings.ending_3_total_failure import Ending3TotalFailureState


STORY_SEQUENCE: List[Tuple[str, str]] = [
    # Prologue: The First Warning (San Isidro)
    ("prologue", "tutorial"),
    ("prologue", "level_1_typhoon"),
    ("prologue", "level_2_flash_flood"),
    ("prologue", "level_3_severe_flooding"),
    # Chapter 1: North West Plateau
    ("chapter_1", "level_1_earthquake"),
    ("chapter_1", "level_2_landslide"),
    ("chapter_1", "level_3_calm_wave"),
    ("chapter_1", "level_4_tsunami"),
    # Chapter 2: Central Town
    ("chapter_2", "level_1_fire"),
    ("chapter_2", "level_2_earthquake"),
    ("chapter_2", "level_3_typhoon"),
    ("chapter_2", "level_4_flash_flood"),
    # Chapter 3: Harbor
    ("chapter_3", "level_1_flash_flood"),
    ("chapter_3", "level_2_typhoon"),
    ("chapter_3", "level_3_severe_flooding"),
    ("chapter_3", "level_4_fire_tsunami"),
    # Chapter 4: North East Plains
    ("chapter_4", "level_1_typhoon"),
    ("chapter_4", "level_2_flash_flood"),
    ("chapter_4", "level_3_landslide"),
    ("chapter_4", "level_4_earthquake_volcano"),
    # Chapter 5: Volcano Valley
    ("chapter_5", "level_1_earthquake_landslide"),
    ("chapter_5", "level_2_volcano"),
    ("chapter_5", "level_3_flash_fire"),
    ("chapter_5", "level_4_typhoon_severe_flood"),
    # Final Mission
    ("final_mission", "shutdown_machine"),
]

LEVEL_MAP: Dict[Tuple[str, str], Type] = {
    ("prologue", "tutorial"): PrologueTutorialLevel,
    ("prologue", "level_1_typhoon"): PrologueLevel1Typhoon,
    ("prologue", "level_2_flash_flood"): PrologueLevel2FlashFlood,
    ("prologue", "level_3_severe_flooding"): PrologueLevel3SevereFlooding,

    ("chapter_1", "level_1_earthquake"): Chapter1Level1Earthquake,
    ("chapter_1", "level_2_landslide"): Chapter1Level2Landslide,
    ("chapter_1", "level_3_calm_wave"): Chapter1Level3CalmWave,
    ("chapter_1", "level_4_tsunami"): Chapter1Level4Tsunami,

    ("chapter_2", "level_1_fire"): Chapter2Level1Fire,
    ("chapter_2", "level_2_earthquake"): Chapter2Level2Earthquake,
    ("chapter_2", "level_3_typhoon"): Chapter2Level3Typhoon,
    ("chapter_2", "level_4_flash_flood"): Chapter2Level4FlashFlood,

    ("chapter_3", "level_1_flash_flood"): Chapter3Level1FlashFlood,
    ("chapter_3", "level_2_typhoon"): Chapter3Level2Typhoon,
    ("chapter_3", "level_3_severe_flooding"): Chapter3Level3SevereFlooding,
    ("chapter_3", "level_4_fire_tsunami"): Chapter3Level4FireTsunami,

    ("chapter_4", "level_1_typhoon"): Chapter4Level1Typhoon,
    ("chapter_4", "level_2_flash_flood"): Chapter4Level2FlashFlood,
    ("chapter_4", "level_3_landslide"): Chapter4Level3Landslide,
    ("chapter_4", "level_4_earthquake_volcano"): Chapter4Level4EarthquakeVolcano,

    ("chapter_5", "level_1_earthquake_landslide"): Chapter5Level1EarthquakeLandslide,
    ("chapter_5", "level_2_volcano"): Chapter5Level2Volcano,
    ("chapter_5", "level_3_flash_fire"): Chapter5Level3FlashFire,
    ("chapter_5", "level_4_typhoon_severe_flood"): Chapter5Level4TyphoonSevereFlood,

    ("final_mission", "shutdown_machine"): FinalMissionShutdownMachine,
}


class StoryLevelState(BaseState):
    """State wrapper for BaseLevel conforming to Game StateManager."""
    def __init__(self, game, chapter_id: str, level_id: str):
        super().__init__(game)
        self.chapter_id = chapter_id
        self.level_id = level_id
        level_cls = LEVEL_MAP.get((chapter_id, level_id), PrologueTutorialLevel)
        self.level = level_cls(game)

    def handle_event(self, event: pygame.Event) -> bool:
        if hasattr(self.level, "pause_menu") and self.level.pause_menu.visible:
            return self.level.pause_menu.handle_event(event, level=self.level)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                return self.level.handle_input("confirm")
            elif event.key == pygame.K_l:
                return self.level.handle_input("legend")
            elif event.key in (pygame.K_UP, pygame.K_w):
                return self.level.handle_input("up")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                return self.level.handle_input("down")
            elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                return self.level.handle_input("escape")
        return False

    def update(self, dt: float):
        self.level.update(dt)

    def draw(self, surface: pygame.Surface):
        self.level.draw(surface)


def load_level(game, chapter_id: str, level_id: str):
    """Instantiate and switch game state to the specified level."""
    state = StoryLevelState(game, chapter_id, level_id)
    if hasattr(game, "session"):
        game.session.current_stage = chapter_id
        norm = game.session.STAGE_ALIASES.get(chapter_id, chapter_id)
        game.session.unlocked.add(norm)
        game.session.unlocked.add(chapter_id)
        game.session.save()
    game.state_manager.change(state)
    return state


def advance_story(game, current_chapter: str, current_level: str):
    """Find current level in sequence and advance to the next."""
    try:
        curr_idx = STORY_SEQUENCE.index((current_chapter, current_level))
        next_idx = curr_idx + 1
        if next_idx < len(STORY_SEQUENCE):
            next_ch, next_lvl = STORY_SEQUENCE[next_idx]
            # If transitioning to a new chapter, complete the previous stage in session
            if next_ch != current_chapter and hasattr(game, "session"):
                game.session.complete_stage(current_chapter)
            load_level(game, next_ch, next_lvl)
        else:
            # Reached end of final mission
            if hasattr(game, "session"):
                game.session.complete_stage(current_chapter)
            launch_ending(game, getattr(game.session, "score_system", None))
    except ValueError:
        load_level(game, "prologue", "tutorial")


def launch_ending(game, score_system):
    """Determine score metrics and launch the appropriate canonical ending."""
    summary = score_system.get_summary() if score_system else {
        "ending_id": "ending_1_complete_victory",
        "preparedness_ratio": 100,
        "warnings_followed": 10,
        "residents_assisted": 8,
        "unsafe_actions": 0,
    }
    ending_id = summary.get("ending_id", "ending_1_complete_victory")

    if ending_id == "ending_1_complete_victory":
        state = Ending1CompleteVictoryState(game, summary)
    elif ending_id == "ending_2_partial_victory":
        state = Ending2PartialVictoryState(game, summary)
    else:
        state = Ending3TotalFailureState(game, summary)

    game.state_manager.change(state)
    return state
