"""Base Hazard Class for BayanSafe.

Defines the common interface for environmental hazards (weather, flooding,
geological events, fire) including update logic, screen effects, danger rating,
and rendering.
"""

from typing import Tuple, Dict, Any, Optional
import pygame


class BaseHazard:
    def __init__(self, name: str, danger_level: int = 1):
        self.name = name
        self.danger_level = danger_level  # 1 to 5 scale
        self.active = True
        self.timer = 0.0
        self.screen_shake = (0, 0)
        self.damage_per_second = 0.0

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        self.timer += dt

    def get_screen_shake(self) -> Tuple[int, int]:
        return self.screen_shake

    def draw_effects(self, surface: pygame.Surface, camera=None):
        """Draw overlay effects (rain lines, ash flakes, screen tint, smoke)."""
        pass

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "danger_level": self.danger_level,
            "active": self.active,
        }
