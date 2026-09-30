import math
import random

import pygame
from src.ui import pixel_art, theme
from src.ui.theme import mix

OUTLINE = (40, 28, 40)
GRASS_SHADOW = (52, 96, 70)


def make_sprite(rows, palette):
    """Turn a list of strings into a Surface. '.' is transparent."""
    surf = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color:
                surf.set_at((x, y), color)
    return surf


PERSON = [
    "...oooooo...",
    "..ohhhhhho..",
    ".ohhhhhhhho.",
    ".ohssssssho.",
    ".osesssseso.",
    ".ossssssso..",
    "...ossssso..",
    ".occcccccco.",
    "occcccccccco",
    "osccccccccso",
    ".oddddddddo.",
    "..oddoodddo.",
    "..obbo.obbo.",
    "..oooo.oooo.",
]

TARSIER = [
    ".oo....oo.",
    "obboooobbo",
    "obbbbbbbbo",
    "obwwbbwwbo",
    "obwkbbkwbo",
    "obbbnnbbbo",
    ".obbbbbbo.",
    ".obbbbbbo.",
    "..oobbbo..",
    "..oo..oo..",
]

ITEM = [
    "..oooo..",
    ".occcco.",
    "occhhcco",
    "occcccco",
    "occcccco",
    "occcccco",
    ".occcco.",
    "..oooo..",
]

BRICK = [
    "lllllllm",
    "bbbbbbbm",
    "bbbbbbbm",
    "mmmmmmmm",
    "lllmllll",
    "bbbmbbbb",
    "bbbmbbbb",
    "mmmmmmmm",
]


def character_sprite(color, hair=(92, 62, 48)):
    return make_sprite(PERSON, {
        "o": OUTLINE, "h": hair, "s": (240, 190, 150), "e": (30, 20, 30),
        "c": color, "d": mix(color, (0, 0, 0), 0.4), "b": (110, 70, 50),
    })


def mascot_sprite(color):
    return make_sprite(TARSIER, {
        "o": (50, 34, 30), "b": color, "w": (255, 255, 255),
        "k": (20, 15, 20), "n": (230, 140, 140),
    })


def item_sprite(color):
    return make_sprite(ITEM, {
        "o": OUTLINE, "c": color, "h": mix(color, (255, 255, 255), 0.55),
    })


def brick_tile():
    return make_sprite(BRICK, {
        "m": (66, 46, 52), "b": (150, 96, 82), "l": (178, 122, 100),
    })


def grass_tiles(count=4, size=16, seed=3):
    rng = random.Random(seed)
    base, dark, light = (86, 140, 100), (72, 122, 88), (104, 160, 110)
    tiles = []
    for _ in range(count):
        t = pygame.Surface((size, size))
        t.fill(base)
        for _ in range(9):
            t.set_at((rng.randrange(size), rng.randrange(size)), dark)
        for _ in range(4):
            t.set_at((rng.randrange(size), rng.randrange(size)), light)
        for _ in range(2):
            x, y = rng.randrange(size), rng.randrange(2, size)
            t.set_at((x, y), dark)
            t.set_at((x, y - 1), dark)
            t.set_at((x, y - 2), light)
        tiles.append(t)
    return tiles


def draw_tiled(surface, rect, tile):
    """Fill a rectangle with a repeating tile."""
    old = surface.get_clip()
    surface.set_clip(rect.clip(surface.get_rect()))
    tw, th = tile.get_size()
    for y in range(rect.y, rect.bottom, th):
        for x in range(rect.x, rect.right, tw):
            surface.blit(tile, (x, y))
    surface.set_clip(old)


def draw_shadow(surface, rect):
    pygame.draw.ellipse(surface, GRASS_SHADOW, (rect.centerx - 6, rect.bottom - 3, 12, 5))


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def vignette(inner=34, outer=95, size=(640, 360), color=(12, 10, 26, 175)):
    """A dark overlay with a dithered (checkerboard-fade) hole in the middle."""
    w, h = size
    cx, cy = w // 2, h // 2
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    for y in range(cy - outer, cy + outer):
        for x in range(cx - outer, cx + outer):
            d = math.hypot(x - cx, y - cy)
            if d >= outer:
                continue
            darkness = max(0.0, (d - inner) / (outer - inner))
            if darkness * 16 <= BAYER[y % 4][x % 4]:
                surf.set_at((x, y), (0, 0, 0, 0))
    return surf