"""Typhoon Hazard Handler.

Simulates PAGASA Tropical Cyclone Wind Signal (TCWS 1 to 5),
heavy rain line rendering, wind push vector on player, and flying debris.
"""

import math
import random
import pygame
from src.hazards.base_hazard import BaseHazard


class TyphoonHazard(BaseHazard):
    def __init__(self, tcws_level: int = 2):
        super().__init__(f"Typhoon (TCWS #{tcws_level})", danger_level=tcws_level)
        self.tcws_level = tcws_level
        self.wind_speed = 30 + tcws_level * 20  # km/h equivalent force
        self.wind_dir = pygame.Vector2(-1.0, 0.4).normalize()
        self.rain_particles = [
            (random.randint(0, 320), random.randint(0, 180), random.randint(4, 10))
            for _ in range(40 + tcws_level * 15)
        ]

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        # Update rain particles
        w, h = 320, 180
        speed = 220 + self.tcws_level * 40
        for i in range(len(self.rain_particles)):
            rx, ry, length = self.rain_particles[i]
            rx += self.wind_dir.x * speed * dt
            ry += self.wind_dir.y * speed * dt
            if rx < 0 or ry > h:
                rx = random.randint(100, w + 100)
                ry = random.randint(-40, -5)
            self.rain_particles[i] = (rx, ry, length)

    def get_wind_push(self) -> pygame.Vector2:
        """Wind resistance against movement."""
        return self.wind_dir * (self.tcws_level * 8.0)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        w, h = surface.get_size()
        # Storm dark tint
        dim_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        dim_surf.fill((15, 25, 35, 70 + self.tcws_level * 20))
        surface.blit(dim_surf, (0, 0))

        # Rain streaks
        rain_color = (180, 205, 230, 180)
        for rx, ry, length in self.rain_particles:
            end_x = rx + self.wind_dir.x * length
            end_y = ry + self.wind_dir.y * length
            pygame.draw.line(surface, rain_color, (rx, ry), (end_x, end_y), 1)
