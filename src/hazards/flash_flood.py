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

    # Read-only aliases: older missions probe several names for the current
    # water height. Keeping them here avoids per-level fallbacks.
    @property
    def water_height(self) -> float:
        return self.water_level

    @property
    def height(self) -> float:
        return self.water_level

    def update(self, dt: float, player_pos: pygame.Vector2, block_map=None):
        super().update(dt, player_pos, block_map)
        if self.water_level < self.max_height:
            self.water_level += self.rise_speed * dt

    def get_speed_scale(self, player_rect=None) -> float:
        """Deep water slows movement; shallow edges do not."""
        if player_rect is None:
            return 1.0
        deep = 360 - self.water_level * 0.55
        return 0.65 if getattr(player_rect, "centery", 0) >= deep else 1.0

    def get_water_rect(self):
        """World-space rect of the flooded band rising from the south."""
        top = max(0, 360 - self.water_level)
        return pygame.Rect(0, top, 640, 360 - top)

    def is_submerged(self, world_y: float) -> bool:
        """Check if a world Y coordinate is under floodwater."""
        # Water rises from bottom up or from river coordinates
        return world_y >= (360 - self.water_level)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        """Wavy, banded floodwater rising from the south (pixel shoreline)."""
        w, h = surface.get_size()
        water_h = min(h, int(self.water_level * (h / 360.0)))
        if water_h <= 0:
            return
        top = h - water_h
        layer = pygame.Surface((w, water_h), pygame.SRCALPHA)
        base = COLOR_HAZARD_FLOOD

        # Body with shallow/deep bands and a jagged 2px pixel shoreline.
        for x in range(w):
            wave = int(round(math.sin(x * 0.055 + self.timer * 2.4) * 2.2
                             + math.sin(x * 0.017 - self.timer * 1.3) * 1.3))
            shore = max(0, min(water_h - 1, 4 + wave))
            pygame.draw.rect(layer, (*base, 175), (x, shore, 1, water_h - shore))
            if (x // 4) % 2 == 0:
                pygame.draw.rect(layer, (200, 232, 255, 180), (x, shore, 2, 1))

        for dy in range(6, water_h, 8):
            depth = min(90, int((dy / max(1, water_h)) * 90))
            pygame.draw.rect(layer, (14, 34, 78, depth), (0, dy, w, 4))

        # Drifting surface highlights and expanding ripple rings.
        for row, y in enumerate(range(8, water_h, 14)):
            start = (row * 11 + int(self.timer * 12)) % 26
            for x in range(start - 26, w, 26):
                pygame.draw.rect(layer, (175, 215, 245, 150), (x, y, 9, 1))
        for cx in range(48, w, 112):
            phase = (self.timer * 0.8 + cx / 112.0) % 1.0
            rx = int(4 + phase * 12)
            if 0 <= top + 10 < h:
                pygame.draw.ellipse(
                    layer, (190, 230, 255, int((1 - phase) * 110)),
                    pygame.Rect(cx - rx, 10 - rx // 3, rx * 2, max(2, rx // 2)), 1,
                )

        surface.blit(layer, (0, top))


class SevereFloodingHazard(BaseHazard):
    """Pixel-style floodwater drawn in world space.

    shallow_rects: low ground covered by ankle-deep water
    deep_rects:    the dangerous deep channels (darker, more opaque)
    """

    CELL_W, CELL_H = 16, 8  # ripple grid size (world pixels)

    def __init__(self, shallow_rects=None, deep_rects=None, rain: bool = True):
        super().__init__("Severe Flooding (Red Rainfall Warning)", danger_level=5)
        self.current_flow_rate = 25.0
        self.shallow_rects = [pygame.Rect(r) for r in (shallow_rects or [])]
        self.deep_rects = [pygame.Rect(r) for r in (deep_rects or [])]
        self.rain = rain

        base = COLOR_HAZARD_FLOOD
        self.c_deep = tuple(int(c * 0.65) for c in base)
        self.c_shallow = base
        self.c_glint = tuple(min(255, int(c + (255 - c) * 0.45)) for c in base)
        self.c_foam = tuple(min(255, int(c + (255 - c) * 0.75)) for c in base)

    # --- helpers -----------------------------------------------------
    @staticmethod
    def _offset(rect, camera):
        """World -> screen offset using the camera (no camera = no offset)."""
        if camera is None:
            return 0, 0
        sr = camera.apply(rect)
        return sr.x - rect.x, sr.y - rect.y

    @staticmethod
    def _hash(cx, cy):
        return ((cx * 73856093) ^ (cy * 19349663)) & 0xFFFF

    def _draw_pool(self, surface, camera, rect, color, alpha, deep=False):
        ox, oy = self._offset(rect, camera)
        sr = rect.move(ox, oy)
        vis = sr.clip(surface.get_rect())
        if vis.w <= 0 or vis.h <= 0:
            return
        t = self.timer

        # 1. translucent water body (single flat tone = pixel-art look)
        body = pygame.Surface(vis.size, pygame.SRCALPHA)
        body.fill((*color, alpha))
        surface.blit(body, vis.topleft)

        # 2. ripples: fixed grid in WORLD space so they scroll with the map
        wx0, wy0 = vis.x - ox, vis.y - oy
        for cy in range(wy0 // self.CELL_H, (wy0 + vis.h) // self.CELL_H + 1):
            for cx in range(wx0 // self.CELL_W, (wx0 + vis.w) // self.CELL_W + 1):
                h = self._hash(cx, cy)
                if h % 4:                      # only ~1 in 4 cells has a ripple
                    continue
                phase = (t * 0.7 + (h % 100) / 100.0) % 1.0
                if phase > 0.8:
                    continue
                x = cx * self.CELL_W + (h >> 3) % self.CELL_W + ox
                y = cy * self.CELL_H + (h >> 6) % self.CELL_H + oy
                half = 1 + int(phase * 4)      # ripple grows, then vanishes
                col = self.c_glint if phase < 0.5 else color
                if deep:
                    col = self.c_shallow if phase < 0.5 else self.c_deep
                if vis.left <= x - half and x + half <= vis.right and vis.top <= y < vis.bottom - 1:
                    pygame.draw.line(surface, col, (x - half, y), (x + half, y))
                    pygame.draw.line(surface, col, (x - half + 1, y + 1), (x + half - 1, y + 1))

        # 3. wavy foam edge on the top shoreline with a dithered fade
        for x in range(vis.left, vis.right, 2):
            wave = int(math.sin(t * 2.0 + (x - ox) * 0.15) * 1.2)
            y = sr.top + wave
            if vis.top <= y < vis.bottom:
                surface.set_at((x, y), self.c_foam)
                if x + 1 < vis.right:
                    surface.set_at((x + 1, y), self.c_foam)
            y2 = y + 1
            if vis.top <= y2 < vis.bottom and (x // 2) % 2 == 0:
                surface.set_at((x, y2), self.c_glint)   # checker dither

    # --- drawing -----------------------------------------------------
    def draw_under(self, surface: pygame.Surface, camera=None):
        """Call BEFORE NPCs/player so characters appear to wade in the water."""
        for r in self.shallow_rects:
            self._draw_pool(surface, camera, r, self.c_shallow, 95)
        for r in self.deep_rects:
            self._draw_pool(surface, camera, r, self.c_deep, 150, deep=True)

    def draw_effects(self, surface: pygame.Surface, camera=None):
        """Rain only; drawn on top of everything."""
        if not self.rain:
            return
        w, h = surface.get_size()
        t = self.timer
        for i in range(28):
            x = int((i * 37 + t * 35) % w)
            y = int((i * 53 + t * 150) % h)
            pygame.draw.line(surface, self.c_glint, (x, y), (x - 1, y + 2))