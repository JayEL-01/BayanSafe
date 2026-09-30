import pygame
from src.ui import theme
from src.core import settings
from src.states.base_state import BaseState
from src.states.character_select import CharacterSelect
from src.states.placeholder_state import PlaceholderState
from src.ui import theme
from src.ui.button import Button


class MainMenu(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.backdrop = theme.CozyBackdrop()
        self.time = 0.0
        self.buttons = []
        self.selected = 0
        self._build_buttons()

    def _build_buttons(self):
        entries = [
            ("NEW GAME", self.new_game),
            ("LOAD GAME", self.load_game),
            ("OPTIONS", self.options),
            ("EXIT", self.game.quit),
        ]
        width, height, gap = 110, 20, 6
        x = (settings.INTERNAL_WIDTH - width) // 2
        for i, (text, callback) in enumerate(entries):
            rect = (x, 76 + i * (height + gap), width, height)
            self.buttons.append(Button(text, rect, callback))
        self._update_selection()

    def new_game(self):
        self.game.session.reset()
        self.game.state_manager.push(CharacterSelect(self.game))

    def load_game(self):
        self.game.state_manager.push(PlaceholderState(self.game, "LOAD GAME"))

    def options(self):
        self.game.state_manager.push(PlaceholderState(self.game, "OPTIONS"))

    def _update_selection(self):
        for i, button in enumerate(self.buttons):
            button.selected = (i == self.selected)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
                self._update_selection()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
                self._update_selection()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected].activate()

        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for i, button in enumerate(self.buttons):
                if button.contains(pos):
                    self.selected = i
                    self._update_selection()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for button in self.buttons:
                if button.contains(pos):
                    button.activate()

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        self.backdrop.draw(surface, self.time)
        bob = int(round(pygame.math.Vector2(0, 1.5).y * 0))  # keep title steady
        theme.draw_text(surface, "BAYANSAFE", (160, 28 + bob), "title", theme.HONEY, anchor="center")
        theme.draw_text(surface, "Disaster Preparedness Adventure", (160, 48),
                        "tiny", theme.CREAM, anchor="center")
        for button in self.buttons:
            button.draw(surface)