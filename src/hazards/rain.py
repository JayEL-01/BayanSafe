import random

import pygame
from src.ui import theme
from src.core import settings


class Rain:
    """Falling drops plus a dark overlay: you only see clearly near yourself."""

    def __init__(self, config):
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        self.drops = [
            [random.uniform(0, w), random.uniform(0, h), random.uniform(120, 200)]
            for _ in range(config["drops"])
        ]
        self.slant = 0.0

    def update(self, dt, wind_x):
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        self.slant = wind_x * 0.6
        for d in self.drops:
            d[1] += d[2] * dt
            d[0] = (d[0] + self.slant * dt) % w
            if d[1] > h:
                d[1] = -5
                d[0] = random.uniform(0, w)

    def draw(self, surface, player_screen_pos):
        # Dark layer with a see-through hole around the player.
        overlay = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((8, 12, 30, 130))
        for radius, alpha in [(80, 110), (65, 80), (50, 45), (38, 15), (30, 0)]:
            pygame.draw.circle(overlay, (8, 12, 30, alpha), player_screen_pos, radius)
        surface.blit(overlay, (0, 0))

        for x, y, _ in self.drops:
            pygame.draw.line(
                surface, (150, 180, 230), (x, y), (x + self.slant * 0.05, y + 4)
            )