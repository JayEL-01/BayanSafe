"""Flash Flood and Severe Flooding Hazard Handlers.

Models rapid inundation, water level escalation, current drag,
and safe high ground clearance.
"""

import math
import pygame
from src.hazards.base_hazard import BaseHazard
from src.config.palette import COLOR_HAZARD_FLOOD


class FlashFloodHazard(BaseHazard):
    def __init__(self, rise_speed: float = 3.5, max_height: float = 90.0):
        super().__init__("Flash Flood Warning", danger_level=4)
        self.water_level: float = 10.0
        self.rise_speed: float = rise_speed
        self.max_height: float = max_height
        self.current_push = pygame.Vector2(-15.0, 0.0)

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        if self.water_level < self.max_height:
            self.water_level += self.rise_speed * dt

    def is_submerged(self, world_y: float) -> bool:
        """Check if a world Y coordinate is under floodwater."""
        # Water rises from bottom up or from river coordinates
        return world_y >= (360 - self.water_level)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        w, h = surface.get_size()
        # Rising floodwater rectangle at screen bottom
        water_h = min(h, int(self.water_level * (h / 360.0)))
        if water_h > 0:
            flood_surf = pygame.Surface((w, water_h), pygame.SRCALPHA)
            flood_surf.fill((*COLOR_HAZARD_FLOOD, 180))
            surface.blit(flood_surf, (0, h - water_h))
            # Crest ripple line
            ripple_y = h - water_h
            for x in range(0, w, 8):
                offset_y = int(math.sin(self.timer * 6.0 + x * 0.1) * 2)
                pygame.draw.line(surface, (140, 200, 255), (x, ripple_y + offset_y), (x + 6, ripple_y + offset_y), 1)


class SevereFloodingHazard(BaseHazard):
    def __init__(self):
        super().__init__("Severe Flooding (Red Rainfall Warning)", danger_level=5)
        self.current_flow_rate = 25.0

    def draw_effects(self, surface: pygame.Surface, camera=None):
        w, h = surface.get_size()
        # Deep murky blue tint across bottom half
        submerged_surf = pygame.Surface((w, int(h * 0.65)), pygame.SRCALPHA)
        submerged_surf.fill((*COLOR_HAZARD_FLOOD, 195))
        surface.blit(submerged_surf, (0, int(h * 0.35)))
        # Flow vectors
        for i in range(8):
            lx = int((self.timer * 40 + i * 45) % w)
            ly = int(h * 0.45 + (i * 14) % int(h * 0.4))
            pygame.draw.line(surface, (200, 230, 255, 160), (lx, ly), (lx + 14, ly), 1)
