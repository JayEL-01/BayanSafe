"theme design"
import math
import random

import pygame

from src.core import settings
from src.utils.data_loader import BASE_DIR

# ------------------------------------------------------------------
# COLORS
# ------------------------------------------------------------------
WOOD       = (120, 78, 44)     # plank
WOOD_DARK  = (84, 52, 32)      # unselected plank
WOOD_LIGHT = (168, 114, 64)    # plank highlight
NIGHT      = (36, 28, 44)      # deepest background
PLUM       = (52, 40, 60)      # panel fill
PLUM_LIGHT = (72, 57, 80)      # panel highlight / unselected button
CREAM      = (255, 244, 224)   # main text
CREAM_DIM  = (196, 180, 170)   # secondary text
HONEY      = (247, 195, 90)    # accent, selection, titles
CORAL      = (232, 118, 104)   # danger, health, bad
SAGE       = (140, 196, 132)   # good, done
SKY        = (124, 178, 204)   # info, water
LAVENDER   = (168, 140, 200)   # locked / special
SHADOW     = (20, 14, 26)      # text and panel shadows

LEVEL_COLORS = {               # Danger Meter levels
    "NORMAL": SAGE,
    "WATCH": HONEY,
    "WARNING": (240, 150, 80),
    "CRITICAL": CORAL,
}


# ------------------------------------------------------------------
# FONTS: smooth text, drawn at full window resolution (after scaling)
# ------------------------------------------------------------------
FONT_DIR = BASE_DIR / "assets" / "fonts" / "text"

# Sizes are in WINDOW pixels (the canvas is scaled x4).
SIZES = {
    "tiny": 24,
    "small": 26,
    "body": 28,
    "button": 32,
    "heading": 44,
    "title": 72,
}
SMOOTH_TEXT = False   # False = crisp pixel edges (good for Pixelify Sans). True = soft edges.
TEXT_QUEUE = []       # text waiting to be drawn on top of the scaled canvas
_font_cache = {}
_font_file = "unset"


def _find_font_file():
    global _font_file
    if _font_file == "unset":
        _font_file = None
        if FONT_DIR.exists():
            files = sorted(FONT_DIR.glob("*.ttf")) + sorted(FONT_DIR.glob("*.otf"))
            if files:
                _font_file = files[0]
        if _font_file is None:
            print(f"No font found in {FONT_DIR}. Using the default font.")
    return _font_file


class TextFont:
    """A smooth font. size() reports CANVAS pixels so layouts and wrap_text still work."""

    def __init__(self, window_size):
        path = _find_font_file()
        self.font = (pygame.font.Font(str(path), window_size) if path
                     else pygame.font.Font(None, window_size + 6))
        self.height = self.font.get_height() / settings.SCALE

    def size(self, text):
        w, h = self.font.size(text)
        return (int(w / settings.SCALE) + 1, int(h / settings.SCALE) + 1)

    def get_height(self):
        return int(self.height) + 1

    def render(self, text, antialias=False, color=(255, 255, 255)):
        """Fallback for old code that renders directly. Prefer theme.draw_text."""
        big = self.font.render(text, True, color)
        w, h = big.get_size()
        return pygame.transform.smoothscale(
            big, (max(1, w // settings.SCALE), max(1, h // settings.SCALE)))


def get_font(name="small"):
    if name not in _font_cache:
        _font_cache[name] = TextFont(SIZES[name])
    return _font_cache[name]


def flush_text(window):
    """Called by Game after the canvas is scaled up. Draws all queued text."""
    scale = settings.SCALE
    for font, text, color, (x, y), shadow in TEXT_QUEUE:
        if shadow:
            window.blit(font.font.render(text, SMOOTH_TEXT, SHADOW), (x * scale + 2, y * scale + 2))
        window.blit(font.font.render(text, SMOOTH_TEXT, color), (x * scale, y * scale))
    TEXT_QUEUE.clear()

# ------------------------------------------------------------------
# SMALL HELPERS
# ------------------------------------------------------------------
def mix(a, b, t):
    """Blend color a toward color b. t=0 gives a, t=1 gives b."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fill_bg(surface, color=NIGHT):
    surface.fill(color)


def dim(surface, alpha=150):
    """Darken everything drawn so far (pause / game over backdrops)."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*SHADOW, alpha))
    surface.blit(overlay, (0, 0))


def draw_text(surface, text, pos, size="small", color=CREAM, shadow=True, anchor="topleft"):
    """Queue smooth text. It is drawn on top of the scaled canvas.
    `size` is a name from SIZES or a font from get_font()."""
    font = get_font(size) if isinstance(size, str) else size
    w, h = font.size(text)
    rect = pygame.Rect(0, 0, w, h)
    setattr(rect, anchor, pos)
    TEXT_QUEUE.append((font, text, color, rect.topleft, shadow))
    return rect


# ------------------------------------------------------------------
# PANELS, BARS, BUTTONS
# ------------------------------------------------------------------
_panel_cache = {}


def _panel_surface(w, h, alpha):
    key = (w, h, alpha)
    if key not in _panel_cache:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        fill = (*PLUM, alpha)
        pygame.draw.rect(s, fill, (1, 0, w - 2, h))       # rounded pixel corners
        pygame.draw.rect(s, fill, (0, 1, w, h - 2))
        pygame.draw.line(s, (*PLUM_LIGHT, alpha), (2, 1), (w - 3, 1))
        _panel_cache[key] = s
    return _panel_cache[key]


def _notched_border(surface, rect, color):
    x, y, w, h = rect
    pygame.draw.line(surface, color, (x + 1, y), (x + w - 2, y))
    pygame.draw.line(surface, color, (x + 1, y + h - 1), (x + w - 2, y + h - 1))
    pygame.draw.line(surface, color, (x, y + 1), (x, y + h - 2))
    pygame.draw.line(surface, color, (x + w - 1, y + 1), (x + w - 1, y + h - 2))


def draw_panel(surface, rect, title=None, accent=HONEY, alpha=235):
    """A cozy panel with rounded pixel corners, a border and a drop shadow.
    Content should start about 18 px below the top when a title is used."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, SHADOW, (rect.x + 2, rect.bottom, rect.w - 1, 2))
    pygame.draw.rect(surface, SHADOW, (rect.right, rect.y + 2, 2, rect.h))
    surface.blit(_panel_surface(rect.w, rect.h, alpha), rect.topleft)
    _notched_border(surface, rect, mix(PLUM_LIGHT, accent, 0.65))
    if title:
        draw_text(surface, title, (rect.x + 6, rect.y + 3), "tiny", accent, shadow=False)
        pygame.draw.line(surface, mix(PLUM, accent, 0.35),
                         (rect.x + 4, rect.y + 15), (rect.right - 5, rect.y + 15))
    return rect


def draw_bar(surface, rect, value, maximum, color):
    """A chunky pixel progress bar (health, danger, timers)."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, SHADOW, rect)
    inner = rect.inflate(-2, -2)
    ratio = max(0.0, min(1.0, value / maximum)) if maximum else 0
    fill = pygame.Rect(inner.x, inner.y, int(inner.w * ratio), inner.h)
    if fill.w > 0:
        pygame.draw.rect(surface, color, fill)
        pygame.draw.line(surface, mix(color, CREAM, 0.45),
                         (fill.x, fill.y), (fill.right - 1, fill.y))
    _notched_border(surface, rect, CREAM_DIM)


ICONS = {   # 8x8 pixel icons
    "house": ["...##...", "..####..", ".######.", "########",
              ".#.##.#.", ".#.##.#.", ".######.", "........"],
    "clip":  ["..####..", ".######.", ".#....#.", ".#.##.#.",
              ".#....#.", ".#.##.#.", ".#....#.", ".######."],
    "gear":  ["..#..#..", ".######.", "###..###", "##....##",
              "##....##", "###..###", ".######.", "..#..#.."],
    "door":  [".######.", ".#....#.", ".#....#.", ".#..#.#.",
              ".#....#.", ".#....#.", ".#....#.", "########"],
}


def _draw_icon(surface, name, pos, color):
    for j, row in enumerate(ICONS[name]):
        for i, ch in enumerate(row):
            if ch == "#":
                surface.set_at((pos[0] + i, pos[1] + j), color)


def draw_button(surface, rect, text, selected=False, font=None, icon=None, t=None):
    rect = pygame.Rect(rect)
    t = pygame.time.get_ticks() / 1000 if t is None else t

    if selected:
        fill, border, text_color = HONEY, CREAM, NIGHT
    else:
        fill, border, text_color = WOOD_DARK, mix(WOOD_DARK, WOOD_LIGHT, 0.6), CREAM

    # plank body + drop shadow
    pygame.draw.rect(surface, SHADOW, rect.move(0, 2))
    pygame.draw.rect(surface, fill, rect.inflate(-2, 0))
    pygame.draw.rect(surface, fill, rect.inflate(0, -2))
    pygame.draw.line(surface, mix(fill, CREAM, 0.25),
                     (rect.x + 2, rect.y + 1), (rect.right - 3, rect.y + 1))

    # wood grain
    grain = mix(fill, SHADOW, 0.25)
    for gy, x0, x1 in ((5, 14, 60), (11, 40, rect.w - 14), (16, 20, 70)):
        if rect.y + gy < rect.bottom - 2:
            pygame.draw.line(surface, grain, (rect.x + x0, rect.y + gy),
                             (min(rect.right - 4, rect.x + x1), rect.y + gy))

    if selected:
        # scrolling hazard stripes on both ends
        shift = int(t * 10)
        for x0 in (rect.x + 2, rect.right - 10):
            for x in range(x0, x0 + 8):
                for y in range(rect.y + 2, rect.bottom - 2):
                    if ((x + y - shift) // 3) % 2 == 0:
                        surface.set_at((x, y), NIGHT)
    else:
        # nails in the corners
        for nx, ny in ((rect.x + 3, rect.y + 3), (rect.right - 4, rect.y + 3),
                       (rect.x + 3, rect.bottom - 4), (rect.right - 4, rect.bottom - 4)):
            surface.set_at((nx, ny), CREAM_DIM)

    _notched_border(surface, rect, border)

    if icon:
        _draw_icon(surface, icon, (rect.x + 14, rect.centery - 4), NIGHT if selected else HONEY)
    draw_text(surface, text, (rect.centerx + (5 if icon else 0), rect.centery),
              font or "button", text_color, shadow=not selected, anchor="center")

    if selected:  # pointer arrows that bounce
        b = int(round(math.sin(t * 8) * 1.5))
        cy = rect.centery
        pygame.draw.polygon(surface, HONEY, [(rect.x - 7 - b, cy - 3), (rect.x - 7 - b, cy + 3), (rect.x - 3 - b, cy)])
        pygame.draw.polygon(surface, HONEY, [(rect.right + 6 + b, cy - 3), (rect.right + 6 + b, cy + 3), (rect.right + 2 + b, cy)])


# ------------------------------------------------------------------
# COZY BACKDROP: dusk sky, stars, moon, hill village, fireflies
# ------------------------------------------------------------------
SKY_TOP = (44, 34, 78)
SKY_BOTTOM = (226, 132, 112)
HILL_FAR = (98, 66, 96)
HILL_NEAR = (58, 44, 70)


class CozyBackdrop:
    def __init__(self, seed=7):
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        rng = random.Random(seed)
        self.static = pygame.Surface((w, h))

        # Sky in chunky bands (looks pixel-art, not a smooth gradient)
        for y in range(0, h, 6):
            pygame.draw.rect(self.static, mix(SKY_TOP, SKY_BOTTOM, (y / h) ** 1.4), (0, y, w, 6))

        # Moon with a crescent bite
        moon_color = mix(SKY_TOP, SKY_BOTTOM, (34 / h) ** 1.4)
        pygame.draw.circle(self.static, CREAM, (262, 34), 10)
        pygame.draw.circle(self.static, moon_color, (267, 31), 9)

        # Hills
        for x in range(w):
            far = 118 + math.sin(x * 0.021 + 1) * 9 + math.sin(x * 0.06) * 3
            pygame.draw.line(self.static, HILL_FAR, (x, int(far)), (x, h))
        near_y = lambda x: 146 + math.sin(x * 0.03) * 7 + math.sin(x * 0.09 + 2) * 2
        for x in range(w):
            pygame.draw.line(self.static, HILL_NEAR, (x, int(near_y(x))), (x, h))

        # Little houses with glowing windows
        for hx, hw, hh in [(22, 20, 13), (58, 15, 10), (232, 21, 14), (272, 16, 11)]:
            base = int(near_y(hx + hw // 2)) + 3
            body = pygame.Rect(hx, base - hh, hw, hh)
            pygame.draw.rect(self.static, NIGHT, body)
            pygame.draw.polygon(self.static, mix(NIGHT, CORAL, 0.35),
                                [(hx - 2, base - hh), (hx + hw // 2, base - hh - 7), (hx + hw + 2, base - hh)])
            win = pygame.Rect(hx + hw // 2 - 2, base - hh + 3, 4, 4)
            pygame.draw.rect(self.static, HONEY, win)

        self.stars = [(rng.randint(2, w - 3), rng.randint(2, 88), rng.uniform(0, 6.28))
                      for _ in range(38)]
        self.flies = [(rng.uniform(0, w), rng.uniform(120, 172), rng.uniform(0, 6.28), rng.uniform(0.4, 1.0))
                      for _ in range(9)]

    def draw(self, surface, t=0.0):
        surface.blit(self.static, (0, 0))
        for x, y, phase in self.stars:
            s = math.sin(t * 2 + phase)
            if s > -0.4:
                color = CREAM if s > 0.6 else mix(SKY_TOP, CREAM, 0.55)
                surface.set_at((x, y), color)
        for x, y, phase, speed in self.flies:
            fx = x + math.sin(t * speed + phase) * 14
            fy = y + math.sin(t * speed * 1.7 + phase) * 6
            glow = (math.sin(t * 3 + phase) + 1) / 2
            pygame.draw.rect(surface, mix(HILL_NEAR, HONEY, 0.4 + 0.6 * glow), (int(fx), int(fy), 2, 2))