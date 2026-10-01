import math
import random

import pygame

from src.core import settings
from src.ui import theme
from src.utils.data_loader import BASE_DIR

MENU_DIR = BASE_DIR / "assets" / "images" / "menu"
MAX_TITLE_WIDTH = 200
SIZE = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)

# ------------------------------------------------------------------
# FILES (in assets/images/menu/, all the same canvas ratio as the scene)
#   bg_clean.png  scene with the palms and grass layer erased
#   trees.png     only the palms, transparent background
#   grass.png     only the foreground grass (optional)
#   clouds.png    only the clouds (optional)
#   title.png     logo
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# MOTION (edit freely)
# ------------------------------------------------------------------
TREE_STRENGTH = 2.5       # sway at the crown, in pixels (1.5 = subtle, 3.5 = strong)
TREE_PERIOD = 8.0         # seconds per full loop (bigger = calmer)
TREE_FRAMES = 40          # more = smoother, uses more RAM at startup
TREE_LAG = 1.2            # delay between trunk and crown (0 = rigid)
FROND_BOB = 1.0           # how much the leaf tips bob up/down
TREE_REGIONS = [(0, 0, 160, 180), (160, 0, 160, 180)]   # one rect per palm

GRASS_STRENGTH = 2.0
GRASS_PERIOD = 4.0
GRASS_FRAMES = 24
GRASS_STRIP = 2           # blade width in pixels
GRASS_WAVELENGTH = 90

CLOUD_SPEED = 3           # pixels per second

# ------------------------------------------------------------------
# DAY / NIGHT
# ------------------------------------------------------------------
PHASE_SECONDS = 10
BLEND_STEPS = 6
START_PHASE = 1           # 0 morning, 1 day, 2 evening, 3 night
PHASES = [
    ("morning", (255, 236, 205), 0.0),
    ("day",     (255, 255, 255), 0.0),
    ("evening", (255, 175, 120), 0.35),
    ("night",   (70, 95, 165),   1.0),
]
LIGHTS = [(24, 116, 6, 12), (232, 130, 10, 4), (250, 130, 10, 4)]   # window glow rects


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def _load(name, alpha=False):
    path = MENU_DIR / name
    if not path.exists():
        return None
    image = pygame.image.load(str(path))
    return image.convert_alpha() if alpha else image.convert()


def _strip_magenta(image, tolerance=60):
    image = image.copy()
    for y in range(image.get_height()):
        for x in range(image.get_width()):
            r, g, b, _ = image.get_at((x, y))
            if r > 255 - tolerance and b > 255 - tolerance and g < tolerance:
                image.set_at((x, y), (0, 0, 0, 0))
    return image


def _load_layer(name):
    """Loads a full-scene layer, scaled to the game size (nearest, stays crisp)."""
    image = _load(name, alpha=True)
    if image is None:
        return None
    return _strip_magenta(pygame.transform.scale(image, SIZE))


def _foot(sprite):
    """Where the plant touches the ground: average x of its lowest opaque pixels."""
    box = sprite.get_bounding_rect()
    if box.h == 0:
        return sprite.get_width() / 2, sprite.get_height()
    xs = [x for y in range(box.bottom - 3, box.bottom) for x in range(box.x, box.right)
          if sprite.get_at((x, y))[3] > 0]
    return (sum(xs) / len(xs) if xs else box.centerx), box.bottom


# ------------------------------------------------------------------
# LAYERS
# ------------------------------------------------------------------
class AliveTree:
    """Baked, looping sway: trunk base stays fixed, crown lags, leaf tips bob."""

    PAD = 8

    def __init__(self, image, region, strength, period, frames, phase=0.0, bob=1.0, lag=1.2):
        self.frames, self.period, self.count = [], period, frames
        self.box = pygame.Rect(0, 0, 0, 0)
        part = image.subsurface(pygame.Rect(region)).copy()
        box = part.get_bounding_rect()
        if box.w == 0 or box.h == 0:
            return
        P = self.PAD
        W, H = box.w + 2 * P, box.h + 2 * P
        src = pygame.Surface((W, H), pygame.SRCALPHA)
        src.blit(part, (P, P), box)

        # palms cut off by the screen edge: repeat the edge column into the padding
        # so the sway never opens a gap at the border
        if region[0] + box.x <= 0:
            col = src.subsurface((P, 0, 1, H)).copy()
            for p in range(P):
                src.blit(col, (p, 0))
        if region[0] + box.right >= SIZE[0]:
            col = src.subsurface((P + box.w - 1, 0, 1, H)).copy()
            for p in range(P):
                src.blit(col, (P + box.w + p, 0))

        self.origin = (region[0] + box.x - P, region[1] + box.y - P)
        self.box = pygame.Rect(self.origin, (W, H))

        anchor, _ = _foot(src)
        half = max(anchor, W - anchor, 1)

        for k in range(frames):
            a = 2 * math.pi * k / frames + phase
            mid = pygame.Surface((W, H), pygame.SRCALPHA)
            for row in range(P, P + box.h):                       # pass 1: bend
                h = 1 - (row - P) / box.h
                w = 0.7 * math.sin(a - lag * h) + 0.3 * math.sin(3 * a - 2 * lag * h + 1.3)
                dx = round(strength * w * h ** 1.8)
                mid.blit(src, (dx, row), (0, row, W, 1))
            out = pygame.Surface((W, H), pygame.SRCALPHA)
            for col in range(0, W, 2):                            # pass 2: leaf bob
                d = min(1.0, abs(col + 1 - anchor) / half)
                dy = round(bob * d ** 1.2 * math.sin(2 * a + col * 0.12))
                out.blit(mid, (col, dy), (col, 0, 2, H))
            self.frames.append(out.convert_alpha())

    def draw(self, surface, t):
        if self.frames:
            i = int(t / self.period * self.count) % self.count
            surface.blit(self.frames[i], self.origin)


class GrassLayer:
    """Every blade bends from its own base, with its own timing, in a travelling gust."""

    def __init__(self, image, strength, frames, period, strip=2, wavelength=90):
        self.count, self.period, self.frames = frames, period, []
        self.box = image.get_bounding_rect()
        bx, by, bw, bh = self.box
        if bw == 0 or bh == 0:
            return
        mask = pygame.mask.from_surface(image)
        bottom = by + bh
        rng = random.Random(11)
        cols = []
        for x in range(bx, bx + bw, strip):
            top = next((y for y in range(by, bottom) if mask.get_at((x, y))), bottom)
            cols.append((x, min(strip, bx + bw - x), top,
                         rng.uniform(0.6, 1.2), rng.uniform(0, 6.28)))

        for k in range(frames):
            a = 2 * math.pi * k / frames
            frame = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            for x, width, top, amp, jit in cols:
                gust = 0.75 + 0.25 * math.sin(a - x * 2 * math.pi / (wavelength * 3))
                bend = (0.75 * math.sin(a - x * 2 * math.pi / wavelength)
                        + 0.35 * math.sin(3 * a - x * 2 * math.pi / (wavelength * 0.4) + jit))
                bend *= gust * amp
                span = max(1, bottom - top)
                for row in range(top, bottom):
                    height = 1 - (row - top) / span
                    off = round(bend * strength * height ** 1.5)
                    frame.blit(image, (x + off, row), (x, row, width, 1))
            self.frames.append(frame.convert_alpha())

    def draw(self, surface, t):
        if self.frames:
            surface.blit(self.frames[int(t / self.period * self.count) % self.count], (0, 0))


# ------------------------------------------------------------------
# THE MENU BACKDROP
# ------------------------------------------------------------------
class MenuBackdrop:
    def __init__(self):
        clean = _load("bg_clean.png")
        full = _load("menu_bg.png")
        base = clean or full
        self.base = pygame.transform.scale(base, SIZE) if base else None
        self.fallback = None if base else theme.CozyBackdrop()

        self.trees = []
        self.grass = self.clouds = None
        if clean:
            trees = _load_layer("trees.png")
            if trees:
                for i, region in enumerate(TREE_REGIONS):
                    layer = AliveTree(trees, region, TREE_STRENGTH, TREE_PERIOD,
                                      TREE_FRAMES, phase=i * 2.1,
                                      bob=FROND_BOB, lag=TREE_LAG)
                    if layer.frames:
                        self.trees.append(layer)
            grass = _load_layer("grass.png")
            if grass:
                self.grass = GrassLayer(grass, GRASS_STRENGTH, GRASS_FRAMES,
                                        GRASS_PERIOD, GRASS_STRIP, GRASS_WAVELENGTH)
            self.clouds = _load_layer("clouds.png")

        title = _load("title.png", alpha=True)
        if title:
            if title.get_width() > MAX_TITLE_WIDTH:
                s = MAX_TITLE_WIDTH / title.get_width()
                title = pygame.transform.scale(
                    title, (MAX_TITLE_WIDTH, max(1, int(title.get_height() * s))))
            title = _strip_magenta(title)
        self.title = title

        # STATUS LINE: tells you exactly what loaded
        yes = lambda v: "yes" if v else "NO"
        print("Menu backdrop -> "
              f"bg_clean: {yes(clean)} | palms: {len(self.trees)} | "
              f"grass: {yes(self.grass)} | clouds: {yes(self.clouds)}")
        if not clean:
            print("   !! bg_clean.png NOT FOUND, so no layers are animated.")

        rng = random.Random(5)
        self.stars = [(rng.randint(2, 317), rng.randint(2, 44), rng.uniform(0, 6.28))
                      for _ in range(36)]
        self.flies = [(rng.uniform(0, 320), rng.uniform(118, 170),
                       rng.uniform(0, 6.28), rng.uniform(0.4, 1.0)) for _ in range(10)]
        self.skip = START_PHASE * PHASE_SECONDS
        self.clock = 0.0
        self.debug = False
        self.boost = False
        self.anim = 0.0          # animation clock, can run faster than real time
        self._last_t = None

    # ---------- controls ----------
    @property
    def has_title(self):
        return self.title is not None

    def next_time(self):
        total = self.clock + self.skip
        self.skip += PHASE_SECONDS - (total % PHASE_SECONDS) + 0.01

    def toggle_debug(self):
        self.debug = not self.debug
        
    def toggle_boost(self):
        self.boost = not self.boost

    # ---------- day / night ----------
    def _state(self, t):
        total = (t + self.skip) % (PHASE_SECONDS * len(PHASES))
        i = int(total // PHASE_SECONDS)
        frac = (total % PHASE_SECONDS) / PHASE_SECONDS
        blend = round(max(0.0, (frac - 0.5) * 2) * BLEND_STEPS) / BLEND_STEPS
        a, b = PHASES[i], PHASES[(i + 1) % len(PHASES)]
        tint = tuple(int(a[1][k] + (b[1][k] - a[1][k]) * blend) for k in range(3))
        return tint, a[2] + (b[2] - a[2]) * blend

    # ---------- night extras ----------
    def _night_extras(self, surface, t, night):
        if night < 0.05:
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
                    pygame.draw.rect(surface, (255, 235, 120), (int(fx), int(fy), 2, 2))

    # ---------- drawing ----------
    def draw(self, surface, t=0.0):
        if not self.base:
            self.fallback.draw(surface, t)
            return
        self.clock = t
        dt = 0.0 if self._last_t is None else max(0.0, t - self._last_t)
        self._last_t = t
        self.anim += dt * (4.0 if self.boost else 1.0)
        tint, night = self._state(t)      # day/night keeps real time

        surface.blit(self.base, (0, 0))
        if self.clouds:
         shift = int(self.anim * CLOUD_SPEED) % SIZE[0]
        surface.blit(self.clouds, (shift, 0))
        surface.blit(self.clouds, (shift - SIZE[0], 0))

        for tree in self.trees:
         tree.draw(surface, self.anim)
        if self.grass:
         self.grass.draw(surface, self.anim)

        if self.debug:
            for layer in (*self.trees, self.grass):
                if layer:
                    pygame.draw.rect(surface, (255, 60, 60), layer.box, 1)
            for rect in LIGHTS:
                pygame.draw.rect(surface, (60, 255, 60), rect, 1)

    def draw_title(self, surface, center):
        surface.blit(self.title, self.title.get_rect(center=center))