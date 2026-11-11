"""Chapter exploration state adapter for BayanSafe.

Connects the world map and chapter selection to the canonical code-rendered
story levels in `src/story/`, with full support for dialogue, choice popups,
and pause state.
"""

import pygame
from src.states.base_state import BaseState
from src.story.chapter_registry import StoryLevelState, LEVEL_MAP
from src.ui import theme
from src.ui.dialogue_box import DialogueBox
from src.ui.choice_box import ChoiceBox


class ChapterState(BaseState):
    """Chapter state bridging to the canonical story level system."""

    DEFAULT_LEVELS = {
        "prologue": ("prologue", "tutorial"),
        "chapter_1": ("chapter_1", "level_1_earthquake"),
        "chapter_01": ("chapter_1", "level_1_earthquake"),
        "chapter_2": ("chapter_2", "level_1_fire"),
        "chapter_02": ("chapter_2", "level_1_fire"),
        "chapter_3": ("chapter_3", "level_1_flash_flood"),
        "chapter_03": ("chapter_3", "level_1_flash_flood"),
        "chapter_4": ("chapter_4", "level_1_typhoon"),
        "chapter_04": ("chapter_4", "level_1_typhoon"),
        "chapter_5": ("chapter_5", "level_1_earthquake_landslide"),
        "chapter_05": ("chapter_5", "level_1_earthquake_landslide"),
        "final_mission": ("final_mission", "shutdown_machine"),
    }

    def __init__(self, game, chapter_id="prologue"):
        super().__init__(game)
        self.chapter_id = chapter_id

        # Resolve (chapter_id, level_id)
        if isinstance(chapter_id, tuple) and chapter_id in LEVEL_MAP:
            target_ch, target_lvl = chapter_id
        elif chapter_id in self.DEFAULT_LEVELS:
            target_ch, target_lvl = self.DEFAULT_LEVELS[chapter_id]
        else:
            target_ch, target_lvl = ("prologue", "tutorial")

        self.story_state = StoryLevelState(game, target_ch, target_lvl)
        self.font = theme.get_font("tiny")
        self.dialogue = DialogueBox(self.font)
        self.choice = ChoiceBox(self.font)
        self.paused = False

    def handle_event(self, event: pygame.Event):
        if self.paused:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.paused = False
                return True
            return True

        if self.choice.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.choice.active = False
                    return True
                self.choice.handle_key(event.key)
            return True

        if self.dialogue.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.dialogue.active = False
                    return True
                if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                    self.dialogue.advance()
                    return True
            return True

        return self.story_state.handle_event(event)

    def update(self, dt: float):
        if self.paused:
            return
        if self.dialogue.active:
            self.dialogue.update(dt)
            return
        self.story_state.update(dt)

    def draw(self, surface: pygame.Surface):
        self.story_state.draw(surface)

        if self.dialogue.active:
            self.dialogue.draw(surface)
        elif self.choice.active:
            self.choice.draw(surface)
        elif self.paused:
            # Simple pause panel
            w, h = surface.get_size()
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((10, 15, 20, 200))
            surface.blit(overlay, (0, 0))
            theme.draw_text(surface, "GAME PAUSED", (w // 2, h // 2 - 10), size="small", color=theme.HONEY, anchor="center")
            theme.draw_text(surface, "Press ESC to resume", (w // 2, h // 2 + 10), size="tiny", color=theme.CREAM, anchor="center")


# Compatibility alias
BigMap = ChapterState
