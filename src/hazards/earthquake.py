"""Earthquake Hazard Handler.

Simulates tectonic ground shaking (PEIS Intensity scale), screen shake
offset, falling structural debris, and Duck-Cover-Hold prompts.
"""

import math
import random
from typing import Tuple, List
import pygame
from src.hazards.base_hazard import BaseHazard


class EarthquakeHazard(BaseHazard):
    def __init__(self, intensity: int = 6):
        super().__init__(f"Earthquake (PEIS Intensity {intensity})", danger_level=intensity)
        self.intensity = intensity
        self.shaking = True
        self.shake_duration = 12.0
        self.shake_amplitude = intensity * 0.9
        self.falling_debris: List[pygame.Rect] = []

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        if self.timer < self.shake_duration:
            # Active tremor
            decay = max(0.2, 1.0 - (self.timer / self.shake_duration))
            amp = self.shake_amplitude * decay
            sx = int(math.sin(self.timer * 28.0) * amp + random.uniform(-1, 1))
            sy = int(math.cos(self.timer * 24.0) * amp + random.uniform(-1, 1))
            self.screen_shake = (sx, sy)

            # Spawn falling debris occasionally
            if random.random() < (0.05 * self.intensity):
                debris_x = random.randint(20, 300)
                self.falling_debris.append(pygame.Rect(debris_x, 0, 6, 6))
        else:
            self.screen_shake = (0, 0)
            self.shaking = False

        # Update falling debris
        surviving = []
        for d in self.falling_debris:
            d.y += int(110 * dt)
            if d.y < 180:
                surviving.append(d)
        self.falling_debris = surviving

    def draw_effects(self, surface: pygame.Surface, camera=None):
        # Draw falling debris blocks (plain gray/brown pixel blocks)
        for d in self.falling_debris:
            pygame.draw.rect(surface, (140, 110, 80), d)
            pygame.draw.rect(surface, (60, 45, 30), d, 1)
