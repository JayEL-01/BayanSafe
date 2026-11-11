"""Clean Stage Complete / Mission Results screen for BayanSafe."""
import pygame

from src.core import audio
from src.states.base_state import BaseState
from src.states.loading import LoadingScreen
from src.ui import theme
from src.ui.button import Button


class StageComplete(BaseState):
    """Clean minimal results screen for chapter completion."""

    def __init__(self, game, stats=None, on_replay=None):
        super().__init__(game)
        self.stats = stats or {"score": 100, "time": 60, "stage_id": "chapter_01"}
        self.on_replay = on_replay
        self.font = theme.get_font("tiny")

        self.continue_button = Button("CONTINUE", (110, 140, 100, 20), self.continue_story)

    def continue_story(self):
        audio.play("confirm")
        self.game.state_manager.pop()
        next_stage = self.game.session.current_stage
        from src.states.chapter import ChapterState
        self.game.state_manager.push(LoadingScreen(
            self.game, lambda: ChapterState(self.game, next_stage), f"LOADING {next_stage.upper()}"))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.continue_story()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            self.continue_button.selected = self.continue_button.contains(pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            if self.continue_button.contains(pos):
                self.continue_story()

    def update(self, dt):
        pass

    def draw(self, surface):
        theme.draw_background(surface)
        panel = pygame.Rect(40, 25, 240, 130)
        theme.draw_panel(surface, panel, title="CHAPTER COMPLETE", accent=theme.HONEY)

        theme.draw_text(surface, "MISSION ACCOMPLISHED!", (panel.centerx, 50), "small", theme.SAGE, anchor="center")
        score = self.stats.get("score", 0)
        theme.draw_text(surface, f"SCORE: {score}", (panel.centerx, 80), "tiny", theme.CREAM, anchor="center")

        self.continue_button.draw(surface)
