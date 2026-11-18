"""Code-generated artwork for BayanSafe's world, menu and UI.

Nothing in this module reads ``assets/images/{menu,ui,world}``: every surface is
drawn in code from the palettes and measurements sampled from the original art,
then memoised so it is built exactly once per process.

Player and NPC sprites are deliberately **not** handled here - those stay as
image files and keep their original loading/drawing code.

Public API
----------
``layer(filename)``
    A canvas-sized replacement for a background/menu/UI image, or ``None`` when
    the name is not one of the code-generated ones.
``icon(name)``
    A pixel-exact SRCALPHA sprite for the small UI icons (sign, lamps, hazard
    badges, go-bag items), or ``None``.
"""
from functools import lru_cache
import math
import random

import pygame

from src.core import settings
from src.ui import theme

SIZE = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)   # 320 x 180


# ------------------------------------------------------------------
# SMALL ICONS - exact pixel grids lifted from the original sprites
# ------------------------------------------------------------------
# name -> (width, height, [palette hex...], [row strings])
# A '.' is transparent (alpha < 40 in the original); a character indexes palette.
ICON_GRIDS = {
    "sign": (54, 33, ["#241c2c", "#9f5c2f", "#8d4e29", "#b67a4b", "#582c30", "#92522a"], [
        ".....0110....................................0200.....",
        ".....0330....................................0300.....",
        ".....030.....................................030......",
        ".....0300....................................0300.....",
        ".....0330....................................030......",
        ".....0330....................................0300.....",
        ".....0000...................................00000.....",
        "....000000.................................0000000....",
        "..00040040000000000000000000000000000000000044004000..",
        ".0002100410000000000000000000000000000000000340015000.",
        "005101125555551313333123322222221111115555551111105200",
        "045000155115555555355525552222222111555555552111300240",
        "045030551112255225555555555222222222225555551110330540",
        "041000000000000000000000000000000000000000000000300540",
        "045500000000000000000000000000000000000000000000002540",
        "002510000000000000000000000000000000000000000000012200",
        "004110000000000000000000000000000000000000000000011100",
        "003150000000000000000000000000000000000000000000011100",
        "045550000000000000000000000000000000000000000000055440",
        "04155000000000000000000000000000000000000000000005114.",
        ".41550000000000000000000000000000000000000000000055540",
        ".41110000000000000000000000000000000000000000000051140",
        "041110000000000000000000000000000000000000000000011140",
        "04555000000000000000000000000000000000000000000002550.",
        "002310000000000000000000000000000000000000000000051140",
        "000220000000000000000000000000000000000000000000055400",
        "041110000000000000000000000000000000000000000000011100",
        "041001000000000000000000000000000000000000000000001140",
        "045030111111111111111111133331111111133113331110330240",
        "042030255511555511111112222222222111555552255250330540",
        "045000255555555555113322222222223331111555511555005240",
        "004522222222255115222222222222222222225525551111552400",
        "..000000000000000000000000000000000000000000000000000.",
    ]),
    "lamp_off": (7, 7, ["#241c2c", "#66405e", "#633d5b", "#7a5c70", "#401b40", "#3f1b3f", "#411b40"], [
        "..000..", ".01110.", "0234420", "0546640", "0156660", ".05510.", "..000..",
    ]),
    "lamp_green": (7, 7, ["#241c2c", "#72ca6a", "#60ac55", "#b1eba7", "#83e079", "#59945a", "#7fdd76", "#3f8449"], [
        "..000..", ".01220.", "0234450", "0444410", "0244670", ".05670.", "..000..",
    ]),
    "lamp_yellow": (7, 7, ["#241c2c", "#faca6a", "#fee298", "#e8ad3e", "#f0b445", "#fee9b6", "#e1a042", "#fddd92", "#b57a33"], [
        "..000..", ".01230.", "0452260", "0222210", "0422780", ".08760.", "..000..",
    ]),
    "lamp_orange": (7, 7, ["#241c2c", "#dc6f32", "#faa13d", "#d1672e", "#fcc080", "#b7552b"], [
        "..000..", ".01230.", "0342250", "0222220", "0322250", ".03250.", "..000..",
    ]),
    "lamp_red": (7, 7, ["#241c2c", "#d84c4c", "#f7716f", "#d34441", "#fba6a9", "#fa7472", "#b23739"], [
        "..000..", ".01230.", "0342230", "0542220", "0322260", ".03230.", "..000..",
    ]),
    "hz_typhoon": (12, 14, ["#241c2c", "#fbe9cb", "#b69a82", "#fbe8c9", "#f2d5a8", "#ad9480", "#e6b061"], [
        ".....00000..",
        "...011100...",
        "..01220000..",
        ".0120022330.",
        "01120400211.",
        "011010300110",
        "051100350320",
        ".0213320320.",
        ".0022200020.",
        "..02006000..",
        "...006660...",
        "....0060....",
        "....060.....",
        "....00......",
    ]),
    "hz_earthquake": (14, 11, ["#241c2c", "#e8e0b4", "#a9c878", "#6d9950", "#fae8c8", "#8d4525", "#934726",
                               "#944927", "#67301e", "#954a27", "#7b3a22", "#6c341f"], [
        ".00000..00000.",
        "00122300022200",
        "03300004030030",
        "05675040555580",
        "06660040660680",
        "06976004060680",
        "079a6a00409980",
        "0b0a0a04099000",
        "0bb000409900b0",
        "00b0b000bb0bb0",
        ".000000000000.",
    ]),
    "hz_flood": (12, 14, ["#241c2c", "#6eacd5", "#80b7d7", "#498ec4", "#6aadd6", "#61a2cf"], [
        ".....00.....",
        ".....010....",
        "....0110....",
        "...012130...",
        "...011130...",
        "...011330...",
        "....0330....",
        ".0...00...0.",
        "000004000400",
        "001110434000",
        ".0000000000.",
        "011004000440",
        "001310051000",
        "..000..00...",
    ]),
    "hz_volcano": (13, 14, ["#241c2c", "#d2bda4", "#d07b69", "#703222", "#8e472a", "#ba4f35", "#632e1d"], [
        "........000..",
        "......001100.",
        ".....0111120.",
        "....01221220.",
        "....0222000..",
        ".....000.....",
        "....02220....",
        "...0034250...",
        "...0234260...",
        "...44442260..",
        "..046446240..",
        ".04664463460.",
        "0466644666460",
        "0000000000000",
    ]),
    "hz_wildfire": (12, 14, ["#241c2c", "#f1624f", "#ef5c4b", "#f9974e", "#f05c4c", "#f0594a", "#fbb244", "#fbe9ca"], [
        "......0.....",
        "......10....",
        ".....012....",
        "...00122....",
        "..0013240...",
        "..004444200.",
        ".0105665200.",
        "005456652040",
        "014556665440",
        "044666766240",
        "044667766240",
        ".0467777650.",
        "..06777760..",
        "..0000000...",
    ]),
    "bag_backpack": (15, 16, ["#241c2c", "#432731", "#b9c692", "#81a66b", "#83a76d", "#84a86e", "#7fa56a",
                               "#7b6139", "#5d8d57", "#4c784d", "#86aa6f", "#7b9d66"], [
        "......0000.....",
        ".....001000....",
        "...000000000...",
        "..00222222210..",
        "..02345554440..",
        "..06744443780..",
        "..05776337780..",
        ".0007000007090.",
        "000870888078000",
        "0a0316666606060",
        "0a06886686b8080",
        "0a0322bbbb28080",
        "08062aaaaaa8080",
        ".0040555558800.",
        "..08999999980..",
        "..00000000000..",
    ]),
    "bag_light": (12, 12, ["#241c2c", "#7f4527", "#feeed4", "#fcd897", "#fbae30", "#fbb53d", "#d6882e"], [
        ".......000..",
        "......01230.",
        ".....0132230",
        ".....0112220",
        "....04011330",
        "...05440100.",
        "..05004600..",
        "..040460....",
        ".044460.....",
        "014460......",
        "01160.......",
        ".000........",
    ]),
    "bag_water": (6, 12, ["#241c2c", "#fdecd7", "#7dbadc", "#5c9cc8", "#70aed6", "#6facd5", "#6fadd6",
                           "#feefda", "#fdedd8", "#6aaad3", "#5183ad", "#e4e4dc"], [
        ".0000.",
        ".0110.",
        ".0230.",
        "024430",
        "045460",
        "078880",
        "089980",
        "088910",
        "0355a0",
        "02aaa0",
        "0b5660",
        ".00000",
    ]),
    "bag_radio": (11, 12, ["#241c2c", "#623327", "#b06635", "#924d26", "#8f4d26", "#8c4a25", "#8d4d26",
                            "#814424", "#cbbeb0", "#381535"], [
        ".......00..",
        "......000..",
        "....000....",
        "..0000.....",
        ".001000000.",
        "02222222220",
        "03405546220",
        "03707140050",
        "03111108800",
        "03707308800",
        "03595440050",
        ".000000000.",
    ]),
    "bag_medkit": (12, 12, ["#241c2c", "#dfcbb6", "#fdeed8", "#c28677", "#fef2df", "#fdedd7", "#fdedd6",
                             "#efdcc6", "#f4624d", "#fdedd8", "#fdecd7", "#fdecd6"], [
        "....00000...",
        "...0000000..",
        ".0100000010.",
        "023455556370",
        "025558852270",
        "099558822970",
        "099888888570",
        "099888888570",
        "0aaab885aa70",
        "01bbb88bbb70",
        "011777777710",
        ".0000000000.",
    ]),
}

_ICON_CACHE = {}


def icon(name):
    """Pixel-exact SRCALPHA sprite for a small UI icon, or None if unknown."""
    if name in _ICON_CACHE:
        return _ICON_CACHE[name]
    grid = ICON_GRIDS.get(name)
    if grid is None:
        _ICON_CACHE[name] = None
        return None
    w, h, palette, rows = grid
    colors = [pygame.Color(*(int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))) for c in palette]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            surf.set_at((x, y), colors[int(ch, 36)])
    _ICON_CACHE[name] = surf
    return surf


# ------------------------------------------------------------------
# DRAWING HELPERS
# ------------------------------------------------------------------
def _bands(surface, rect, top, bottom, steps=7):
    """Chunky vertical gradient (keeps the pixel-art look, no smooth blends)."""
    x, y, w, h = rect
    if steps < 2:
        pygame.draw.rect(surface, top, rect)
        return
    for i in range(steps):
        y0 = y + h * i // steps
        y1 = y + h * (i + 1) // steps
        k = i / (steps - 1)
        col = tuple(int(top[c] + (bottom[c] - top[c]) * k) for c in range(3))
        pygame.draw.rect(surface, col, (x, y0, w, y1 - y0))


def _hut(surface, x, base_y, w, h, wall, roof, dark):
    """A little stilt hut with a thatched gable roof."""
    pygame.draw.rect(surface, wall, (x, base_y - h, w, h))
    pygame.draw.rect(surface, dark, (x, base_y - h, w, 1))
    pygame.draw.polygon(surface, roof,
                        [(x - 3, base_y - h), (x + w + 3, base_y - h), (x + w // 2, base_y - h - 7)])
    pygame.draw.rect(surface, dark, (x + w // 2 - 2, base_y - 7, 4, 7))     # door
    pygame.draw.rect(surface, dark, (x + 2, base_y - h + 3, 4, 4))          # window


def _frond(surface, x, y, angle, length, color):
    pts = []
    for i in range(length):
        t = i / length
        px = x + math.cos(angle) * i
        py = y + math.sin(angle) * i + i * i * 0.03
        pts.append((int(px), int(py)))
    for i in range(len(pts) - 1):
        pygame.draw.line(surface, color, pts[i], pts[i + 1], 2)


def _palm(surface, base_x, base_y, top_x, top_y, trunk, trunk_hi, frond_cols):
    """A leaning palm: trunk plus a fan of drooping fronds."""
    steps = 20
    for i in range(steps):
        t = i / (steps - 1)
        x = base_x + (top_x - base_x) * t
        y = base_y + (top_y - base_y) * t
        w = max(1, int(5 - 3 * t))
        pygame.draw.rect(surface, trunk, (int(x - w / 2), int(y), w, 3))
        pygame.draw.rect(surface, trunk_hi, (int(x - w / 2), int(y), 1, 3))
    angles = (-2.75, -2.35, -1.95, -1.55, -1.15, -0.75, -0.35)
    for k, ang in enumerate(angles):
        col = frond_cols[k % len(frond_cols)]
        _frond(surface, top_x, top_y, ang, 30 + (k % 3) * 5, col)
    pygame.draw.circle(surface, frond_cols[0], (int(top_x), int(top_y)), 3)


# ------------------------------------------------------------------
# MAIN MENU - a coastal barangay at golden hour
# ------------------------------------------------------------------
@lru_cache(maxsize=1)
def menu_scene():
    """Opaque 320x180 coastal-village scene behind the main menu."""
    s = pygame.Surface(SIZE)
    rng = random.Random(7)

    _bands(s, (0, 0, 320, 78), (48, 169, 252), (171, 228, 251), steps=8)   # sky
    # distant tree line on the horizon
    for x in range(0, 320, 4):
        h = 4 + int(3 * math.sin(x * 0.11) + 2 * math.sin(x * 0.37))
        pygame.draw.rect(s, (63, 150, 134), (x, 74 - h, 4, h + 4))
    # a thin band of sea
    _bands(s, (0, 78, 320, 14), (43, 168, 196), (31, 143, 176), steps=3)
    for x in range(0, 320, 9):
        pygame.draw.rect(s, (122, 208, 224), (x, 82 + int(2 * math.sin(x)), 5, 1))

    # land
    _bands(s, (0, 92, 320, 88), (41, 124, 70), (44, 107, 42), steps=6)
    for _ in range(60):                                                    # vegetation clumps
        x, y = rng.randrange(0, 320), rng.randrange(94, 150)
        w, h = rng.randint(8, 26), rng.randint(4, 12)
        col = rng.choice(((52, 143, 88), (58, 150, 74), (38, 118, 60), (86, 145, 60)))
        pygame.draw.ellipse(s, col, (x, y, w, h))
    # crop fields in the mid ground
    for i, (fx, fy, fw, fh) in enumerate(((20, 118, 70, 24), (150, 112, 90, 26), (250, 120, 60, 22))):
        pygame.draw.rect(s, (126, 148, 46) if i % 2 else (162, 163, 40), (fx, fy, fw, fh))
        for yy in range(fy, fy + fh, 4):
            pygame.draw.line(s, (108, 132, 40), (fx, yy), (fx + fw, yy))
    # foreground grass
    _bands(s, (0, 150, 320, 30), (58, 120, 44), (44, 107, 42), steps=3)
    for _ in range(120):
        x, y = rng.randrange(0, 320), rng.randrange(150, 179)
        pygame.draw.line(s, rng.choice(((74, 140, 56), (60, 124, 48))), (x, y), (x, y - 3))

    # huts
    _hut(s, 16, 128, 30, 20, (150, 96, 48), (198, 130, 56), (92, 56, 28))
    _hut(s, 52, 132, 26, 17, (140, 90, 46), (176, 112, 52), (84, 50, 26))
    _hut(s, 206, 108, 34, 24, (168, 104, 50), (206, 140, 60), (96, 58, 30))
    _hut(s, 250, 118, 24, 16, (150, 96, 48), (186, 124, 54), (92, 56, 28))
    _hut(s, 120, 122, 22, 15, (146, 94, 46), (180, 116, 52), (88, 54, 28))

    # a sandy path to the shore
    pygame.draw.polygon(s, (196, 166, 108),
                        [(150, 180), (168, 180), (158, 120), (152, 120)])
    return s


# ------------------------------------------------------------------
# MENU ANIMATION LAYERS (alpha)
# ------------------------------------------------------------------
@lru_cache(maxsize=1)
def trees_layer():
    """Alpha palm layer: one palm in the left half, one in the right half."""
    s = pygame.Surface(SIZE, pygame.SRCALPHA)
    fronds = ((47, 122, 53), (63, 148, 64), (36, 92, 40), (78, 160, 70))
    _palm(s, 30, 174, 44, 96, (107, 68, 34), (138, 92, 46), fronds)
    _palm(s, 296, 174, 282, 100, (107, 68, 34), (138, 92, 46), fronds)
    return s


@lru_cache(maxsize=1)
def grass_layer():
    """Alpha grass layer: blades sprouting from the bottom edge."""
    s = pygame.Surface(SIZE, pygame.SRCALPHA)
    rng = random.Random(11)
    for x in range(0, 320, 2):
        edge = min(x, 319 - x)
        top = 138 + min(26, edge) + rng.randint(0, 12)
        top = min(top, 176)
        col = rng.choice(((47, 122, 53), (63, 148, 64), (36, 92, 40)))
        pygame.draw.line(s, col, (x, 180), (x + rng.randint(-1, 1), top), 2)
    return s


@lru_cache(maxsize=1)
def clouds_layer():
    """Alpha cloud layer: two soft clusters near the top corners."""
    s = pygame.Surface(SIZE, pygame.SRCALPHA)
    white = (250, 250, 252, 235)
    soft = (250, 250, 252, 120)

    def cloud(cx, cy, scale):
        for (dx, dy, w, h, a) in ((0, 0, 34, 12, 235), (-8, -5, 20, 12, 200),
                                  (10, -6, 18, 10, 200), (-2, 5, 40, 8, 110)):
            col = (250, 250, 252, a)
            pygame.draw.ellipse(s, col, (cx + int(dx * scale), cy + int(dy * scale),
                                         int(w * scale), int(h * scale)))

    cloud(46, 22, 1.0)
    cloud(286, 34, 0.85)
    return s


@lru_cache(maxsize=1)
def title_surface():
    """The 'BAYANSAFE' logo as an alpha surface <= 200 px wide (matches the original cap)."""
    pygame.font.init()
    font = theme.get_font("title").font
    gold = (254, 206, 2)
    dark = (40, 18, 0)
    base = font.render("BAYANSAFE", True, gold)
    w, h = base.get_size()
    pad = 4
    out = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    outline = font.render("BAYANSAFE", True, dark)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        out.blit(outline, (pad + dx, pad + dy))
    out.blit(base, (pad, pad))
    target = 196
    if out.get_width() > target:
        s = target / out.get_width()
        out = pygame.transform.smoothscale(out, (target, max(1, int(out.get_height() * s))))
    return out


# ------------------------------------------------------------------
# CHARACTER SELECT - a warm wooden house interior
# ------------------------------------------------------------------
@lru_cache(maxsize=1)
def select_scene():
    s = pygame.Surface(SIZE)
    _bands(s, (0, 0, 320, 34), (131, 65, 31), (104, 50, 28), steps=4)       # ceiling
    for x in range(6, 320, 46):                                             # beams
        pygame.draw.rect(s, (74, 36, 22), (x, 0, 6, 34))
    _bands(s, (0, 34, 320, 108), (150, 83, 29), (122, 62, 26), steps=5)     # back wall
    for x in range(0, 320, 22):                                             # planks
        pygame.draw.line(s, (92, 46, 24), (x, 34), (x, 142))
    _bands(s, (0, 142, 320, 38), (196, 130, 45), (150, 90, 34), steps=4)    # floor
    for y in range(144, 180, 7):
        pygame.draw.line(s, (120, 66, 28), (0, y), (320, y))
    pygame.draw.rect(s, (79, 38, 34), (0, 172, 320, 8))                     # skirting

    # window (see select_backdrop.WINDOW) with a cross frame
    wx, wy, ww, wh = 250, 34, 40, 46
    _bands(s, (wx, wy, ww, wh), (86, 172, 196), (58, 138, 176), steps=3)
    pygame.draw.rect(s, (232, 224, 200), (wx, wy, ww, wh), 2)
    pygame.draw.line(s, (232, 224, 200), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 2)
    pygame.draw.line(s, (232, 224, 200), (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 2)

    # hanging lantern at (48, 44)
    pygame.draw.line(s, (60, 40, 26), (48, 34), (48, 40))
    pygame.draw.rect(s, (72, 52, 30), (43, 40, 10, 12))
    pygame.draw.rect(s, (255, 214, 130), (45, 42, 6, 8))
    return s


# ------------------------------------------------------------------
# OPTIONS - the inside of a green go-bag
# ------------------------------------------------------------------
@lru_cache(maxsize=1)
def options_scene():
    s = pygame.Surface(SIZE)
    _bands(s, (0, 0, 320, 180), (12, 34, 28), (24, 72, 52), steps=8)
    for _ in range(180):                                                    # canvas weave
        x, y = random.randrange(320), random.randrange(180)
        pygame.draw.rect(s, (30, 84, 60), (x, y, 2, 1))
    # pockets
    pygame.draw.rect(s, (20, 52, 40), (0, 60, 34, 90))
    pygame.draw.rect(s, (20, 52, 40), (286, 60, 34, 90))
    pygame.draw.rect(s, (26, 62, 46), (10, 20, 300, 20))
    # a red first-aid pouch on the left, a red flare pouch on the right
    pygame.draw.rect(s, (168, 34, 20), (4, 74, 26, 44))
    pygame.draw.rect(s, (196, 44, 24), (8, 78, 18, 16))
    pygame.draw.rect(s, (150, 24, 16), (270, 74, 30, 46))
    pygame.draw.rect(s, (190, 40, 22), (274, 78, 22, 14))
    # strap across the bottom
    _bands(s, (0, 150, 320, 30), (70, 156, 158), (44, 120, 122), steps=3)
    pygame.draw.rect(s, (16, 44, 34), (0, 146, 320, 6))
    return s


# ------------------------------------------------------------------
# HAZARD GUIDE - a notebook open on a wooden table
# ------------------------------------------------------------------
# these mirror the rects the guide state reads off the original image
GUIDE_LEFT_PAGE = pygame.Rect(56, 29, 100, 117)
GUIDE_RIGHT_PAGE = pygame.Rect(164, 29, 100, 117)
GUIDE_TABS = ((267, 44, 10, 13, (30, 120, 150)),
              (267, 59, 10, 12, (240, 170, 20)),
              (267, 73, 10, 13, (210, 60, 35)),
              (267, 88, 10, 13, (90, 130, 40)))


@lru_cache(maxsize=1)
def guide_scene():
    s = pygame.Surface(SIZE)
    _bands(s, (0, 0, 320, 180), (168, 96, 44), (104, 56, 28), steps=8)      # table
    for y in range(0, 180, 9):
        pygame.draw.line(s, (92, 48, 22), (0, y), (320, y))
    # warm lantern pool on the left
    for r in range(54, 0, -6):
        a = int(70 * (1 - r / 54))
        pygame.draw.circle(s, (min(255, 196 + a), min(255, 140 + a // 2), 56), (30, 60), r)

    # the notebook: dark cover, cream pages
    cover = pygame.Rect(48, 22, 224, 132)
    pygame.draw.rect(s, (74, 40, 22), cover.inflate(8, 8), border_radius=4)
    pygame.draw.rect(s, (54, 28, 16), cover.inflate(4, 4), border_radius=3)
    for page in (GUIDE_LEFT_PAGE, GUIDE_RIGHT_PAGE):
        pygame.draw.rect(s, (250, 213, 140), page)
        pygame.draw.rect(s, (236, 196, 120), page, 1)
    pygame.draw.line(s, (222, 180, 104), (160, 29), (160, 146), 2)          # spine shadow
    # coloured page tabs down the right edge
    for (tx, ty, tw, th, col) in GUIDE_TABS:
        pygame.draw.rect(s, col, (tx, ty, tw, th))
        pygame.draw.rect(s, (60, 34, 20), (tx, ty, tw, th), 1)

    # lantern flame
    pygame.draw.circle(s, (255, 226, 150), (17, 29), 4)
    pygame.draw.circle(s, (255, 250, 210), (17, 29), 2)
    return s


# ------------------------------------------------------------------
# WORLD MAP (aspect-fit 233x131) and JOURNEY MAP (320x180)
# ------------------------------------------------------------------
@lru_cache(maxsize=1)
def worldmap_scene():
    """A small teal ocean chart with a single island - drawn at the fitted 233x131."""
    s = pygame.Surface((233, 131))
    _bands(s, (0, 0, 233, 131), (12, 122, 150), (8, 106, 136), steps=6)
    for _ in range(140):                                                    # wave glints
        x, y = random.randrange(233), random.randrange(131)
        pygame.draw.rect(s, (24, 138, 162), (x, y, 3, 1))
    # island landmass
    pygame.draw.ellipse(s, (150, 158, 66), (22, 22, 192, 92))
    pygame.draw.ellipse(s, (110, 140, 58), (36, 30, 158, 72))
    pygame.draw.ellipse(s, (196, 176, 74), (70, 46, 74, 34))
    # volcano with a warm crater
    pygame.draw.polygon(s, (122, 96, 58), [(150, 58), (176, 96), (124, 96)])
    pygame.draw.polygon(s, (214, 122, 60), [(158, 62), (176, 96), (140, 96)])
    pygame.draw.circle(s, (236, 174, 62), (162, 66), 4)
    return s


@lru_cache(maxsize=1)
def journey_map_scene():
    """The big island the loading screen shows while travelling between chapters."""
    s = pygame.Surface(SIZE)
    _bands(s, (0, 0, 320, 180), (1, 106, 178), (1, 106, 178), steps=2)
    for _ in range(220):                                                    # ocean texture
        x, y = random.randrange(320), random.randrange(180)
        pygame.draw.rect(s, (10, 118, 188), (x, y, 3, 1))
    # surf ring
    pygame.draw.ellipse(s, (157, 201, 229), (18, 14, 284, 152))
    # landmass
    pygame.draw.ellipse(s, (74, 128, 66), (26, 20, 268, 140))
    pygame.draw.ellipse(s, (96, 152, 74), (34, 28, 250, 124))
    for _ in range(90):                                                     # fields
        x, y = random.randrange(40, 280), random.randrange(34, 148)
        pygame.draw.ellipse(s, random.choice(((120, 158, 64), (150, 152, 60), (96, 128, 56))),
                            (x, y, random.randint(6, 18), random.randint(4, 10)))
    # purple mountain range (north)
    for mx, mh in ((150, 26), (168, 32), (188, 28), (206, 22)):
        pygame.draw.polygon(s, (128, 108, 150), [(mx - 14, 52), (mx, 52 - mh), (mx + 14, 52)])
        pygame.draw.polygon(s, (160, 140, 176), [(mx - 5, 52 - mh + 10), (mx, 52 - mh), (mx + 5, 52 - mh + 10)])
    # volcano (east) with a lava glow
    pygame.draw.polygon(s, (110, 70, 40), [(206, 62), (238, 122), (174, 122)])
    pygame.draw.polygon(s, (176, 82, 46), [(214, 68), (238, 122), (190, 122)])
    pygame.draw.circle(s, (226, 122, 52), (216, 66), 6)
    pygame.draw.circle(s, (250, 190, 90), (216, 66), 3)
    return s


# ------------------------------------------------------------------
# DISPATCH
# ------------------------------------------------------------------
_LAYER_BUILDERS = {
    "bg_clean.png": menu_scene,
    "menu_bg.png": menu_scene,
    "trees.png": trees_layer,
    "grass.png": grass_layer,
    "clouds.png": clouds_layer,
    "title.png": title_surface,
    "select_bg.png": select_scene,
    "options_bg.png": options_scene,
    "guide_bg.png": guide_scene,
    "worldmap.png": worldmap_scene,
    "mount_talon_island_map.png": journey_map_scene,
}


def layer(filename):
    """Return the code-drawn replacement for ``filename`` (basename matched), or None."""
    if not filename:
        return None
    name = str(filename).replace("\\", "/").rsplit("/", 1)[-1]
    builder = _LAYER_BUILDERS.get(name)
    return builder() if builder else None
