import math
import random

import pygame

from src.core import settings
from src.core.strings import tr
from src.ui import theme
from src.ui.menu_fx import FIRE_FRAMES, HAZARDS, MenuFX, QUAKE_SHAKE
from src.utils.data_loader import BASE_DIR

MENU_DIR = BASE_DIR / "assets" / "images" / "menu"
MAX_TITLE_WIDTH = 200
SIZE = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)

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
PHASE_SECONDS = 5
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

# the casing: a rubber shell that hugs the letters of the logo (it only fits the title)
CASE_BODY = (74, 128, 92)      # rubber body
CASE_LIGHT = (150, 205, 150)   # highlights
CASE_DARK = (40, 78, 56)       # outline and shadows
CASE_T = 4                     # how far the casing reaches out from the letters (pixels)
TITLE_STAGES = 8               # ash / burn / crack steps baked for the casing
ENTRANCE_DELAY = 0.15          # seconds before the title drops in when the menu opens
ENTRANCE_TIME = 1.3            # how long the drop, bounce and settle take
SHOW_HINT = False             # True shows the small "click to repair" text under the logo
HINT_FROM, HINT_TO = 3.0, 11.0 # seconds on screen during which "CLICK THE TITLE" shows
# stripe color of the selected button (blended in as the danger rises)
HAZARD_STRIPE = {"typhoon": (40, 90, 130), "flood": (30, 70, 140), "earthquake": (120, 80, 40),
                 "volcano": (150, 40, 40), "wildfire": (170, 70, 20)}


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


def _bake_decay(base, cells, h, mode):
    """The casing getting covered in ash ('ash', settles from the top) or charred and
    glowing ('burn', spreads up from the bottom). TITLE_STAGES+1 images."""
    rng = random.Random(14 if mode == "ash" else 15)
    ranked = [(x, y, rgb, rng.random() * 0.6 + (y / h if mode == "ash" else 1 - y / h) * 0.4)
              for x, y, rgb in cells]
    stages = [base]
    for n in range(1, TITLE_STAGES + 1):
        p = n / TITLE_STAGES
        img = base.copy()
        for x, y, rgb, v in ranked:
            if mode == "ash":
                if v < p:
                    img.set_at((x, y), (*theme.mix(rgb, (150, 142, 138), 0.75), 255))
            elif v < p - 0.12:
                img.set_at((x, y), (*theme.mix(rgb, (28, 20, 20), 0.85), 255))
            elif v < p:
                img.set_at((x, y), (*theme.mix(rgb, (255, 130, 30), 0.7), 255))
        stages.append(img)
    return stages


def _bake_cracks(size, edge, shell_alpha):
    """Cracks that start on the outer edge of the casing and creep in, revealed step by step.
    They are clipped to the casing, so they never touch the logo."""
    rng = random.Random(23)
    cracks = []
    for _ in range(14):
        x, y = edge[rng.randrange(len(edge))]
        ang = rng.uniform(0, 6.28)
        pts = [(x, y)]
        for _ in range(rng.randint(4, 7)):
            ang += rng.uniform(-0.7, 0.7)
            step = rng.uniform(2.5, 4.5)
            x, y = x + math.cos(ang) * step, y + math.sin(ang) * step
            pts.append((x, y))
        cracks.append(pts)
    stages = [None]
    for n in range(1, TITLE_STAGES + 1):
        p = n / TITLE_STAGES
        ov = pygame.Surface(size, pygame.SRCALPHA)
        for i, pts in enumerate(cracks):
            f = max(0.0, min(1.0, (p - 0.7 * i / len(cracks)) / 0.3))
            m = int(len(pts) * f)
            if m >= 2:
                pygame.draw.lines(ov, (18, 12, 22, 255), False, pts[:m], 1)
                pygame.draw.lines(ov, (225, 238, 240, 255), False, [(x + 1, y) for x, y in pts[:m]], 1)
        ov.blit(shell_alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        stages.append(ov)
    return stages


def _bake_case(title):
    """Builds the casing once. It is the silhouette of the letters grown outward by CASE_T
    pixels, painted like rubber, so it fits the title exactly and nothing else."""
    P = CASE_T + 2
    tw, th = title.get_size()
    size = (tw + 2 * P, th + 2 * P)
    letters = pygame.mask.from_surface(title, 40)
    shell = pygame.mask.Mask(size)
    for dy in range(-CASE_T, CASE_T + 1):
        for dx in range(-CASE_T, CASE_T + 1):
            if dx * dx + dy * dy <= CASE_T * CASE_T + 1:
                shell.draw(letters, (P + dx, P + dy))
    ring = shell.copy()
    ring.erase(letters, (P, P))

    def has(x, y):
        return 0 <= x < size[0] and 0 <= y < size[1] and bool(shell.get_at((x, y)))

    base = pygame.Surface(size, pygame.SRCALPHA)
    cells, edge, up_edge = [], [], []
    mid = theme.mix(CASE_BODY, CASE_DARK, 0.5)
    for y in range(size[1]):
        for x in range(size[0]):
            if not shell.get_at((x, y)):
                continue
            if not (has(x - 1, y) and has(x + 1, y) and has(x, y - 1) and has(x, y + 1)):
                rgb = CASE_DARK
                edge.append((x, y))
                if not has(x, y - 1):
                    up_edge.append((x, y))
            elif not has(x, y - 2) or not has(x - 2, y):
                rgb = CASE_LIGHT
            elif not has(x, y + 2) or not has(x + 2, y):
                rgb = mid
            else:
                rgb = CASE_BODY
            base.set_at((x, y), (*rgb, 255))
            cells.append((x, y, rgb))
    if not edge:
        edge = up_edge = [(P, P)]
    up_edge = up_edge or edge
    up_edge.sort()
    tops = {}
    for x, y in up_edge:
        tops[x] = min(y, tops.get(x, 999))

    shell_alpha = shell.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    return {
        "size": size, "P": P, "base": base, "edge": edge, "up": up_edge,
        "tops": sorted(tops.items()),
        "shell_alpha": shell_alpha,
        "shell_rgb": shell.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255)),
        "ring_rgb": ring.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255)),
        "ash": _bake_decay(base, cells, size[1], "ash"),
        "burn": _bake_decay(base, cells, size[1], "burn"),
        "cracks": _bake_cracks(size, edge, shell_alpha),
    }


def _bake_vignette():
    """Darker screen edges, in a few pixel-art steps (not a smooth gradient)."""
    w, h = SIZE
    s = pygame.Surface(SIZE, pygame.SRCALPHA)
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - cx) / cx, (y - cy) / cy * 0.9)
            v = round(min(1.0, max(0.0, (d - 0.62) / 0.8)) * 6) / 6
            if v > 0:
                s.set_at((x, y), (20, 14, 26, int(150 * v)))
    return s


def _bake_glow():
    """Warm lamp light that sits behind the buttons at night."""
    gw, gh = 150, 112
    s = pygame.Surface((gw, gh), pygame.SRCALPHA)
    for y in range(gh):
        for x in range(gw):
            d = math.hypot((x - gw / 2) / (gw / 2), (y - gh / 2) / (gh / 2))
            v = round(max(0.0, 1 - d) * 5) / 5
            if v > 0:
                s.set_at((x, y), (255, 170, 90, int(70 * v)))
    return s


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
        self._case_cache = None   # baked phone case for the logo
        self._sweep = None        # time the last hit-shine started
        self._prev_hit = 0.0
        self._title_rect = None   # clickable area of the logo + casing (set while drawing)
        self._hover = False
        self._repair = 0.0        # 0..1: clicking repairs the casing for a while
        self._taps = []           # recent clicks on the title: (x, y, time)
        self._poked = False       # has the player clicked the title yet (hides the hint)
        self._landed = False      # has the title finished its entrance drop
        self._vig = _bake_vignette()
        self._glow = _bake_glow()
        if self.title:
            self._ensure_case()   # bake the casing now so the entrance does not stutter
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
        self._repair = max(0.0, self._repair - adt * 0.12)      # the repair slowly wears off
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

        if night > 0.3:                                  # warm light behind the buttons at night
            self._glow.set_alpha(int(255 * min(1.0, (night - 0.3) / 0.7)))
            surface.blit(self._glow, (SIZE[0] // 2 - 75, 59))
        self._vig.set_alpha(int(255 * min(1.0, 0.6 + 0.3 * night + 0.25 * level)))
        surface.blit(self._vig, (0, 0))                  # darker edges, stronger at night and in danger
        if hasattr(theme, "set_stripe"):                 # the selected button's stripes follow the hazard
            theme.set_stripe(theme.mix(theme.NIGHT, HAZARD_STRIPE[hazard], min(1.0, level * 1.3)))

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

    @staticmethod
    def _drop(u):
        """Entrance offset in pixels (negative = above its place): fall, bounce, settle."""
        if u < 0.55:
            return -46 * (1 - (u / 0.55) ** 2)
        if u < 0.8:
            return -7 * math.sin(math.pi * (u - 0.55) / 0.25)
        if u < 0.92:
            return -2 * math.sin(math.pi * (u - 0.8) / 0.12)
        return 0.0

    def draw_hint(self, surface):
        """Small "CLICK THE TITLE" hint under the logo for a few seconds, until the player tries it."""
        t = self.clock
        if not SHOW_HINT or self._poked or self._hover or self.title is None or not (HINT_FROM < t < HINT_TO):
            return
        bob = 1 if math.sin(t * 5) > 0 else 0
        theme.draw_text(surface, tr("hint_click"), (SIZE[0] // 2, 63 + bob), "tiny",
                        theme.CREAM, anchor="center")

    # ---------- mouse: the casing reacts to the pointer ----------
    def _on_title(self, pos):
        r = self._title_rect
        return r is not None and r.collidepoint(pos)

    def hover_at(self, pos):
        """Feed the mouse position (canvas pixels). Hovering makes the casing shine."""
        on = self._on_title(pos)
        if on and not self._hover:
            self._sweep = self.anim                     # a gloss streak sweeps in when the pointer arrives
        self._hover = on

    def poke(self, pos):
        """Feed a left click. Clicking the title flares the casing, throws sparks and repairs it
        for a while. Returns True if the title was hit."""
        if not self._on_title(pos):
            return False
        self._poked = True
        self._taps = (self._taps + [(pos[0], pos[1], self.anim)])[-6:]
        self._repair = min(1.0, self._repair + 0.35)
        self._sweep = self.anim
        self.fx.sounds.append(("tink", 0.45))
        return True

    # ---------- the phone case: disasters hit it, the logo inside stays safe ----------
    def _hit(self):
        """0..1 strength of the current impact on the case (each hit makes it shine)."""
        fx, hz = self.fx, self.hazard
        if hz == "typhoon":
            z = fx.zap
            return 0.0 if z is None or z > 0.5 else 1 - z / 0.5
        if hz == "volcano":
            h = fx.flash / 0.18
            if fx.ring is not None and fx.ring < 0.4:
                h = max(h, 1 - fx.ring / 0.4)
            return min(1.0, h)
        if hz == "earthquake":
            return min(1.0, fx.shake_amp / QUAKE_SHAKE)
        if self.level < 0.3:
            return 0.0
        if hz == "wildfire":                                # a flame flare every 2.4 s
            return max(0.0, 1 - (self.anim % 2.4) / 0.4)
        return max(0.0, 1 - (self.anim % 3.2) / 0.5)        # a wave slams in every 3.2 s

    def _ensure_case(self):
        if self._case_cache is None:
            self._case_cache = _bake_case(self.title)
        return self._case_cache

    def _fall_onto(self, surface, pos, c, n, color, speed, splash):
        """Particles fall onto the tops of the letters (and splash if asked)."""
        tops, a = c["tops"], self.anim
        for i in range(n):
            x, y0 = tops[int(((i * 0.7548776) % 1.0) * len(tops))]
            px, py = pos[0] + x, pos[1] + y0
            age = (a * speed * 0.5 + (i * 0.6180339) % 1.0) % 1.0
            if age < 0.8:
                y = py - 14 + int(age / 0.8 * 14)
                surface.set_at((px, y), color)
                surface.set_at((px, y - 1), color)
            elif splash:
                d = int((age - 0.8) / 0.2 * 2)
                surface.set_at((px - 1 - d, py - 1 - d), color)
                surface.set_at((px + 1 + d, py - 1 - d), color)

    def _case_water(self, surface, pos, c):
        """The flood drowns the casing: it goes under water and bubbles leak out, the logo stays dry."""
        w, h = c["size"]
        top = self.fx.water_top
        if top >= pos[1] + h:
            return
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(0, w, 2):
            wy = max(0, self.fx.water_y(pos[0] + x) - pos[1])
            if wy < h:
                pygame.draw.rect(ov, (75, 125, 180, 165), (x, wy, 2, h - wy))
                pygame.draw.rect(ov, (190, 225, 245, 210), (x, wy, 2, 1))
        ov.blit(c["shell_alpha"], (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(ov, pos)
        edge = c["edge"]
        for i in range(10):                                 # bubbles leaking out of the casing
            ex, ey = edge[(i * 37) % len(edge)]
            if pos[1] + ey < top:
                continue
            age = (self.anim * 0.5 + i * 0.1) % 1.0
            y = pos[1] + ey - age * (pos[1] + ey - top)
            pygame.draw.circle(surface, (200, 230, 250), (pos[0] + ex + int(math.sin(age * 9 + i) * 2), int(y)), 1)

    def _flame(self, surface, x, y, i, scale):
        spr = self.fx._sprite(FIRE_FRAMES[(int(self.anim * 8) + i) % 3], False, scale)
        box = spr.get_rect(midbottom=(int(x), int(y)))
        surface.fill((34, 12, 0), box.inflate(10, 8), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(spr, box)

    def draw_title(self, surface, center):
        image = self.title
        rect = image.get_rect(center=center)
        hz, k, a = self.hazard, self.level, self.anim
        active = k >= 0.12
        hit = self._hit() if active else 0.0
        u = (self.clock - ENTRANCE_DELAY) / ENTRANCE_TIME      # entrance: the title drops in and bounces
        if u < 1.0:
            rect = rect.move(0, -90 if u < 0 else int(round(self._drop(u))))
            if not self._landed and u >= 0.55:                 # it lands: the casing flashes, a thud
                self._landed = True
                self._sweep = a
                self.fx.sounds.append(("thud", 0.45))
        c = self._ensure_case()
        P = c["P"]
        w, h = c["size"]
        rep = self._repair
        self._title_rect = pygame.Rect(rect.x - P, rect.y - P, w, h)

        if hit > 0.6 and self._prev_hit <= 0.6:             # every big hit starts a shine sweep
            self._sweep = a
        self._prev_hit = hit

        zap = self.fx.zap if hz == "typhoon" else None
        shocked = active and zap is not None and zap < 0.5
        m = 2 if shocked else (int(round(self.fx.shake_amp / 2)) if (active and hz == "earthquake") else 0)
        pos = (rect.x - P, rect.y - P)
        if m:                                               # the casing buzzes, the logo inside holds still
            r = random.Random(int(a * 40))
            pos = (pos[0] + r.randint(-m, m), pos[1] + r.randint(-(m // 2), m // 2))

        frame, p = c["base"], 0.0
        if active and hz == "volcano":
            p = max(0.0, min(1.0, (k - 0.25) / 0.65)) * (1 - rep)      # a repaired casing is cleaner
            frame = c["ash"][int(p * TITLE_STAGES)]
        elif active and hz == "wildfire":
            p = max(0.0, min(1.0, (k - 0.2) / 0.7)) * (1 - rep)
            frame = c["burn"][int(p * TITLE_STAGES)]
        if shocked and int(a * 30) % 2 == 0:                # white-hot flash while electrocuted
            frame = frame.copy()
            frame.fill((120, 120, 60, 0), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(frame, pos)

        # ----- damage that sits ON the casing (clipped to it) -----
        crack = 0.0
        if active and hz == "earthquake":
            crack = max(0.0, min(1.0, (k - 0.3) / 0.6))
        elif active and hz == "volcano":
            crack = 0.6 * max(0.0, min(1.0, (k - 0.45) / 0.5))
        crack *= (1 - rep)
        if crack > 0.02 and c["cracks"][int(crack * TITLE_STAGES)] is not None:
            surface.blit(c["cracks"][int(crack * TITLE_STAGES)], pos)
        if active and hz == "flood":
            self._case_water(surface, pos, c)

        # ----- the logo itself is never damaged -----
        if hit > 0.4:                                       # it soaks up the energy and glows gold
            image = image.copy()
            image.fill((int(60 * hit), int(45 * hit), int(10 * hit)), special_flags=pygame.BLEND_RGB_ADD)
        elif self.shine:                                    # calm shine sweep
            q = (self.clock % SHINE_EVERY) / SHINE_LENGTH
            if q < 1:
                image = self.shine[min(len(self.shine) - 1, int(q * len(self.shine)))]
        squash = bool(self._taps) and a - self._taps[-1][2] < 0.12          # the logo hops when tapped
        surface.blit(image, rect.move(0, 1) if squash else rect)

        # ----- hazard effects around the casing -----
        edge, up = c["edge"], c["up"]
        if active and hz == "typhoon":
            self._fall_onto(surface, pos, c, 16, (150, 180, 220), 2.2, True)
            if shocked:                                     # electric arcs crawl over the casing
                r = random.Random(int(a * 40))
                for n in range(8):
                    ex, ey = edge[r.randrange(len(edge))]
                    x, y = pos[0] + ex, pos[1] + ey
                    pts = [(x, y)]
                    for _ in range(4):
                        x += r.randint(-4, 4)
                        y += r.randint(-4, 4)
                        pts.append((x, y))
                    pygame.draw.lines(surface, (255, 255, 210) if n % 2 else (130, 210, 255), False, pts, 1)
            elif k > 0.6:                                   # stray sparks while the storm builds
                r = random.Random(int(a * 12))
                for _ in range(4):
                    ex, ey = edge[r.randrange(len(edge))]
                    surface.set_at((pos[0] + ex, pos[1] + ey), (255, 240, 150))
        elif active and hz == "volcano":
            self._fall_onto(surface, pos, c, 14, (160, 152, 146), 1.0, False)
            if self.fx.ring is not None:                    # lava splatters cooling on the casing
                f = 1 - self.fx.ring / 0.8
                tops = c["tops"]
                for i in range(8):
                    x, y = tops[(i * 41) % len(tops)]
                    surface.fill(theme.mix((60, 40, 30), (255, 150, 40), f), (pos[0] + x, pos[1] + y, 2, 2))
        elif active and hz == "earthquake":
            self._fall_onto(surface, pos, c, 14, (170, 145, 110), 1.6, False)
        elif active and hz == "wildfire" and p > 0.02:
            front = h - p * h                               # burn front, from the bottom up
            cand = [e for e in up if e[1] >= front - 2] or up
            n = 3 + int(p * 9)
            for i in range(n):                              # flames sit on the burning edges
                ex, ey = cand[min(len(cand) - 1, int((i + 0.5) * len(cand) / n))]
                self._flame(surface, pos[0] + ex, pos[1] + ey + 2, i, 2 if (hit > 0.5 and i % 2 == 0) else 1)
            for i in range(10):                             # embers lifting off
                ex, ey = cand[(i * 17) % len(cand)]
                age = (a * 0.5 + i * 0.1) % 1.0
                surface.set_at((pos[0] + ex + int(math.sin(a * 2 + i) * 2), int(pos[1] + ey - age * 30)),
                               theme.mix((255, 200, 80), (160, 40, 20), age))

        # ----- shine: the casing flares and a gloss streak sweeps over the title on every hit -----
        sw = None
        if self._sweep is not None:
            u = (a - self._sweep) / 0.45
            if u >= 1:
                self._sweep = None
            else:
                sw = u
        gl = hit * (0.45 if hz == "earthquake" else 1.0)       # a quake is constant, so keep its glow calmer
        if self._hover:
            gl = max(gl, 0.28 + 0.07 * math.sin(a * 6))         # pointer on the title: the casing glows
        if gl > 0.05:
            glow = pygame.Surface((w, h))
            glow.fill((int(120 * gl), int(150 * gl), int(110 * gl)))
            glow.blit(c["ring_rgb"], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, pos, special_flags=pygame.BLEND_RGB_ADD)
        if sw is not None:
            streak = pygame.Surface((w, h))
            xc = int(-20 + (w + 40) * sw)
            pygame.draw.polygon(streak, (110, 110, 90), [(xc, 0), (xc + 14, 0), (xc + 14 - h // 2, h), (xc - h // 2, h)])
            pygame.draw.polygon(streak, (60, 60, 50), [(xc + 20, 0), (xc + 24, 0), (xc + 24 - h // 2, h), (xc + 20 - h // 2, h)])
            streak.blit(c["shell_rgb"], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(streak, pos, special_flags=pygame.BLEND_RGB_ADD)

        # ----- taps: a ripple runs over the casing and sparks fly from the click -----
        live = []
        for tx, ty, t0 in self._taps:
            age = a - t0
            if age >= 0.6:
                continue
            live.append((tx, ty, t0))
            if age < 0.45:
                f = 1 - age / 0.45
                ring = pygame.Surface((w, h))
                pygame.draw.circle(ring, (int(130 * f), int(190 * f), int(120 * f)),
                                   (tx - pos[0], ty - pos[1]), int(4 + age / 0.45 * 34), 2)
                ring.blit(c["shell_rgb"], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(ring, pos, special_flags=pygame.BLEND_RGB_ADD)
            for i in range(7):                              # sparks fly out, then fall
                ang = i * 0.9 + (t0 * 7 % 1.0) * 3
                spd = 34 + (i * 13) % 22
                sx = tx + math.cos(ang) * spd * age
                sy = ty + math.sin(ang) * spd * age + 90 * age * age
                col = theme.mix((255, 245, 200), (247, 195, 90), min(1.0, age / 0.5))
                surface.set_at((int(sx), int(sy)), col)
                if age < 0.25:
                    surface.set_at((int(sx) + 1, int(sy)), col)
        self._taps = live

        # ----- repaired: green twinkles run along the casing while the repair lasts -----
        if rep > 0.05:
            r = random.Random(int(a * 10))
            for _ in range(int(2 + rep * 12)):
                ex, ey = c["edge"][r.randrange(len(c["edge"]))]
                surface.set_at((pos[0] + ex, pos[1] + ey), theme.mix(CASE_LIGHT, (255, 255, 255), 0.6))