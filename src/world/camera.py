import pygame

from src.core import settings


class Camera:
    """Follows a target and stays inside the map edges."""

    def __init__(self, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height
        self.offset = pygame.Vector2(0, 0)

    def follow(self, target_rect):
        # Center the target on screen...
        x = target_rect.centerx - settings.INTERNAL_WIDTH // 2
        y = target_rect.centery - settings.INTERNAL_HEIGHT // 2

        # ...but never show anything outside the map.
        x = max(0, min(x, self.map_width - settings.INTERNAL_WIDTH))
        y = max(0, min(y, self.map_height - settings.INTERNAL_HEIGHT))
        self.offset.update(x, y)

    def apply(self, rect):
        """Convert a world rect into a screen rect."""
        return rect.move(-int(self.offset.x), -int(self.offset.y))