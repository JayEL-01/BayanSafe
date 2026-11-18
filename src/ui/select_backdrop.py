import math
import random

import pygame

from src.core import settings
from src.ui import theme
from src.ui.backdrop import PHASES, _bake_vignette      # same tints + vignette as the menu
from src.utils.data_loader import BASE_DIR

SIZE = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
MAX_NIGHT_REF = 1.0   # PHASES night value
IMAGE = BASE_DIR / "assets" / "images" / "menu" / "select_bg.png"

# ------------------------------------------------------------------
# EDIT FREELY
# ------------------------------------------------------------------
PHASE_SECONDS = 12      # seconds per morning / day / evening / night (menu uses 5)
START_PHASE = 1         # 0 morning, 1 day, 2 evening, 3 night
INDOOR = True           # True = inside a house. False = the old outdoor plaza
CLOUDS = True           # outdoor only
BIRDS = True            # outdoor only
CLOUD_SPEED = 3         # pixels per second
DEBUG = False           # True draws boxes so you can line the effects up with your picture

# ---- OUTDOOR: glow rects at night (canvas pixels) ----
LIGHTS = [(27, 88, 6, 9), (284, 90, 22, 8)]

# ---- INDOOR: all in canvas pixels (320 x 180). Move these to match YOUR picture. ----
WINDOW = pygame.Rect(250, 34, 40, 46)     # the window opening
BEAM_LENGTH = 70                          # how far the sunbeam slants down-left
BEAM_FLOOR = 150                          # y where the beam ends
LANTERNS = [(48, 44)]                     # centre of each hanging lamp
LAMP_SIZE = (26, 20)                      # glow radius (x, y)


class SelectBackdrop:
    """Plaza picture with the same day/night look as the main menu."""

    def __init__(self, seed=3):
        rng = random.Random(seed)
        if IMAGE.exists():
            img = pygame.image.load(str(IMAGE)).convert()
            if img.get_size() != SIZE:
                img = pygame.transform.scale(img, SIZE)       # nearest, like the menu
            self.bg = img
        else:
            print(f"Missing {IMAGE}. Using a plain sky instead.")
            self.bg = pygame.Surface(SIZE)
            self.bg.fill((90, 170, 230))

        self.t = 0.0
        self.look = 0.0
        self._look_target = 0.0
        self.tint = (255, 255, 255)
        self.night = 0.0
        self.skip = START_PHASE * PHASE_SECONDS
        self._vig = _bake_vignette()
        self.glow = self._make_glow(40, 12)

        self.clouds = [[rng.uniform(0, SIZE[0]), rng.uniform(4, 34), rng.choice((1.0, 1.4, 1.8))]
                       for _ in range(4)]
        self.birds = [[rng.uniform(-SIZE[0], 0), rng.uniform(16, 60), rng.uniform(14, 24),
                       rng.uniform(0, 6.28)] for _ in range(3)]
        self.stars = [(rng.randint(2, 317), rng.randint(2, 44), rng.uniform(0, 6.28))
                      for _ in range(36)]
        self.flies = [(rng.uniform(0, 320), rng.uniform(112, 172),
                       rng.uniform(0, 6.28), rng.uniform(0.4, 1.0)) for _ in range(12)]

        # indoor extras
        self.lamp_glow = self._make_glow(*LAMP_SIZE)
        self.beam = self._make_beam()
        self.dust = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 6.28),
                      rng.uniform(0.15, 0.4)) for _ in range(18)]

    # ---------- helpers ----------
    @staticmethod
    def _make_glow(rx, ry):
        surf = pygame.Surface((rx * 2, ry * 2))
        surf.fill((0, 0, 0))
        steps = 10
        for i in range(steps):
            k = (i + 1) / steps
            rect = pygame.Rect(0, 0, int(rx * 2 * (1 - i / steps)), int(ry * 2 * (1 - i / steps)))
            rect.center = (rx, ry)
            pygame.draw.ellipse(surf, (int(70 * k), int(52 * k), int(18 * k)), rect)
        return surf

    @staticmethod
    def _beam_points():
        w = WINDOW
        return [(w.left, w.top), (w.right, w.top),
                (w.right - BEAM_LENGTH, BEAM_FLOOR), (w.left - BEAM_LENGTH, BEAM_FLOOR)]

    def _make_beam(self):
        """A soft shaft of window light, baked in 5 pixel-art steps (not a smooth gradient)."""
        surf = pygame.Surface(SIZE, pygame.SRCALPHA)
        w = WINDOW
        height = max(1, BEAM_FLOOR - w.top)
        for y in range(w.top, BEAM_FLOOR):
            f = (y - w.top) / height
            shift = int(-BEAM_LENGTH * f)
            strength = round((1 - f * 0.8) * 5) / 5
            pygame.draw.line(surf, (255, 255, 255, int(255 * strength)),
                             (w.left + shift, y), (w.right + shift, y))
        return surf

    def _draw_indoor(self, surface):
        n, t = self.night, self.t
        # sunbeam by day, cold moonlight at night
        color = theme.mix((255, 226, 150), (130, 160, 255), min(1.0, n * 1.6))
        alpha = int(70 * (1 - n * 0.4))
        beam = self.beam.copy()
        beam.fill((*color, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(beam, (0, 0))

        # dust specks floating in the beam
        w = WINDOW
        for u, v, phase, speed in self.dust:
            f = (v + t * speed * 0.05) % 1.0
            y = w.top + f * (BEAM_FLOOR - w.top)
            x = w.left + u * w.width - BEAM_LENGTH * f + math.sin(t * speed * 3 + phase) * 4
            if math.sin(t * 1.5 + phase) > -0.4:
                surface.set_at((int(x), int(y)), (255, 244, 214))

        # lamp glow: faint in the day, strong at night, with a gentle flicker
        for lx, ly in LANTERNS:
            flicker = 0.9 + 0.1 * math.sin(t * 9 + lx) * math.sin(t * 2.3 + ly)
            power = (0.3 + 0.7 * n / MAX_NIGHT_REF) * flicker
            g = self.lamp_glow.copy()
            g.fill((int(255 * min(1.0, power)),) * 3, special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(g, g.get_rect(center=(lx, ly)), special_flags=pygame.BLEND_RGB_ADD)

    def look_at(self, canvas_x):
        """Mouse x in canvas pixels, for a small parallax shift of the clouds."""
        self._look_target = max(-1.0, min(1.0, (canvas_x - SIZE[0] / 2) / (SIZE[0] / 2)))

    def _state(self):
        cycle = PHASE_SECONDS * len(PHASES)
        total = (self.t + self.skip) % cycle
        i = int(total // PHASE_SECONDS)
        frac = (total % PHASE_SECONDS) / PHASE_SECONDS
        blend = round(max(0.0, (frac - 0.5) * 2) * 6) / 6
        a, b = PHASES[i], PHASES[(i + 1) % len(PHASES)]
        tint = tuple(int(a[1][k] + (b[1][k] - a[1][k]) * blend) for k in range(3))
        return tint, a[2] + (b[2] - a[2]) * blend

    def update(self, dt):
        self.t += dt
        self.look += (self._look_target - self.look) * 0.08
        for c in self.clouds:
            c[0] += CLOUD_SPEED * dt * c[2] * 0.6
            if c[0] > SIZE[0] + 30:
                c[0] = -30
        for b in self.birds:
            b[0] += b[2] * dt
            if b[0] > SIZE[0] + 10:
                b[0] = random.uniform(-120, -10)
                b[1] = random.uniform(16, 60)
        self.tint, self.night = self._state()

    def _cloud(self, surface, x, y, s):
        x, y = int(x - self.look * 2), int(y)
        pygame.draw.rect(surface, (255, 255, 255), (x, y + int(4 * s), int(18 * s), int(4 * s)))
        pygame.draw.rect(surface, (255, 255, 255), (x + int(3 * s), y + int(1 * s), int(10 * s), int(5 * s)))
        pygame.draw.rect(surface, (255, 255, 255), (x + int(8 * s), y - int(1 * s), int(6 * s), int(4 * s)))
        pygame.draw.line(surface, (196, 220, 242), (x + 1, y + int(8 * s)), (x + int(18 * s) - 2, y + int(8 * s)))

    def _night_extras(self, surface):
        night, t = self.night, self.t
        if night < 0.05 or INDOOR:
            return
        glow = int(110 * night)
        for rect in LIGHTS:
            surface.fill((glow, int(glow * 0.7), int(glow * 0.2)), rect,
                         special_flags=pygame.BLEND_RGB_ADD)
        if night > 0.4:
            for x, y, phase in self.stars:
                if math.sin(t * 2 + phase) > -0.3:
                    surface.set_at((x, y), theme.CREAM)
        if night > 0.6:
            cx, cy = 298, 14
            for dy in range(-7, 8):
                for dx in range(-7, 8):
                    if dx * dx + dy * dy <= 36 and (dx - 3) ** 2 + (dy + 2) ** 2 > 30:
                        surface.set_at((cx + dx, cy + dy), theme.CREAM)
        if night > 0.3:
            for x, y, phase, speed in self.flies:
                fx = x + math.sin(t * speed + phase) * 10
                fy = y + math.sin(t * speed * 1.7 + phase) * 5
                if math.sin(t * 3 + phase) > -0.2:
                    surface.fill((40, 36, 10), (int(fx) - 1, int(fy) - 1, 4, 4),
                                 special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.rect(surface, (255, 235, 120), (int(fx), int(fy), 2, 2))

    def draw(self, surface, glow_pos=None):
        surface.blit(self.bg, (0, 0))

        if CLOUDS and not INDOOR:
            for x, y, s in self.clouds:
                self._cloud(surface, x, y, s)
        if BIRDS and not INDOOR:
            for x, y, _, phase in self.birds:
                f = 2 if int(self.t * 6 + phase) % 2 else 0
                by = int(y + math.sin(self.t * 1.5 + phase) * 2)
                pygame.draw.line(surface, (30, 40, 50), (int(x) - 3, by - 1 + f), (int(x), by))
                pygame.draw.line(surface, (30, 40, 50), (int(x), by), (int(x) + 3, by - 1 + f))

        surface.fill(self.tint, special_flags=pygame.BLEND_RGB_MULT)   # morning/day/evening/night
        self._night_extras(surface)
        if INDOOR:
            self._draw_indoor(surface)

        if glow_pos:                                                    # spotlight on the selected hero
            pulse = 0.85 + 0.15 * math.sin(self.t * 3)
            g = self.glow
            if pulse < 1:
                g = g.copy()
                g.fill((int(255 * pulse),) * 3, special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(g, g.get_rect(center=glow_pos), special_flags=pygame.BLEND_RGB_ADD)

        if DEBUG and INDOOR:
            pygame.draw.rect(surface, (255, 60, 60), WINDOW, 1)
            pygame.draw.lines(surface, (255, 200, 60), True, self._beam_points(), 1)
            for lx, ly in LANTERNS:
                pygame.draw.circle(surface, (60, 255, 60), (lx, ly), 3, 1)

        self._vig.set_alpha(int(255 * min(1.0, 0.6 + 0.3 * self.night)))
        surface.blit(self._vig, (0, 0))                                 # darker edges, like the menu