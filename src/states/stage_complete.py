import random

import pygame
from src.ui import theme
from src.states.base_state import BaseState
from src.ui.button import Button
from src.utils.helpers import wrap_text


class StageComplete(BaseState):
    def __init__(self, game, stats, on_replay):
        super().__init__(game)
        self.stats = stats
        self.title_font = pygame.font.Font(None, 26)
        self.font = pygame.font.Font(None, 12)
        self.button_font = pygame.font.Font(None, 16)
        lessons = stats["lessons"]
        self.lesson = random.choice(lessons) if lessons else ""

        self.selected = 0
        self.buttons = [
            Button("CONTINUE", (40, 158, 110, 18), self.go_to_map, self.button_font),
            Button("REPLAY", (170, 158, 110, 18), on_replay, self.button_font),
        ]
        self.update_selection()

    def go_to_map(self):
        self.game.state_manager.pop()   # this screen
        self.game.state_manager.pop()   # the stage

    def update_selection(self):
        for i, b in enumerate(self.buttons):
            b.selected = (i == self.selected)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.buttons)
                self.update_selection()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected].activate()
            elif event.key == pygame.K_ESCAPE:
                self.go_to_map()
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

    def panel(self, surface, rect, label):
        pygame.draw.rect(surface, (20, 35, 70), rect)
        pygame.draw.rect(surface, (255, 200, 60), rect, 1)
        surface.blit(self.font.render(label, False, (255, 200, 60)), (rect.x + 6, rect.y + 4))

    def draw(self, surface):
        surface.fill((15, 25, 55))
        s = self.stats

        title = self.title_font.render("STAGE COMPLETE!", False, (110, 230, 130))
        surface.blit(title, title.get_rect(center=(160, 12)))

        # Stats
        left = pygame.Rect(10, 24, 146, 88)
        self.panel(surface, left, "RESULTS")
        minutes, seconds = divmod(int(s["time"]), 60)
        rows = [
            ("TIME", f"{minutes}:{seconds:02d}"),
            ("DAMAGE TAKEN", str(s["damage"])),
            ("ITEMS", f"{s['items_found']}/{s['items_total']}"),
            ("QUESTS", f"{s['quests_done']}/{s['quests_total']}"),
            ("SCORE", str(s["score"])),
        ]
        for i, (name, value) in enumerate(rows):
            y = left.y + 17 + i * 11
            surface.blit(self.font.render(name, False, (190, 205, 240)), (left.x + 6, y))
            val = self.font.render(value, False, (255, 255, 255))
            surface.blit(val, (left.right - val.get_width() - 6, y))
        if s["perfect"]:
            perfect = self.font.render("PERFECT COMPLETION!", False, (255, 220, 80))
            surface.blit(perfect, perfect.get_rect(center=(left.centerx, left.bottom - 8)))

        # Cause and effect
        right = pygame.Rect(164, 24, 146, 88)
        self.panel(surface, right, "CAUSE & EFFECT")
        text = " ".join(s["consequences"]) or "You made no big choices this time."
        for i, line in enumerate(wrap_text(text, self.font, right.w - 12)[:7]):
            surface.blit(self.font.render(line, False, (255, 255, 255)),
                         (right.x + 6, right.y + 16 + i * 10))

        # Lesson
        lesson = pygame.Rect(10, 116, 300, 38)
        self.panel(surface, lesson, "LESSON LEARNED")
        for i, line in enumerate(wrap_text(self.lesson, self.font, lesson.w - 12)[:2]):
            surface.blit(self.font.render(line, False, (255, 255, 255)),
                         (lesson.x + 6, lesson.y + 15 + i * 10))

        for b in self.buttons:
            b.draw(surface)