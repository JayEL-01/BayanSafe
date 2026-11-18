"""Chapter and Level Registry for BayanSafe.

Orchestrates linear and chapter-select progression through the complete
canonical story, connecting levels to the game engine state manager.
"""

from typing import Dict, Tuple, Type, Optional, List
import pygame

from src.states.base_state import BaseState
from src.ui import theme

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


# Leaderboard metadata: one entry per playable mission, in story order. Keys are
# short enough for the VARCHAR(30) stage_id columns in the database schema.
MISSION_INFO: List[Dict[str, str]] = [
    {"key": "prologue_0", "chapter_id": "prologue", "level_id": "tutorial",
     "chapter_label": "PROLOGUE · SAN ISIDRO", "title": "Prologue: The First Warning"},
    {"key": "prologue_1", "chapter_id": "prologue", "level_id": "level_1_typhoon",
     "chapter_label": "PROLOGUE · SAN ISIDRO", "title": "Prologue - Level 1: The Gale Rising"},
    {"key": "prologue_2", "chapter_id": "prologue", "level_id": "level_2_flash_flood",
     "chapter_label": "PROLOGUE · SAN ISIDRO", "title": "Prologue - Level 2: Torrential Surge"},
    {"key": "prologue_3", "chapter_id": "prologue", "level_id": "level_3_severe_flooding",
     "chapter_label": "PROLOGUE · SAN ISIDRO", "title": "Prologue - Level 3: The Sanctuary"},

    {"key": "ch1_1", "chapter_id": "chapter_1", "level_id": "level_1_earthquake",
     "chapter_label": "CHAPTER 1 · NORTH WEST PLATEAU", "title": "Chapter 1 - Level 1: The Shaking Highland"},
    {"key": "ch1_2", "chapter_id": "chapter_1", "level_id": "level_2_landslide",
     "chapter_label": "CHAPTER 1 · NORTH WEST PLATEAU", "title": "Chapter 1 - Level 2: The Sliding Ridge"},
    {"key": "ch1_3", "chapter_id": "chapter_1", "level_id": "level_3_calm_wave",
     "chapter_label": "CHAPTER 1 · NORTH WEST PLATEAU", "title": "Chapter 1 - Level 3: The Sea Recedes"},
    {"key": "ch1_4", "chapter_id": "chapter_1", "level_id": "level_4_tsunami",
     "chapter_label": "CHAPTER 1 · NORTH WEST PLATEAU", "title": "Chapter 1 - Level 4: The Inundation"},

    {"key": "ch2_1", "chapter_id": "chapter_2", "level_id": "level_1_fire",
     "chapter_label": "CHAPTER 2 · CENTRAL TOWN", "title": "Chapter 2 - Level 1: Inferno in the Streets"},
    {"key": "ch2_2", "chapter_id": "chapter_2", "level_id": "level_2_earthquake",
     "chapter_label": "CHAPTER 2 · CENTRAL TOWN", "title": "Chapter 2 - Level 2: Tremors and Truth"},
    {"key": "ch2_3", "chapter_id": "chapter_2", "level_id": "level_3_typhoon",
     "chapter_label": "CHAPTER 2 · CENTRAL TOWN", "title": "Chapter 2 - Level 3: Winds Over the City"},
    {"key": "ch2_4", "chapter_id": "chapter_2", "level_id": "level_4_flash_flood",
     "chapter_label": "CHAPTER 2 · CENTRAL TOWN", "title": "Chapter 2 - Level 4: The Submerged Avenue"},

    {"key": "ch3_1", "chapter_id": "chapter_3", "level_id": "level_1_flash_flood",
     "chapter_label": "CHAPTER 3 · HARBOR", "title": "Chapter 3 - Level 1: The Flooded Pier"},
    {"key": "ch3_2", "chapter_id": "chapter_3", "level_id": "level_2_typhoon",
     "chapter_label": "CHAPTER 3 · HARBOR", "title": "Chapter 3 - Level 2: The Crashing Seawall"},
    {"key": "ch3_3", "chapter_id": "chapter_3", "level_id": "level_3_severe_flooding",
     "chapter_label": "CHAPTER 3 · HARBOR", "title": "Chapter 3 - Level 3: The Flooded Depots"},
    {"key": "ch3_4", "chapter_id": "chapter_3", "level_id": "level_4_fire_tsunami",
     "chapter_label": "CHAPTER 3 · HARBOR", "title": "Chapter 3 - Level 4: Fire and Water"},

    {"key": "ch4_1", "chapter_id": "chapter_4", "level_id": "level_1_typhoon",
     "chapter_label": "CHAPTER 4 · NORTH EAST PLAINS", "title": "Chapter 4 - Level 1: Winds Over the Fields"},
    {"key": "ch4_2", "chapter_id": "chapter_4", "level_id": "level_2_flash_flood",
     "chapter_label": "CHAPTER 4 · NORTH EAST PLAINS", "title": "Chapter 4 - Level 2: The Dike Breaks"},
    {"key": "ch4_3", "chapter_id": "chapter_4", "level_id": "level_3_landslide",
     "chapter_label": "CHAPTER 4 · NORTH EAST PLAINS", "title": "Chapter 4 - Level 3: The Exposed Arteries"},
    {"key": "ch4_4", "chapter_id": "chapter_4", "level_id": "level_4_earthquake_volcano",
     "chapter_label": "CHAPTER 4 · NORTH EAST PLAINS", "title": "Chapter 4 - Level 4: The Earth Groans"},

    {"key": "ch5_1", "chapter_id": "chapter_5", "level_id": "level_1_earthquake_landslide",
     "chapter_label": "CHAPTER 5 · VOLCANO VALLEY", "title": "Chapter 5 - Level 1: The Splitting Caldera"},
    {"key": "ch5_2", "chapter_id": "chapter_5", "level_id": "level_2_volcano",
     "chapter_label": "CHAPTER 5 · VOLCANO VALLEY", "title": "Chapter 5 - Level 2: Ashfall Darkness"},
    {"key": "ch5_3", "chapter_id": "chapter_5", "level_id": "level_3_flash_fire",
     "chapter_label": "CHAPTER 5 · VOLCANO VALLEY", "title": "Chapter 5 - Level 3: Rain of Fire"},
    {"key": "ch5_4", "chapter_id": "chapter_5", "level_id": "level_4_typhoon_severe_flood",
     "chapter_label": "CHAPTER 5 · VOLCANO VALLEY", "title": "Chapter 5 - Level 4: The Concrete Flood (Lahar)"},

    {"key": "final", "chapter_id": "final_mission", "level_id": "shutdown_machine",
     "chapter_label": "FINAL MISSION", "title": "Final Mission: The Aegis Core"},
]

# One entry per world-map chapter. Chapter boards aggregate the best run of
# every mission inside the chapter, so completing a chapter records a total.
CHAPTER_INFO: List[Dict[str, str]] = [
    {"key": "prologue", "chapter_label": "PROLOGUE · SAN ISIDRO",
     "title": "Prologue: The First Warning"},
    {"key": "chapter_1", "chapter_label": "CHAPTER 1 · NORTH WEST PLATEAU",
     "title": "Chapter 1: The Shaking Highland"},
    {"key": "chapter_2", "chapter_label": "CHAPTER 2 · CENTRAL TOWN",
     "title": "Chapter 2: Inferno in the Streets"},
    {"key": "chapter_3", "chapter_label": "CHAPTER 3 · HARBOR",
     "title": "Chapter 3: The Flooded Pier"},
    {"key": "chapter_4", "chapter_label": "CHAPTER 4 · NORTH EAST PLAINS",
     "title": "Chapter 4: Winds Over the Fields"},
    {"key": "chapter_5", "chapter_label": "CHAPTER 5 · VOLCANO VALLEY",
     "title": "Chapter 5: The Splitting Caldera"},
    {"key": "final_mission", "chapter_label": "FINAL MISSION",
     "title": "Final Mission: The Aegis Core"},
]

MISSION_KEYS: Dict[Tuple[str, str], str] = {
    (mission["chapter_id"], mission["level_id"]): mission["key"]
    for mission in MISSION_INFO
}


def mission_key(chapter_id: str, level_id: str) -> str:
    """Return the stable leaderboard key for a story mission."""
    key = MISSION_KEYS.get((chapter_id, level_id))
    if key:
        return key
    return f"{chapter_id}:{level_id}"[:30]


class StoryLevelState(BaseState):
    """State wrapper for BaseLevel conforming to Game StateManager."""
    def __init__(self, game, chapter_id: str, level_id: str):
        super().__init__(game)
        self.chapter_id = chapter_id
        self.level_id = level_id
        level_cls = LEVEL_MAP.get((chapter_id, level_id), PrologueTutorialLevel)
        self.level = level_cls(game)
        # Restore the active quest marker after the world has been built. The
        # session flag is one-shot and is set by load_level(..., resume=True).
        if hasattr(self.level, "restore_progress"):
            self.level.restore_progress()

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


CHAPTER_RECAPS: Dict[str, Dict[str, str]] = {
    "prologue": {
        "title": "PROLOGUE COMPLETED: SAN ISIDRO SURVIVES",
        "story": (
            "The coastal barangay of San Isidro withstood the typhoon's initial fury through early warnings "
            "and communal solidarity. Go-Bags were secured and neighbors sheltered together. "
            "Yet as the gale subsides, unnatural subterranean vibrations pulse toward the Northwest Plateau."
        ),
    },
    "chapter_1": {
        "title": "CHAPTER 1 COMPLETED: NORTHWEST PLATEAU DEFENDED",
        "story": (
            "Plateau families heeded seismic fault alerts and evacuated to elevated ridge lines before the tsunami arrived. "
            "Rockfalls were navigated and coastal warning sirens sounded in time. "
            "As plateau families assemble in safety, black smoke erupts from Central Town's commercial power grid."
        ),
    },
    "chapter_2": {
        "title": "CHAPTER 2 COMPLETED: CENTRAL TOWN SECURED",
        "story": (
            "Flash fires were extinguished, hospital emergency power was restored, and persons with disabilities "
            "were escorted safely across cleared access ramps to the Civic Center through pure Bayanihan. "
            "Central Town holds firm, but massive tidal surges are now crashing over the Harbor District seawalls!"
        ),
    },
    "chapter_3": {
        "title": "CHAPTER 3 COMPLETED: HARBOR DISTRICT SALVAGED",
        "story": (
            "Cargo lines were secured, the backup VHF marine transceiver was salvaged and calibrated to Channel 16, "
            "and ruptured fuel lines were safely isolated before the tsunami hit the pier. "
            "With harbor assets preserved, emergency dispatch alerts focus on the agricultural Northeast Plains."
        ),
    },
    "chapter_4": {
        "title": "CHAPTER 4 COMPLETED: NORTHEAST PLAINS SAFEGUARDED",
        "story": (
            "Livestock were untethered to elevated mounds, breached irrigation canals were reinforced with sandbags, "
            "and the 6-kilometer Permanent Danger Zone was established around the caldera boundary. "
            "Telemetry decoded from severed waveguides confirms: the crisis originates inside Volcano Valley!"
        ),
    },
    "chapter_5": {
        "title": "CHAPTER 5 COMPLETED: CALDERA GORGE BREACHED",
        "story": (
            "Valley-wide acoustic sirens mobilized lowland villages ahead of torrential lahar mudflows. "
            "Wildfire firebreaks protected generator reserves, and the subterranean facility airlock was breached. "
            "Juan and Maria stand at the core threshold of Project Aegis-Terra for the decisive confrontation!"
        ),
    },
}

CHAPTER_BRIDGES: Dict[Tuple[str, str], str] = {
    ("prologue", "chapter_1"): "San Isidro holds against the first storm. Now tremors rock the Northwest Plateau...",
    ("chapter_1", "chapter_2"): "Plateau evacuees reach high ground. Sirens echo across Central Town as transformers ignite...",
    ("chapter_2", "chapter_3"): "Central Town stabilizes under emergency protocols. Seawater breaches the Harbor seawalls...",
    ("chapter_3", "chapter_4"): "Harbor assets salvaged and secured. Storm fronts collide over the agricultural Northeast Plains...",
    ("chapter_4", "chapter_5"): "The plains communities rally together. Deep beneath Volcano Valley, the Aegis-Terra machine surges...",
    ("chapter_5", "final_mission"): "The caldera ruptures! Juan and Maria penetrate the Aegis-Terra core facility for the final shutdown...",
}


class StoryTransitionState(BaseState):
    """Atmospheric transition card between story missions and chapters."""

    def __init__(self, game, next_ch: str, next_lvl: str, bridge_text: str = "",
                 is_chapter_end: bool = False, completed_ch: str = ""):
        super().__init__(game)
        self.next_ch = next_ch
        self.next_lvl = next_lvl
        self.chapter_id = next_ch
        self.level_id = next_lvl
        self.bridge_text = bridge_text
        self.is_chapter_end = is_chapter_end
        self.completed_ch = completed_ch
        self.timer = 0.0
        self.duration = 4.0 if is_chapter_end else 3.2

        self.info = next(
            (m for m in MISSION_INFO if m["chapter_id"] == next_ch and m["level_id"] == next_lvl),
            {"title": f"{next_ch}: {next_lvl}", "chapter_label": next_ch.upper()}
        )

    def handle_event(self, event: pygame.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e, pygame.K_ESCAPE):
                self._proceed()
                return True
        return False

    def _proceed(self):
        load_level(self.game, self.next_ch, self.next_lvl)

    def update(self, dt: float):
        self.timer += dt
        if self.timer >= self.duration:
            self._proceed()

    def draw(self, surface: pygame.Surface):
        w, h = surface.get_size()
        theme.draw_background(surface)

        if self.is_chapter_end and self.completed_ch in CHAPTER_RECAPS:
            recap = CHAPTER_RECAPS[self.completed_ch]
            title = recap["title"]
            subtitle = f"NEXT: {self.info.get('title')}"
            body = recap["story"]
            accent = theme.SAGE
        else:
            title = self.info.get("title", "Next Level")
            subtitle = self.info.get("chapter_label", "NEXT MISSION")
            body = self.bridge_text
            accent = theme.HONEY

        theme.draw_title_card(
            surface, (8, 8, w - 16, h - 16), title, subtitle, body,
            footer="[SPACE] Continue >", accent=accent,
        )


def load_level(game, chapter_id: str, level_id: str, resume: bool = False):
    """Instantiate and switch game state to the specified level."""
    if hasattr(game, "session"):
        game.session.begin_level(chapter_id, level_id, resume=resume)
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
    """Find current level in sequence and advance to the next with transition."""
    try:
        curr_idx = STORY_SEQUENCE.index((current_chapter, current_level))
        next_idx = curr_idx + 1
        if next_idx < len(STORY_SEQUENCE):
            next_ch, next_lvl = STORY_SEQUENCE[next_idx]
            # If transitioning to a new chapter, complete previous stage in session
            if hasattr(game, "session"):
                if next_ch != current_chapter:
                    game.session.complete_stage(current_chapter)
                game.session.current_stage = next_ch
                norm = game.session.STAGE_ALIASES.get(next_ch, next_ch)
                game.session.unlocked.add(norm)
                game.session.unlocked.add(next_ch)
                game.session.save()

            is_ch_end = (next_ch != current_chapter)
            bridge = CHAPTER_BRIDGES.get((current_chapter, next_ch))
            if not bridge:
                bridge = "Bayanihan continues. Mobilizing response teams to the next sector!"

            trans = StoryTransitionState(
                game, next_ch, next_lvl, bridge,
                is_chapter_end=is_ch_end, completed_ch=current_chapter
            )
            game.state_manager.change(trans)
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
