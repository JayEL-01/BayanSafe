"""Landslide, Tsunami, Flash Fire, and Volcanic Eruption Hazard Handlers."""

import math
import random
from typing import List, Tuple
import pygame
from src.hazards.base_hazard import BaseHazard
from src.config.palette import (
    COLOR_HAZARD_LANDSLIDE,
    COLOR_HAZARD_TSUNAMI,
    COLOR_HAZARD_FIRE,
    COLOR_HAZARD_ASH,
)


class LandslideHazard(BaseHazard):
    def __init__(self):
        super().__init__("Rain-Induced Landslide Warning", danger_level=4)
        self.debris_spread = 0.0

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        if self.debris_spread < 60.0:
            self.debris_spread += 8.0 * dt

    def draw_effects(self, surface: pygame.Surface, camera=None):
        # Mud splatter particles
        w, h = surface.get_size()
        for i in range(12):
            mx = (int(self.timer * 35) + i * 28) % w
            my = int(h * 0.75 + math.sin(i * 1.5) * 15)
            pygame.draw.rect(surface, COLOR_HAZARD_LANDSLIDE, (mx, my, 4, 3))


class TsunamiHazard(BaseHazard):
    def __init__(self):
        super().__init__("Tsunami Warning (Inundation Threat)", danger_level=5)
        self.phase = "retreat"  # retreat -> surge
        self.sea_level_offset = 0.0

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        if self.timer < 8.0:
            self.phase = "retreat"
            self.sea_level_offset = -math.sin(self.timer / 8.0 * math.pi * 0.5) * 30.0
        else:
            self.phase = "surge"
            surge_time = self.timer - 8.0
            self.sea_level_offset = min(120.0, surge_time * 16.0)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        w, h = surface.get_size()
        if self.phase == "surge" and self.sea_level_offset > 0:
            surge_w = min(w, int(self.sea_level_offset * (w / 120.0)))
            surge_surf = pygame.Surface((surge_w, h), pygame.SRCALPHA)
            surge_surf.fill((*COLOR_HAZARD_TSUNAMI, 190))
            surface.blit(surge_surf, (0, 0))
            # Foaming wave crest
            for y in range(0, h, 6):
                crest_x = surge_w - 4 + int(math.sin(self.timer * 8.0 + y * 0.2) * 3)
                pygame.draw.line(surface, (255, 255, 255), (crest_x, y), (crest_x + 3, y), 2)


class FlashFireHazard(BaseHazard):
    def __init__(self):
        super().__init__("Flash Fire Outbreak", danger_level=4)
        self.smoke_particles = [
            (random.randint(0, 320), random.randint(0, 180), random.randint(8, 20))
            for _ in range(25)
        ]

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        for i in range(len(self.smoke_particles)):
            sx, sy, size = self.smoke_particles[i]
            sy -= 20.0 * dt
            if sy < -10:
                sy = 190
                sx = random.randint(0, 320)
            self.smoke_particles[i] = (sx, sy, size)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        w, h = surface.get_size()
        # Heat haze glow
        heat_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        glow_pulse = int(25 + 15 * math.sin(self.timer * 5.0))
        heat_surf.fill((230, 80, 20, glow_pulse))
        surface.blit(heat_surf, (0, 0))

        # Smoke clouds
        for sx, sy, size in self.smoke_particles:
            smoke = pygame.Surface((size, size), pygame.SRCALPHA)
            smoke.fill((40, 35, 35, 90))
            surface.blit(smoke, (sx, sy))


class VolcanicEruptionHazard(BaseHazard):
    def __init__(self):
        super().__init__("Volcanic Eruption (Alert Level 4)", danger_level=5)
        self.ash_particles = [
            (random.randint(0, 320), random.randint(-40, 180), random.randint(2, 4))
            for _ in range(50)
        ]

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        w, h = 320, 180
        for i in range(len(self.ash_particles)):
            ax, ay, size = self.ash_particles[i]
            ay += 35.0 * dt
            ax += math.sin(self.timer + i) * 10.0 * dt
            if ay > h:
                ay = random.randint(-20, -5)
                ax = random.randint(0, w)
            self.ash_particles[i] = (ax, ay, size)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        w, h = surface.get_size()
        # Gray ash overcast
        ash_sky = pygame.Surface((w, h), pygame.SRCALPHA)
        ash_sky.fill((*COLOR_HAZARD_ASH, 110))
        surface.blit(ash_sky, (0, 0))

        # Falling ash flakes
        for ax, ay, size in self.ash_particles:
            pygame.draw.rect(surface, (215, 215, 220), (ax, ay, size, size))
