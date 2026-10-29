import pygame

from src.core import audio
from src.states.base_state import BaseState
from src.states.character_select import CharacterSelect
from src.ui import theme
from src.ui.button import Button


class NewGameConfirm(BaseState):
    """Require an explicit confirmation before replacing campaign progress."""
    def __init__(self, game):
        super().__init__(game)
        self.buttons = [
            Button("KEEP SAVE", (48, 111, 100, 18), self.cancel),
            Button("START OVER", (172, 111, 100, 18), self.start_over),
        ]
        self.selected = 0
        self._select()

    def _select(self):
        for i, button in enumerate(self.buttons):
            button.selected = i == self.selected

    def cancel(self):
        audio.play("back")
        self.game.state_manager.pop()

    def start_over(self):
        audio.play("confirm")
        self.game.session.erase()
        self.game.state_manager.pop()
        self.game.state_manager.push(CharacterSelect(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                self.selected = 1 - self.selected
                self._select()
                audio.play("tick")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected].activate()
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.cancel()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for i, button in enumerate(self.buttons):
                if button.contains(pos):
                    self.selected = i
                    self._select()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for button in self.buttons:
                if button.contains(pos):
                    button.activate()
                    break

    def draw(self, surface):
        surface.fill((19, 24, 40))
        theme.draw_panel(surface, pygame.Rect(30, 43, 260, 88), title="START A NEW CAMPAIGN", accent=theme.CORAL)
        theme.draw_text(surface, "This replaces your saved campaign progress.", (160, 76), "tiny", theme.CREAM, anchor="center")
        theme.draw_text(surface, "Mission progress resets; local high scores stay saved.", (160, 88), "tiny", theme.CREAM_DIM, anchor="center")
        for button in self.buttons:
            button.draw(surface)
