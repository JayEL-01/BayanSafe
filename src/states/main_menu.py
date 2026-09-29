import pygame

from src.core import settings
from src.states.base_state import BaseState
from src.states.placeholder_state import PlaceholderState
from src.ui.button import Button
from src.states.character_select import CharacterSelect

class MainMenu(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.title_font = pygame.font.Font(None, 44)
        self.sub_font = pygame.font.Font(None, 16)
        self.button_font = pygame.font.Font(None, 20)

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
        y = 78
        for i, (text, callback) in enumerate(entries):
            rect = (x, y + i * (height + gap), width, height)
            self.buttons.append(Button(text, rect, callback, self.button_font))
        self._update_selection()

    # ---- button actions (placeholders for now) ----
    def new_game(self):
        self.game.session.reset()
        self.game.state_manager.push(CharacterSelect(self.game))

    def load_game(self):
        self.game.state_manager.push(PlaceholderState(self.game, "LOAD GAME"))

    def options(self):
        self.game.state_manager.push(PlaceholderState(self.game, "OPTIONS"))

    # ---- selection ----
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

    def draw(self, surface):
        surface.fill((15, 25, 55))

        # simple skyline decoration
        for x, h in [(10, 30), (40, 45), (70, 25), (230, 40), (260, 28), (290, 50)]:
            pygame.draw.rect(surface, (25, 40, 80), (x, 180 - h, 22, h))

        # title with a shadow
        shadow = self.title_font.render("BAYANSAFE", False, (0, 0, 0))
        title = self.title_font.render("BAYANSAFE", False, (255, 200, 60))
        surface.blit(shadow, shadow.get_rect(center=(162, 32)))
        surface.blit(title, title.get_rect(center=(160, 30)))

        sub = self.sub_font.render(
            "Disaster Preparedness Adventure", False, (180, 200, 240)
        )
        surface.blit(sub, sub.get_rect(center=(160, 52)))

        for button in self.buttons:
            button.draw(surface)