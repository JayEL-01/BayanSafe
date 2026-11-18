# theme design
import math
import random

import pygame

from src.core import settings
from src.utils.data_loader import BASE_DIR

# ------------------------------------------------------------------
# COLORS - Warm Handcrafted Wood, Brass & Storybook Parchment
# ------------------------------------------------------------------
NIGHT      = (28, 18, 12)      # warm dark oak base
PLUM       = (38, 25, 16)      # rich warm dark cedar/walnut wood panel body
PLUM_LIGHT = (78, 52, 32)      # warm carved wood border / highlight
CREAM      = (248, 244, 230)   # main parchment cream text
CREAM_DIM  = (195, 180, 155)   # secondary warm tan parchment text
HONEY      = (255, 190, 61)    # warm amber gold accent, selection, titles
CORAL      = (226, 75, 58)     # danger, health, emergency
SAGE       = (76, 165, 98)     # good, safety, completed
SKY        = (88, 168, 212)    # info, water
LAVENDER   = (148, 132, 172)   # locked / special
SHADOW     = (14, 9, 6)        # deep warm umber shadow

WOOD       = (120, 80, 50)     # warm natural brown button
WOOD_DARK  = (62, 42, 26)      # rich dark cedar/walnut wood plank
WOOD_LIGHT = (145, 98, 62)     # warm amber oak highlight
WOOD_FRAME = (78, 52, 32)      # carved wood frame/border (mid-tone)
WOOD_BORDER= (122, 88, 56)     # carved wood border
BRASS      = (195, 150, 78)    # antique brass trim
BRASS_LIGHT= (225, 180, 95)    # polished brass highlight

DARK_OAK   = (32, 20, 13)      # desk table / screen background base
WOOD_GRAIN = (42, 27, 18)      # subtle desk grain line

PARCHMENT       = (238, 228, 210)
PARCHMENT_LIGHT = (248, 244, 230)
PARCHMENT_DARK  = (212, 196, 168)

STRIPE     = (168, 118, 72)    # warm amber-gold stripes on selected button

INK        = (34, 22, 12)      # near-black brown: maximum contrast on cream paper

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
    "tiny": 28,
    "small": 32,
    "body": 36,
    "button": 36,
    "heading": 44,
    "title": 72,
}
SMOOTH_TEXT = True    # Render at window resolution before scaling for cleaner letter shapes.
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
        # A one-canvas-pixel outline keeps letters legible over busy art and
        # colored panels without relying on a particular background color.
        glyph = font.font.render(text, SMOOTH_TEXT, color)
        if shadow:
            outline = font.font.render(text, SMOOTH_TEXT, SHADOW)
            for ox, oy in ((-scale, 0), (scale, 0), (0, -scale), (0, scale)):
                window.blit(outline, (x * scale + ox, y * scale + oy))
            window.blit(outline, (x * scale + scale, y * scale + scale))
        window.blit(glyph, (x * scale, y * scale))
    TEXT_QUEUE.clear()

# ------------------------------------------------------------------
# SMALL HELPERS
# ------------------------------------------------------------------
def mix(a, b, t):
    """Blend color a toward color b. t=0 gives a, t=1 gives b."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def set_stripe(color):
    """The main menu calls this so the selected button's stripes match the current hazard."""
    global STRIPE
    STRIPE = color


_bg_surface = None


def draw_background(surface):
    """Draw a cozy, handcrafted dark walnut desk table surface with subtle wood grain and soft vignette."""
    global _bg_surface
    w, h = surface.get_size()
    if _bg_surface is None or _bg_surface.get_size() != (w, h):
        s = pygame.Surface((w, h))
        s.fill(DARK_OAK)
        plank_h = 36
        for y in range(0, h, plank_h):
            pygame.draw.line(s, (22, 14, 9), (0, y), (w, y), 1)
            pygame.draw.line(s, (44, 29, 19), (0, y + 1), (w, y + 1), 1)
            for gx0, gx1, gy in ((20, 90, 8), (140, 220, 14), (60, 180, 22), (240, 310, 28)):
                if y + gy < h:
                    pygame.draw.line(s, WOOD_GRAIN, (gx0, y + gy), (gx1, y + gy), 1)
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (10, 6, 4, 70), (0, 0, w, h))
        pygame.draw.rect(vignette, (0, 0, 0, 0), (8, 8, w - 16, h - 16))
        s.blit(vignette, (0, 0))
        _bg_surface = s
    surface.blit(_bg_surface, (0, 0))


def fill_bg(surface, color=NIGHT):
    surface.fill(color)


def fade(surface, alpha, color=SHADOW):
    """Draw a uniform pixel-art fade over everything already on *surface*."""
    alpha = int(max(0, min(255, alpha)))
    if alpha <= 0:
        return
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, alpha))
    surface.blit(overlay, (0, 0))


def dim(surface, alpha=150):
    """Darken everything drawn so far (pause / game over backdrops)."""
    fade(surface, alpha)


def draw_text(surface, text, pos, size="small", color=CREAM, shadow=True, anchor="topleft"):
    """Queue smooth text. It is drawn on top of the scaled canvas.
    `size` is a name from SIZES or a font from get_font()."""
    if isinstance(size, str):
        font = get_font(size)
    elif isinstance(size, TextFont):
        font = size
    else:
        font = get_font("small")   # an old raw pygame font was passed in: use the theme font
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


def draw_footer(surface, text, y=None, color=CREAM_DIM, size="tiny"):
    """Draw the shared one-line control/hint footer near the bottom of a screen."""
    w, h = surface.get_size()
    y = (h - 10) if y is None else y
    return draw_text(surface, text, (w // 2, y), size, color,
                     shadow=False, anchor="midtop")


def draw_option_row(surface, rect, selected=False, accent=HONEY):
    """Shared wooden choice/decision row. Caller queues the wrapped text."""
    rect = pygame.Rect(rect)
    fill = (142, 96, 60) if selected else WOOD_DARK
    border = BRASS_LIGHT if selected else WOOD_BORDER
    pygame.draw.rect(surface, SHADOW, rect.move(0, 2))
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, 1)
    if selected:
        cy = rect.centery
        pygame.draw.polygon(surface, accent,
                            [(rect.x + 4, cy - 3), (rect.x + 9, cy), (rect.x + 4, cy + 3)])
    return rect


def draw_title_card(surface, rect, title, subtitle="", body="", footer="",
                    accent=HONEY, title_size="small"):
    """Uniform story/chapter/transition card with wrapped body text.

    All text is queued through ``draw_text`` so it is drawn after the canvas
    is scaled, just like every other screen in the game.
    """
    rect = pygame.Rect(rect)
    draw_panel(surface, rect, accent=accent)

    from src.ui.text_utils import wrap_text

    y = rect.y + 6
    draw_text(surface, title, (rect.centerx, y), title_size, accent,
              shadow=True, anchor="midtop")
    y += get_font(title_size).get_height() + 2

    if subtitle:
        for line in wrap_text(subtitle, "tiny", rect.w - 14)[:2]:
            draw_text(surface, line, (rect.centerx, y), "tiny", CREAM,
                      shadow=False, anchor="midtop")
            y += line_height("tiny") + 1

    if body:
        lines = body if isinstance(body, (list, tuple)) else wrap_text(body, "tiny", rect.w - 16)
        room = max(0, rect.bottom - y - (18 if footer else 8))
        max_lines = max(0, room // (line_height("tiny") + 1))
        for line in list(lines)[:max_lines]:
            draw_text(surface, line, (rect.x + 8, y), "tiny", CREAM_DIM,
                      shadow=False, anchor="topleft")
            y += line_height("tiny") + 1

    if footer:
        draw_text(surface, footer, (rect.centerx, rect.bottom - 8), "tiny", CREAM_DIM,
                  shadow=False, anchor="midtop")
    return rect


def line_height(size="tiny"):
    """Canvas-pixel line height for a named theme font."""
    return get_font(size).get_height()


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
    _notched_border(surface, rect, WOOD_BORDER)


# ------------------------------------------------------------------
# PIXEL ICONS (8x8) and the wooden-plank button
# ------------------------------------------------------------------
ICONS = {
    "house": ["...##...", "..####..", ".######.", "########",
              ".#.##.#.", ".#.##.#.", ".######.", "........"],
    "clip":  ["..####..", ".######.", ".#....#.", ".#.##.#.",
              ".#....#.", ".#.##.#.", ".#....#.", ".######."],
    "gear":  ["..#..#..", ".######.", "###..###", "##....##",
              "##....##", "###..###", ".######.", "..#..#.."],
    "door":  [".######.", ".#....#.", ".#....#.", ".#..#.#.",
              ".#....#.", ".#....#.", ".#....#.", "########"],
    "book":  ["########", "#..##..#", "#..##..#", "#..##..#",
              "#..##..#", "#..##..#", "########", "........"],
    "light": ["..####..", ".######.", "..####..", "..####..",
              "..####..", "..####..", "..####..", "...##..."],
    "water": ["...##...", "...##...", "..####..", ".######.",
              ".######.", ".######.", "..####..", "........"],
    "radio": ["......#.", ".....#..", "########", "#......#",
              "#.##.#.#", "#.##...#", "#......#", "########"],
    "aid":   ["########", "#..##..#", "#..##..#", "#.####.#",
              "#.####.#", "#..##..#", "#..##..#", "########"],
}


def draw_icon(surface, name, pos, color):
    for j, row in enumerate(ICONS[name]):
        for i, ch in enumerate(row):
            if ch == "#":
                surface.set_at((pos[0] + i, pos[1] + j), color)


def draw_button(surface, rect, text, selected=False, font=None, icon=None, t=None, disabled=False):
    rect = pygame.Rect(rect)
    t = pygame.time.get_ticks() / 1000 if t is None else t
    hot = selected and not disabled

    if disabled:
        fill = (52, 40, 32)
        border = (78, 65, 54)
        text_color = (130, 118, 105)
    elif selected:
        fill = (142, 96, 60)       # warm amber brown
        border = (225, 180, 95)     # polished brass gold
        text_color = (255, 252, 240)# parchment cream
    else:
        fill = WOOD_DARK            # (62, 42, 26) warm dark cedar/walnut
        border = (122, 88, 56)      # carved wood border
        text_color = (238, 228, 210)# soft parchment cream

    # plank body + drop shadow
    pygame.draw.rect(surface, (14, 9, 6), rect.move(0, 2))
    pygame.draw.rect(surface, fill, rect.inflate(-2, 0))
    pygame.draw.rect(surface, fill, rect.inflate(0, -2))
    pygame.draw.line(surface, (168, 118, 78) if selected else (88, 58, 38),
                     (rect.x + 2, rect.y + 1), (rect.right - 3, rect.y + 1))

    # wood grain
    grain = (80, 52, 32) if selected else (46, 30, 18)
    for gy, x0, x1 in ((5, 14, 60), (11, 40, rect.w - 14), (16, 20, 70)):
        if rect.y + gy < rect.bottom - 2:
            pygame.draw.line(surface, grain, (rect.x + x0, rect.y + gy),
                             (min(rect.right - 4, rect.x + x1), rect.y + gy))

    if hot:
        # warm amber/brass stripes on both ends
        shift = int(t * 10)
        for x0 in (rect.x + 2, rect.right - 10):
            for x in range(x0, x0 + 8):
                for y in range(rect.y + 2, rect.bottom - 2):
                    if ((x + y - shift) // 3) % 2 == 0:
                        surface.set_at((x, y), STRIPE)
    else:
        # antique brass nails in the corners
        for nx, ny in ((rect.x + 3, rect.y + 3), (rect.right - 4, rect.y + 3),
                       (rect.x + 3, rect.bottom - 4), (rect.right - 4, rect.bottom - 4)):
            surface.set_at((nx, ny), (185, 142, 74))

    _notched_border(surface, rect, border)

    if icon:
        icon_color = (255, 252, 240) if hot else (text_color if disabled else HONEY)
        draw_icon(surface, icon, (rect.x + 14, rect.centery - 4), icon_color)
    draw_text(surface, text, (rect.centerx + (5 if icon else 0), rect.centery),
              font or "button", text_color, shadow=not disabled, anchor="center")

    if selected:  # pointer arrows that bounce
        b = int(round(math.sin(t * 8) * 1.5))
        cy = rect.centery
        arrow = (225, 180, 95) if hot else (160, 145, 125)
        pygame.draw.polygon(surface, arrow, [(rect.x - 7 - b, cy - 3), (rect.x - 7 - b, cy + 3), (rect.x - 3 - b, cy)])
        pygame.draw.polygon(surface, arrow, [(rect.right + 6 + b, cy - 3), (rect.right + 6 + b, cy + 3), (rect.right + 2 + b, cy)])


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
