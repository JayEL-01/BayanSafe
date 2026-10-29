import pygame

from src.core import settings


class Camera:
    """Follows the player with a slightly closer-than-map view."""

    def __init__(self, map_width, map_height, zoom=1.0, viewport=None):
        self.map_width = map_width
        self.map_height = map_height
        self.offset = pygame.Vector2(0, 0)
        self.zoom = zoom
        self.viewport = pygame.Rect(viewport or (0, 0, settings.INTERNAL_WIDTH,
                                                  settings.INTERNAL_HEIGHT))

    @property
    def view_width(self):
        return self.viewport.w / self.zoom

    @property
    def view_height(self):
        return self.viewport.h / self.zoom

    def follow(self, target_rect):
        # Center the target on screen...
        x = target_rect.centerx - self.view_width / 2
        y = target_rect.centery - self.view_height / 2

        # ...but never show anything outside the map.
        x = max(0, min(x, self.map_width - self.view_width))
        y = max(0, min(y, self.map_height - self.view_height))
        self.offset.update(x, y)

    def apply(self, rect):
        """Convert and scale a world rectangle into screen coordinates."""
        left = self.viewport.x + round(rect.left * self.zoom) - round(self.offset.x * self.zoom)
        top = self.viewport.y + round(rect.top * self.zoom) - round(self.offset.y * self.zoom)
        right = self.viewport.x + round(rect.right * self.zoom) - round(self.offset.x * self.zoom)
        bottom = self.viewport.y + round(rect.bottom * self.zoom) - round(self.offset.y * self.zoom)
        return pygame.Rect(
            left, top, max(1, right - left), max(1, bottom - top),
        )

    def visible_world_rect(self):
        return pygame.Rect(round(self.offset.x), round(self.offset.y),
                           round(self.view_width), round(self.view_height))
