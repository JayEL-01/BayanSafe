import random

import pygame

from src.states.base_state import BaseState
from src.ui import theme
from src.ui.button import Button
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text


class GameOver(BaseState):
    def __init__(self, game, on_retry):
        super().__init__(game)
        self.on_retry = on_retry
        self.font = theme.get_font("tiny")
        self.tip = random.choice(load_json("data/trivia.json"))

        self.selected = 0
        self.buttons = [
            Button("RETRY", (105, 112, 110, 20), self.on_retry),
            Button("WORLD MAP", (105, 140, 110, 20), self.back_to_map),
        ]
        self.update_selection()

    def back_to_map(self):
        self.game.state_manager.pop()   # this screen
        self.game.state_manager.pop()   # the stage

    def update_selection(self):
        for i, b in enumerate(self.buttons):
            b.selected = (i == self.selected)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
                self.update_selection()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected].activate()
            elif event.key == pygame.K_ESCAPE:
                self.back_to_map()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for i, b in enumerate(self.buttons):
                if b.contains(pos):
                    self.selected = i
                    self.update_selection()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for b in self.buttons:
                if b.contains(pos):
                    b.activate()
                    break

    def draw(self, surface):
        theme.fill_bg(surface, theme.mix(theme.NIGHT, theme.CORAL, 0.12))
        theme.draw_text(surface, "Game Over", (160, 12), "title",
                        theme.CORAL, anchor="midtop")

        panel = pygame.Rect(30, 54, 260, 50)
        theme.draw_panel(surface, panel, title="SAFETY TIP", accent=theme.SAGE)
        for i, line in enumerate(wrap_text(self.tip, self.font, 248)[:3]):
            theme.draw_text(surface, line, (panel.x + 6, panel.y + 18 + i * 10),
                            self.font, theme.CREAM)

        for b in self.buttons:
            b.draw(surface)