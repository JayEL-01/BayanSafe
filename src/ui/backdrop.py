import math
import random

import pygame

from src.core import settings
from src.ui import theme
from src.ui.menu_fx import FIRE_FRAMES, HAZARDS, MenuFX
from src.utils.data_loader import BASE_DIR

MENU_DIR = BASE_DIR / "assets" / "images" / "menu"
MAX_TITLE_WIDTH = 200
SIZE = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)

# ------------------------------------------------------------------
# FILES (in assets/images/menu/, all the same canvas ratio as the scene)
#   bg_clean.png  scene with the palms and grass layer erased
#                 (use the VOLCANO version so the cone is always visible)
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
BOOST_SPEED = 4.0         # F3: animation speed multiplier

SHINE_EVERY = 6.0         # logo shine: seconds between sweeps
SHINE_LENGTH = 0.9        # seconds a sweep takes
SHINE_FRAMES = 18

# ------------------------------------------------------------------
# DAY / NIGHT
# ------------------------------------------------------------------
PHASE_SECONDS = 6
DAY_SECONDS = PHASE_SECONDS * 4        # one full day = one hazard
BLEND_STEPS = 6
START_PHASE = 1           # 0 morning, 1 day, 2 evening, 3 night
START_HAZARD = 0          # index in HAZARDS the menu starts with (0 = typhoon)
PHASES = [
    ("morning", (255, 236, 205), 0.0),
    ("day",     (255, 255, 255), 0.0),
    ("evening", (255, 175, 120), 0.35),
    ("night",   (70, 95, 165),   1.0),
]
LIGHTS = [(24, 116, 6, 12), (232, 130, 10, 4), (250, 130, 10, 4)]   # window glow rects

# the scene is multiplied toward this color, scaled by HAZARD_K, as danger rises
HAZARD_TINTS = {
    "typhoon": (170, 180, 205),
    "flood": (160, 182, 205),
    "earthquake": (205, 195, 180),
    "volcano": (185, 140, 120),
    "wildfire": (255, 170, 110),
}
HAZARD_K = {"typhoon": 0.5, "flood": 0.5, "earthquake": 0.35, "volcano": 0.75, "wildfire": 0.6}

TITLE_GAP = 7             # earthquake: how far the two logo halves drift apart (pixels)
TITLE_STAGES = 8          # volcano ash / wildfire burn steps baked for the logo
SWAY_PAD = 6              # typhoon: extra room around the logo so the sway is not clipped


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


def _build_shine(title):
    """Pre-bakes frames of a diagonal highlight sweeping across the logo."""
    w, h = title.get_size()
    frames = []
    for k in range(SHINE_FRAMES):
        pos = -12 + (w + 24 + h // 2) * k / (SHINE_FRAMES - 1)
        frame = title.copy()
        for y in range(h):
            cx = pos - y * 0.5
            for x in range(max(0, int(cx) - 3), min(w, int(cx) + 4)):
                r, g, b, a = frame.get_at((x, y))
                if a > 0:
                    frame.set_at((x, y), (*theme.mix((r, g, b), (255, 255, 255), 0.6), a))
        frames.append(frame)
    return frames


def _bake_split(title):
    """Cuts the logo along a jagged line into a left and right half (done once)."""
    w, h = title.get_size()
    rng = random.Random(8)
    left = pygame.Surface((w, h), pygame.SRCALPHA)
    right = pygame.Surface((w, h), pygame.SRCALPHA)
    x, cuts = w // 2, []
    for y in range(h):
        x = max(w // 2 - 14, min(w // 2 + 14, x + rng.randint(-2, 2)))
        cuts.append(x)
        left.blit(title, (0, y), (0, y, x, 1))
        right.blit(title, (x, y), (x, y, w - x, 1))
    return left, right, cuts


def _bake_decay(title, mode):
    """Pre-bakes the logo getting covered in ash ('ash', settles from the top) or
    charred and glowing ('burn', spreads up from the bottom). Returns TITLE_STAGES+1 images."""
    w, h = title.get_size()
    rng = random.Random(14 if mode == "ash" else 15)
    noise = [[rng.random() for _ in range(w)] for _ in range(h)]
    stages = [title]
    for n in range(1, TITLE_STAGES + 1):
        p = n / TITLE_STAGES
        frame = title.copy()
        for y in range(h):
            bias = y / h if mode == "ash" else 1 - y / h
            for x in range(w):
                r, g, b, a = title.get_at((x, y))
                if a == 0:
                    continue
                v = noise[y][x] * 0.6 + bias * 0.4
                if mode == "ash":
                    if v < p:
                        frame.set_at((x, y), (*theme.mix((r, g, b), (150, 142, 138), 0.75), a))
                elif v < p - 0.12:
                    frame.set_at((x, y), (*theme.mix((r, g, b), (28, 20, 20), 0.85), a))
                elif v < p:
                    frame.set_at((x, y), (*theme.mix((r, g, b), (255, 130, 30), 0.7), a))
        stages.append(frame)
    return stages


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

    def draw(self, surface, t, dx=0):
        if self.frames:
            i = int(t / self.period * self.count) % self.count
            surface.blit(self.frames[i], (self.origin[0] + dx, self.origin[1]))


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
        self.shine = _build_shine(title) if title else []
        self.title_split = _bake_split(title) if title else None
        self.title_ash = _bake_decay(title, "ash") if title else None
        self.title_burn = _bake_decay(title, "burn") if title else None

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
        self.fx = MenuFX()
        self.skip = START_PHASE * PHASE_SECONDS
        self.clock = 0.0          # real time (day/night)
        self.anim = 0.0           # animation time (F3 can speed it up)
        self.tree_anim = 0.0      # tree time (runs faster in an earthquake)
        self._last_t = None
        self.boost = False
        self.debug = False
        self.hazard = HAZARDS[START_HAZARD % len(HAZARDS)]
        self.level = 0.0          # current hazard strength 0..1
        self.storm = 0.0          # typhoon strength only (kept for old code)
        self.look = 0.0           # mouse parallax, -1..1 (smoothed)
        self._look_target = 0.0

    # ---------- controls ----------
    @property
    def has_title(self):
        return self.title is not None

    def next_time(self):
        total = self.clock + self.skip
        self.skip += PHASE_SECONDS - (total % PHASE_SECONDS) + 0.01

    def next_hazard(self):
        """Jump to the evening (peak danger) of the next day, which is the next hazard."""
        total = self.clock + self.skip
        day = int(total // DAY_SECONDS)
        target = (day + 1) * DAY_SECONDS + 2.5 * PHASE_SECONDS
        self.skip += target - total

    def toggle_debug(self):
        self.debug = not self.debug

    def toggle_boost(self):
        self.boost = not self.boost

    def look_at(self, canvas_x):
        """Feed the mouse x (canvas pixels) for a small parallax shift."""
        self._look_target = max(-1.0, min(1.0, (canvas_x - SIZE[0] / 2) / (SIZE[0] / 2)))

    def consume_sounds(self):
        """List of (sound name, volume) the scene wants played this frame."""
        return self.fx.consume_sounds()

    # ---------- day / night / hazard ----------
    @staticmethod
    def _intensity(i, frac):
        """Hazard strength 0..1 across the day: calm, builds, peaks at evening,
        then fades during the night."""
        if i == 0:
            return 0.0
        if i == 1:
            return 0.3 * max(0.0, (frac - 0.5) * 2)
        if i == 2:
            if frac < 0.5:
                return 0.3 + 0.7 * frac * 2
            if frac < 0.8:
                return 1.0
            return 1.0 - 0.4 * (frac - 0.8) / 0.2
        return 0.6 * max(0.0, 1 - frac * 2)

    def _state(self, t):
        total = t + self.skip
        day = int(total // DAY_SECONDS)
        hazard = HAZARDS[(day + START_HAZARD) % len(HAZARDS)]
        total %= DAY_SECONDS
        i = int(total // PHASE_SECONDS)
        frac = (total % PHASE_SECONDS) / PHASE_SECONDS
        blend = round(max(0.0, (frac - 0.5) * 2) * BLEND_STEPS) / BLEND_STEPS
        a, b = PHASES[i], PHASES[(i + 1) % len(PHASES)]
        tint = tuple(int(a[1][k] + (b[1][k] - a[1][k]) * blend) for k in range(3))
        return tint, a[2] + (b[2] - a[2]) * blend, self._intensity(i, frac), hazard

    # ---------- night extras ----------
    def _night_extras(self, surface, t, night, level):
        if night < 0.05:
            return
        glow = int(110 * night)
        for rect in LIGHTS:
            surface.fill((glow, int(glow * 0.7), int(glow * 0.2)), rect,
                         special_flags=pygame.BLEND_RGB_ADD)
        if night > 0.4 and level < 0.3:
            for x, y, phase in self.stars:
                if math.sin(t * 2 + phase) > -0.3:
                    surface.set_at((x, y), theme.CREAM)
        if night > 0.6 and level < 0.3:
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
                                 special_flags=pygame.BLEND_RGB_ADD)      # soft glow
                    pygame.draw.rect(surface, (255, 235, 120), (int(fx), int(fy), 2, 2))

    # ---------- drawing ----------
    def draw(self, surface, t=0.0):
        if not self.base:
            self.fallback.draw(surface, t)
            return
        dt = 0.0 if self._last_t is None else max(0.0, min(0.25, t - self._last_t))
        self._last_t = t
        self.clock = t
        adt = dt * (BOOST_SPEED if self.boost else 1.0)
        self.anim += adt
        a = self.anim
        self.look += (self._look_target - self.look) * 0.08

        tint, night, level, hazard = self._state(t)
        self.hazard = hazard
        self.level = level
        self.storm = level if hazard == "typhoon" else 0.0
        self.fx.update(adt, level, hazard)
        self.tree_anim += adt * (1.0 + 0.7 * self.fx.shake_amp)      # trees thrash in a quake

        surface.blit(self.base, (0, 0))
        if self.clouds:
            shift = int(a * CLOUD_SPEED - self.look * 2) % SIZE[0]
            surface.blit(self.clouds, (shift, 0))
            surface.blit(self.clouds, (shift - SIZE[0], 0))
        self.fx.draw_sky(surface)

        tree_dx = int(round(self.look))
        if self.fx.shake_amp >= 1:
            tree_dx += random.Random(int(a * 20)).randint(-1, 1)
        for tree in self.trees:
            tree.draw(surface, self.tree_anim, tree_dx)
        self.fx.draw_ground(surface)
        if self.grass:
            self.grass.draw(surface, a)

        k = HAZARD_K[hazard] * level
        tint = tuple(int(c * (1 - k * (1 - g / 255))) for c, g in zip(tint, HAZARD_TINTS[hazard]))
        surface.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        self._night_extras(surface, a, night, level)
        self.fx.draw_lights(surface, night)
        self.fx.draw_weather(surface)

        ox, oy = self.fx.shake_offset()                  # earthquake: shake the whole scene
        if ox or oy:
            surface.blit(surface.copy(), (ox, oy))

        if self.debug:
            for layer in (*self.trees, self.grass):
                if layer:
                    pygame.draw.rect(surface, (255, 60, 60), layer.box, 1)
            for rect in LIGHTS:
                pygame.draw.rect(surface, (60, 255, 60), rect, 1)
            self.fx.draw_debug(surface)

    # ---------- the logo reacts to the hazard ----------
    @staticmethod
    def _wind_sway(image, t, amp):
        """Typhoon: the logo bends in the wind (rows shift by a travelling wave)."""
        w, h = image.get_size()
        out = pygame.Surface((w + 2 * SWAY_PAD, h), pygame.SRCALPHA)
        for y in range(h):
            dx = round(amp * (0.7 * math.sin(t * 3.2 - y * 0.07) + 0.5 * math.sin(t * 1.3)))
            out.blit(image, (SWAY_PAD + dx, y), (0, y, w, 1))
        return out

    @staticmethod
    def _arcs(surface, rect, t):
        """Electric arcs crawling down the logo."""
        r = random.Random(int(t * 40))
        for n in range(5):
            x, y = rect.x + r.randint(0, rect.w), rect.y + r.randint(0, rect.h // 3)
            pts = [(x, y)]
            for _ in range(6):
                x += r.randint(-9, 9)
                y += r.randint(4, 10)
                pts.append((x, y))
            pygame.draw.lines(surface, (255, 255, 210) if n % 2 else (130, 210, 255), False, pts, 1)

    def draw_title(self, surface, center):
        image = self.title
        rect = image.get_rect(center=center)
        hz, k, a = self.hazard, self.level, self.anim

        # TYPHOON: sways in the wind, gets electrocuted when lightning strikes
        if hz == "typhoon" and k > 0.1:
            img = self._wind_sway(image, a, k * 3.0)
            pos = (rect.x - SWAY_PAD, rect.y)
            zap = self.fx.zap
            shocked = zap is not None and zap < 0.5
            if shocked:
                r = random.Random(int(a * 40))
                pos = (pos[0] + r.randint(-2, 2), pos[1] + r.randint(-1, 1))
                if int(a * 30) % 2 == 0:                       # white-hot flash
                    img = img.copy()
                    img.fill((120, 120, 50), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(img, pos)
            if shocked:
                self._arcs(surface, rect.move(pos[0] + SWAY_PAD - rect.x, pos[1] - rect.y), a)
            elif k > 0.6:                                      # stray sparks while the storm builds
                r = random.Random(int(a * 12))
                for _ in range(4):
                    surface.set_at((rect.x + r.randint(0, rect.w), rect.y + r.randint(0, rect.h)),
                                   (255, 240, 150))
            return

        # FLOOD: the water reaches the logo, which floats, bobs and sinks into it
        if hz == "flood":
            top = self.fx.water_top
            r2 = rect
            if top < rect.bottom:
                r2 = rect.move(0, int(round(math.sin(a * 2.2) * 1.5)))
            surface.blit(image, r2)
            if top < r2.bottom:
                over = pygame.Surface(r2.size, pygame.SRCALPHA)
                for x in range(0, r2.w, 2):
                    wy = max(0, self.fx.water_y(r2.x + x) - r2.y)
                    if wy < r2.h:
                        pygame.draw.rect(over, (75, 125, 180, 150), (x, wy, 2, r2.h - wy))
                        pygame.draw.rect(over, (190, 225, 245, 200), (x, wy, 2, 1))
                surface.blit(over, r2.topleft)
                for i in range(6):                             # bubbles rising off the logo
                    age = (a * 0.6 + i * 0.17) % 1.0
                    bx = r2.x + (i * 47 + 13) % r2.w
                    by = r2.bottom - age * max(1, r2.bottom - top)
                    if by > r2.y:
                        pygame.draw.circle(surface, (200, 230, 250), (bx, int(by)), 1)
            return

        # VOLCANO: ash settles on the logo, which shudders on every blast
        if hz == "volcano" and self.title_ash:
            p = max(0.0, min(1.0, (k - 0.25) / 0.65))
            pos = rect.topleft
            if self.fx.flash > 0 or (self.fx.ring is not None and self.fx.ring < 0.25):
                r = random.Random(int(a * 40))
                pos = (pos[0] + r.randint(-1, 1), pos[1] + r.randint(-1, 1))
            surface.blit(self.title_ash[int(p * TITLE_STAGES)], pos)
            return

        # WILDFIRE: the logo chars from the bottom up, with flames on the burn front
        if hz == "wildfire" and self.title_burn:
            p = max(0.0, min(1.0, (k - 0.2) / 0.7))
            surface.blit(self.title_burn[int(p * TITLE_STAGES)], rect)
            if p > 0.02:
                front = rect.bottom - p * rect.h
                n = 3 + int(p * 8)
                for i in range(n):
                    fx_x = rect.x + int((i + 0.5) * rect.w / n) + int(math.sin(a * 2 + i) * 3)
                    scale = 2 if (p > 0.6 and i % 3 == 0) else 1
                    spr = self.fx._sprite(FIRE_FRAMES[(int(a * 8) + i) % 3], False, scale)
                    box = spr.get_rect(midbottom=(fx_x, int(front) + 2))
                    surface.fill((34, 12, 0), box.inflate(10, 8), special_flags=pygame.BLEND_RGB_ADD)
                    surface.blit(spr, box)
                for i in range(10):                            # embers lifting off the logo
                    age = (a * 0.5 + i * 0.1) % 1.0
                    ex = rect.x + (i * 53) % rect.w + math.sin(a * 2 + i) * 2
                    surface.set_at((int(ex), int(front - age * 28)),
                                   theme.mix((255, 200, 80), (160, 40, 20), age))
            return

        # EARTHQUAKE: a crack grows, then the logo splits in two
        c = 0.0
        if hz == "earthquake":
            c = max(0.0, min(1.0, (k - 0.35) / 0.5))
        if c > 0 and self.title_split:
            r = random.Random(int(self.clock * 30))
            jx, jy = r.randint(-1, 1), r.randint(0, 1)          # the logo trembles
            left, right, cuts = self.title_split
            if c < 0.5:                                         # stage 1: crack grows downward
                surface.blit(image, rect.move(jx, jy))
                n = int(len(cuts) * c * 2)
                if n >= 2:
                    pts = [(rect.x + jx + cuts[y], rect.y + jy + y) for y in range(n)]
                    pygame.draw.lines(surface, (30, 20, 26), False, pts, 1)
            else:                                               # stage 2: halves drift apart
                gap = int(round((c - 0.5) * 2 * TITLE_GAP))
                surface.blit(left, rect.move(jx - gap, jy + gap // 2))
                surface.blit(right, rect.move(jx + gap, jy - gap // 3))
            return

        # calm: the normal shine sweep
        if self.shine:
            p = (self.clock % SHINE_EVERY) / SHINE_LENGTH
            if p < 1:
                image = self.shine[min(len(self.shine) - 1, int(p * len(self.shine)))]
        surface.blit(image, rect)