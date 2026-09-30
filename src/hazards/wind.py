import random

import pygame
from src.ui import theme
from src.core import settings


class Wind:
    def __init__(self, config, events):
        self.base_strength = config["strength"]
        self.events = events
        self.state = "calm"          # calm -> warning -> gust -> calm
        self.timer = random.uniform(3, 6)
        self.direction = 1
        self.push = pygame.Vector2(0, 0)
        self.font = pygame.font.Font(None, 14)
        self.streaks = [
            [random.uniform(0, settings.INTERNAL_WIDTH),
             random.uniform(0, settings.INTERNAL_HEIGHT)]
            for _ in range(14)
        ]

    def update(self, dt, danger):
        self.timer -= dt
        if self.state == "calm" and self.timer <= 0:
            self.state = "warning"
            self.timer = 1.2
            self.direction = random.choice((-1, 1))
            self.events.emit("wind_warning")
        elif self.state == "warning" and self.timer <= 0:
            self.state = "gust"
            self.timer = 2.5
        elif self.state == "gust" and self.timer <= 0:
            self.state = "calm"
            self.timer = max(2.0, random.uniform(4, 8) - danger * 0.03)

        # Higher danger = stronger wind.
        strength = self.base_strength * (0.6 + 0.4 * danger / 100)
        self.push.x = self.direction * strength if self.state == "gust" else 0

        if self.state == "gust":
            for s in self.streaks:
                s[0] = (s[0] + self.direction * 260 * dt) % settings.INTERNAL_WIDTH

    def draw(self, surface):
        if self.state == "warning" and int(self.timer * 6) % 2 == 0:
            arrows = ">>>" if self.direction > 0 else "<<<"
            text = self.font.render(f"WIND {arrows}", False, (255, 255, 120))
            surface.blit(text, text.get_rect(center=(160, 50)))
        elif self.state == "gust":
            for x, y in self.streaks:
                pygame.draw.line(
                    surface, (220, 230, 245), (x, y), (x + self.direction * 10, y)
                )