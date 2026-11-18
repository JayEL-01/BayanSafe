import math

import pygame

from src.core import settings
from src.ui import theme
from src.utils.data_loader import BASE_DIR

SIZE = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
MENU_DIR = BASE_DIR / "assets" / "images" / "ui"


class ImageBackdrop:
    """A picture background with a 'flashlight' look: the screen is dark and a warm
    circle of light follows the selected button (like looking inside a go-bag at night).

    ImageBackdrop("options_bg.png")  -> falls back to the old CozyBackdrop if the file is missing.
    Use .look_at_y(y) every frame (or when the selection changes) to aim the light.
    """

    DARKNESS = 150          # 0 = no darkness, 255 = pitch black outside the light
    RADIUS = 88             # light radius in canvas pixels
    SPEED = 8.0             # how fast the light follows the selection

    def __init__(self, filename, light_pos=None):
        path = MENU_DIR / filename
        self.fallback = None
        self.image = None
        if path.exists():
            img = pygame.image.load(str(path)).convert()
            self.image = img if img.get_size() == SIZE else pygame.transform.scale(img, SIZE)
        else:
            print(f"Missing {path}. Using the old backdrop instead.")
            self.fallback = theme.CozyBackdrop()

        self.light = list(light_pos or (SIZE[0] / 2, SIZE[1] / 2))
        self.target = tuple(self.light)
        self.t = 0.0
        self.dark = pygame.Surface(SIZE, pygame.SRCALPHA)
        # a few slightly different light sizes, so the flicker costs nothing at runtime
        self.holes = [self._make_hole(self.RADIUS + d) for d in (-3, -1, 0, 1, 3)]
        self.warm = self._make_warm(self.RADIUS)

    # ---------- baking ----------
    def _make_hole(self, r):
        """Alpha mask: 0 in the middle (lit) rising to DARKNESS at the edge, in pixel-art steps."""
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        s.fill((255, 255, 255, self.DARKNESS))
        for y in range(r * 2):
            for x in range(r * 2):
                d = math.hypot(x - r, y - r) / r
                if d < 1:
                    v = round(min(1.0, d ** 1.4) * 6) / 6
                    s.set_at((x, y), (255, 255, 255, int(self.DARKNESS * v)))
        return s

    def _make_warm(self, r):
        """A faint warm tint inside the light (pixel-art steps)."""
        s = pygame.Surface((r * 2, r * 2))
        s.fill((0, 0, 0))
        for y in range(r * 2):
            for x in range(r * 2):
                d = math.hypot(x - r, y - r) / r
                if d < 1:
                    v = round((1 - d) * 4) / 4
                    s.set_at((x, y), (int(26 * v), int(16 * v), int(4 * v)))
        return s

    # ---------- use ----------
    def aim(self, x, y):
        """Where the light should go (canvas pixels)."""
        self.target = (x, y)

    def draw(self, surface, t=0.0):
        if self.fallback:
            self.fallback.draw(surface, t)
            theme.dim(surface, 110)
            return
        dt = max(0.0, min(0.1, t - self.t)) if self.t else 0.0
        self.t = t
        k = min(1.0, dt * self.SPEED)
        self.light[0] += (self.target[0] - self.light[0]) * k
        self.light[1] += (self.target[1] - self.light[1]) * k

        surface.blit(self.image, (0, 0))

        # flicker: pick one of the light sizes
        flick = math.sin(t * 7.3) * 0.5 + math.sin(t * 17.0) * 0.3 + math.sin(t * 3.1) * 0.2
        hole = self.holes[max(0, min(len(self.holes) - 1, int((flick + 1) / 2 * len(self.holes))))]
        pos = (int(self.light[0]), int(self.light[1]))

        self.dark.fill((8, 6, 14, self.DARKNESS))
        self.dark.blit(hole, hole.get_rect(center=pos), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(self.dark, (0, 0))
        surface.blit(self.warm, self.warm.get_rect(center=pos), special_flags=pygame.BLEND_RGB_ADD)