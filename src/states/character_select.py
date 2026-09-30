import random

import pygame

from src.states.base_state import BaseState
from src.states.world_map import WorldMap
from src.ui import theme
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text


class CharacterSelect(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.characters = load_json("data/characters.json")
        self.trivia = load_json("data/trivia.json")
        random.shuffle(self.trivia)
        self.trivia_index = 0
        self.trivia_timer = 0.0

        self.font = theme.get_font("tiny")
        self.selected = 0
        self.cards = [pygame.Rect(50, 24, 100, 84), pygame.Rect(170, 24, 100, 84)]

    def confirm(self):
        self.game.session.character = self.characters[self.selected]
        self.game.state_manager.change(WorldMap(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(self.characters)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.characters)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.confirm()
            elif event.key == pygame.K_ESCAPE:
                self.game.state_manager.pop()

        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for i, card in enumerate(self.cards):
                if card.collidepoint(pos):
                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for i, card in enumerate(self.cards):
                if card.collidepoint(pos):
                    self.selected = i
                    self.confirm()

    def update(self, dt):
        self.trivia_timer += dt
        if self.trivia_timer > 7:
            self.trivia_timer = 0
            self.trivia_index = (self.trivia_index + 1) % len(self.trivia)

    def draw_card(self, surface, card, character, selected):
        accent = theme.HONEY if selected else theme.LAVENDER
        theme.draw_panel(surface, card, accent=accent)

        portrait = pygame.Rect(0, 0, 30, 30)
        portrait.midtop = (card.centerx, card.y + 8)
        pygame.draw.rect(surface, tuple(character["color"]), portrait)
        pygame.draw.rect(surface, theme.CREAM, portrait, 1)

        theme.draw_text(surface, character["name"], (card.centerx, card.y + 41),
                        "button", theme.CREAM, anchor="midtop")

        ability = character["ability"].replace("_", " ").title()
        theme.draw_text(surface, f"Speed {character['speed']}  HP {character['max_health']}",
                        (card.centerx, card.y + 58), self.font, theme.CREAM_DIM, anchor="midtop")
        theme.draw_text(surface, f"Ability: {ability}",
                        (card.centerx, card.y + 68), self.font, theme.HONEY, anchor="midtop")

    def draw(self, surface):
        theme.fill_bg(surface)
        theme.draw_text(surface, "Select Your Character", (160, 5), "heading",
                        theme.HONEY, anchor="midtop")

        for i, card in enumerate(self.cards):
            self.draw_card(surface, card, self.characters[i], i == self.selected)

        theme.draw_text(surface, "A/D: choose   ENTER: confirm   ESC: back",
                        (160, 112), self.font, theme.CREAM_DIM, anchor="midtop")

        panel = pygame.Rect(20, 126, 280, 50)
        theme.draw_panel(surface, panel, title="DID YOU KNOW?")
        lines = wrap_text(self.trivia[self.trivia_index], self.font, 268)[:3]
        for i, line in enumerate(lines):
            theme.draw_text(surface, line, (panel.x + 6, panel.y + 18 + i * 10),
                            self.font, theme.CREAM)