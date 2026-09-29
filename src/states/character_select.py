import random

import pygame

from src.states.base_state import BaseState
from src.states.world_map import WorldMap
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

        self.title_font = pygame.font.Font(None, 22)
        self.name_font = pygame.font.Font(None, 18)
        self.small = pygame.font.Font(None, 12)

        self.selected = 0
        self.cards = [pygame.Rect(50, 26, 100, 84), pygame.Rect(170, 26, 100, 84)]

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
        fill = (50, 75, 130) if selected else (30, 45, 90)
        border = (255, 220, 80) if selected else (90, 110, 170)
        pygame.draw.rect(surface, fill, card)
        pygame.draw.rect(surface, border, card, 2 if selected else 1)

        # Placeholder portrait (replace with portrait.png later)
        portrait = pygame.Rect(0, 0, 30, 30)
        portrait.midtop = (card.centerx, card.y + 8)
        pygame.draw.rect(surface, tuple(character["color"]), portrait)
        pygame.draw.rect(surface, (255, 255, 255), portrait, 1)

        name = self.name_font.render(character["name"].upper(), False, (255, 255, 255))
        surface.blit(name, name.get_rect(center=(card.centerx, card.y + 48)))

        ability = character["ability"].replace("_", " ").upper()
        lines = [
            f"SPEED {character['speed']}   HP {character['max_health']}",
            f"ABILITY: {ability}",
        ]
        for i, line in enumerate(lines):
            text = self.small.render(line, False, (190, 205, 240))
            surface.blit(text, text.get_rect(center=(card.centerx, card.y + 62 + i * 10)))

    def draw(self, surface):
        surface.fill((15, 25, 55))

        title = self.title_font.render("SELECT YOUR CHARACTER", False, (255, 200, 60))
        surface.blit(title, title.get_rect(center=(160, 13)))

        for i, card in enumerate(self.cards):
            self.draw_card(surface, card, self.characters[i], i == self.selected)

        hint = self.small.render(
            "A/D or arrows: choose   ENTER: confirm   ESC: back", False, (150, 170, 210)
        )
        surface.blit(hint, hint.get_rect(center=(160, 118)))

        # Trivia panel
        panel = pygame.Rect(20, 128, 280, 46)
        pygame.draw.rect(surface, (20, 35, 70), panel)
        pygame.draw.rect(surface, (255, 200, 60), panel, 1)
        label = self.small.render("DID YOU KNOW?", False, (255, 200, 60))
        surface.blit(label, (panel.x + 6, panel.y + 4))
        for i, line in enumerate(wrap_text(self.trivia[self.trivia_index], self.small, 268)[:3]):
            text = self.small.render(line, False, (255, 255, 255))
            surface.blit(text, (panel.x + 6, panel.y + 15 + i * 10))