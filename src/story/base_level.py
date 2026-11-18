"""Base Level Framework for BayanSafe Story Chapters.

Coordinates the code-rendered BlockMap, animated NPC sprites, Player entity,
active environmental Hazards, Decision prompts, and HUD rendering with zero
environment image dependencies.
"""

import math
import random
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import pygame

from src.core import settings
from src.world.camera import Camera
from src.entities.player import Player
from src.entities.npc import NPC
from src.maps.block_map import BlockMap
from src.hazards.base_hazard import BaseHazard
from src.core.decision_system import DecisionSystem, Decision
from src.core.score_system import ScoreSystem
from src.ui.legend_screen import LegendScreen
from src.ui.pause_menu import PauseMenu
from src.ui import theme
from src.config.palette import (
    COLOR_UI_PANEL,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)
from src.ui.text_utils import (
    measure_text,
    wrap_text as tu_wrap,
    ellipsize,
    draw_wrapped,
    line_height,
    clamp_rect,
)
# Hard-coded world/pickup sprites live in src/entities/world_art.py so the
# block map can share the exact same art. Re-exported here so levels can keep
# importing ICONS/icon_surface/draw_icon from this module.
from src.entities.world_art import (
    PALETTE,
    DIM_OUTLINE,
    DIM_FILL,
    ICONS,
    INTERACTABLE_ART,
    ITEM_ART,
    interactable_art_name,
    item_art_name,
    icon_surface,
    draw_icon,
)


# ======================================================================
# Pixel-game toolkit (icons, effects, mini-games). Everything is drawn in
# code, so no image files or extra modules are needed.
# ======================================================================

# The icon grids, the palette and the sprite helpers now live in
# src/entities/world_art.py and are imported at the top of this file.


def draw_sparkle(surface: pygame.Surface, x: int, y: int,
                 color: Tuple[int, int, int] = (255, 245, 170)) -> None:
    """Tiny plus-shaped twinkle (5 pixels)."""
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        surface.fill(color, (x + dx, y + dy, 1, 1))


# ----------------------------------------------------------------------
# UI pieces
# ----------------------------------------------------------------------
def draw_panel(surface: pygame.Surface, rect, fill, border, accent=None) -> None:
    """Pixel panel: 2px border, notched corners and a hard drop shadow."""
    r = pygame.Rect(rect)
    shadow = (8, 6, 10)
    for rr in (r.inflate(-4, 0), r.inflate(0, -4)):
        pygame.draw.rect(surface, shadow, rr.move(2, 2))
    for rr in (r.inflate(-4, 0), r.inflate(0, -4)):
        pygame.draw.rect(surface, border, rr)
    pygame.draw.rect(surface, fill, r.inflate(-4, -4))
    if accent is not None:
        pygame.draw.rect(surface, accent, r.inflate(-8, -8), 1)


def draw_bar(surface: pygame.Surface, rect, ratio: float, color,
             back=(18, 20, 26), border=(90, 84, 70), seg: int = 5, gap: int = 1) -> None:
    """Segmented pixel progress bar."""
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, back, r)
    pygame.draw.rect(surface, border, r, 1)
    inner = r.inflate(-4, -4)
    n = max(1, inner.w // (seg + gap))
    filled = int(round(n * max(0.0, min(1.0, ratio))))
    for i in range(n):
        x = inner.x + i * (seg + gap)
        col = color if i < filled else (34, 38, 46)
        pygame.draw.rect(surface, col, (x, inner.y, seg, inner.h))


# ----------------------------------------------------------------------
# Animated tile effects (drawn in screen space)
# ----------------------------------------------------------------------
def draw_flames(surface: pygame.Surface, rect, t: float) -> None:
    """Flickering pixel flames filling *rect* (3 colour layers)."""
    r = pygame.Rect(rect)
    col_w = 4
    for i, x in enumerate(range(r.left, r.right, col_w)):
        wobble = 0.5 * math.sin(t * 7 + i * 1.9) + 0.5 * math.sin(t * 3.1 + i * 0.7)
        h = int(r.h * (0.58 + 0.34 * wobble)) // 2 * 2
        h = max(6, min(r.h, h))
        w = min(col_w, r.right - x)
        base = r.bottom
        pygame.draw.rect(surface, (200, 40, 30), (x, base - h, w, h))
        h2 = int(h * 0.72)
        pygame.draw.rect(surface, (245, 130, 30), (x, base - h2, w, h2))
        h3 = int(h * 0.42)
        pygame.draw.rect(surface, (255, 215, 80), (x, base - h3, w, h3))


def draw_charred(surface: pygame.Surface, rect, t: float) -> None:
    """Burnt ground with a few glowing embers (a put-out fire)."""
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, (34, 30, 32), r)
    rnd = random.Random(7)
    for _ in range(max(6, r.w * r.h // 90)):
        x = rnd.randrange(r.left, max(r.left + 1, r.right - 3))
        y = rnd.randrange(r.top, max(r.top + 1, r.bottom - 2))
        pygame.draw.rect(surface, (20, 18, 20), (x, y, 3, 2))
    for k in range(5):
        x = rnd.randrange(r.left, max(r.left + 1, r.right - 2))
        y = rnd.randrange(r.top, max(r.top + 1, r.bottom - 1))
        if int(t * 2 + k) % 3 == 0:
            pygame.draw.rect(surface, (160, 64, 30), (x, y, 2, 1))


def draw_water(surface: pygame.Surface, rect, t: float,
               alpha: int = 110, color=(40, 100, 170),
               foam: bool = False, depth: bool = False,
               shore: bool = False) -> None:
    """Translucent water with drifting pixel highlights.

    ``foam`` adds a wavy surface line, ``depth`` adds shallow-to-deep
    bands and ``shore`` draws a jagged, rising pixel shoreline at the top
    edge (used by flood levels that advance from the south). All new
    options are off by default, so existing callers render as before.
    """
    r = pygame.Rect(rect)
    if r.w <= 0 or r.h <= 0:
        return
    layer = pygame.Surface(r.size, pygame.SRCALPHA)

    def shoreline_y(x: int) -> int:
        if not shore:
            return 0
        wave = (math.sin(x * 0.055 + t * 2.4) * 2.3
                + math.sin(x * 0.017 - t * 1.3) * 1.4)
        return int(max(0, min(max(0, r.h - 2), round(wave))))

    if shore:
        # Draw the body one 2px pixel row at a time so the top edge is a
        # wavy shoreline instead of a hard rectangle.
        for x in range(r.w):
            top = shoreline_y(x)
            pygame.draw.rect(layer, (*color, alpha), (x, top, 1, r.h - top))
    else:
        layer.fill((*color, alpha))

    # Depth bands: shallow at the surface, darker towards the bottom.
    if depth and r.h > 12:
        for dy in range(r.h // 3, r.h, 2):
            frac = (dy - r.h // 3) / max(1.0, r.h - r.h // 3)
            dark_a = min(120, int(frac * 90))
            pygame.draw.rect(layer, (15, 30, 65, dark_a), (0, dy, r.w, 2))

    for row, y in enumerate(range(2, r.h, 6)):
        start = (row * 5 + int(t * 12)) % 14
        for x in range(start - 14, r.w, 14):
            pygame.draw.rect(layer, (170, 215, 245, 170), (x, y, 6, 1))

    # Wavy foam on the shoreline edge.
    if foam and r.w > 0:
        for fx in range(0, r.w, 4):
            fy = shoreline_y(fx) if shore else int(math.sin(fx * 0.15 + t * 4.0) * 1.5)
            fy = max(0, min(r.h - 1, fy))
            pygame.draw.rect(layer, (230, 245, 255, 220), (fx, fy, 4, 1))
            if shore and (fx // 4) % 3 == 0:
                pygame.draw.rect(layer, (190, 225, 245, 150),
                                 (fx + 1, min(r.h - 1, fy + 2), 2, 1))

    surface.blit(layer, r.topleft)


def draw_wading_ripples(surface: pygame.Surface, camera, player_rect: pygame.Rect, t: float) -> None:
    """Draw expanding circular pixel water ripples around player feet when wading."""
    p_screen = camera.apply(player_rect)
    cx, cy = p_screen.centerx, p_screen.bottom - 2
    for i in range(2):
        phase = (t * 2.2 + i * 0.5) % 1.0
        rad_x = int(3 + phase * 7)
        rad_y = int(2 + phase * 3)
        alpha = int((1.0 - phase) * 180)
        if alpha > 15 and rad_x > 2:
            rip_surf = pygame.Surface((rad_x * 2 + 2, rad_y * 2 + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(rip_surf, (210, 240, 255, alpha), rip_surf.get_rect(), 1)
            surface.blit(rip_surf, (cx - rad_x, cy - rad_y))


def draw_cracks(surface: pygame.Surface, camera, polylines: Iterable[Sequence[Tuple[int, int]]]) -> None:
    """Jagged ground cracks given as world-space point lists."""
    for pts in polylines:
        sp = [camera.apply(pygame.Rect(int(x), int(y), 1, 1)).topleft for x, y in pts]
        if len(sp) >= 2:
            pygame.draw.lines(surface, (22, 18, 20), False, sp, 2)
            pygame.draw.lines(surface, (90, 80, 72), False, [(x, y - 1) for x, y in sp], 1)


def draw_drain(surface: pygame.Surface, center: Tuple[int, int], probed: bool, t: float) -> None:
    """Open storm drain; blinks a red '!' until it has been probed."""
    cx, cy = center
    pygame.draw.ellipse(surface, (12, 14, 20), (cx - 8, cy - 4, 16, 8))
    pygame.draw.ellipse(surface, (60, 70, 90), (cx - 8, cy - 4, 16, 8), 1)
    if probed:
        for dx in (-4, 0, 4):
            surface.fill((90, 220, 120), (cx + dx - 1, cy - 1, 2, 2))
    elif int(t * 2) % 2 == 0:
        surface.fill((220, 60, 50), (cx - 1, cy - 13, 2, 5))
        surface.fill((220, 60, 50), (cx - 1, cy - 6, 2, 2))


class ParticleField:
    """Screen-space ambient particles that wrap around the canvas."""

    CONFIG = {
        "embers": dict(count=34, size=(2, 3), color=(255, 150, 40), alpha=(150, 255),
                       vx=(-8, 8), vy=(-55, -22), sway=10),
        "smoke": dict(count=16, size=(14, 28), color=(26, 24, 28), alpha=(30, 62),
                      vx=(4, 16), vy=(-14, -5), sway=6),
        "rain": dict(count=110, size=(5, 8), color=(170, 190, 235), alpha=(255, 255),
                     vx=(-60, -60), vy=(230, 300), sway=0),
        "dust": dict(count=26, size=(1, 2), color=(205, 195, 170), alpha=(120, 220),
                     vx=(-6, 6), vy=(18, 46), sway=5),
    }

    def __init__(self, kind: str, size: Tuple[int, int] = (640, 360),
                 seed=None, count=None):
        self.kind = kind
        self.cfg = self.CONFIG[kind]
        self.size = size
        self._rnd = random.Random(seed)
        self._t = 0.0
        self._layer = None
        self.particles: List[dict] = [
            self._spawn(initial=True) for _ in range(count or self.cfg["count"])
        ]

    def _spawn(self, initial: bool = False) -> dict:
        c, rnd = self.cfg, self._rnd
        W, H = self.size
        size = rnd.randint(*c["size"])
        vy = rnd.uniform(*c["vy"])
        if initial:
            y = rnd.uniform(0, H)
        else:
            y = H + size if vy < 0 else -size
        return dict(
            x=rnd.uniform(-40, W + 120), y=y,
            vx=rnd.uniform(*c["vx"]), vy=vy, size=size,
            alpha=rnd.randint(*c["alpha"]), phase=rnd.uniform(0, 6.28),
        )

    def update(self, dt: float) -> None:
        self._t += dt
        W, H = self.size
        sway = self.cfg["sway"]
        for i, p in enumerate(self.particles):
            p["x"] += (p["vx"] + sway * math.sin(self._t * 2 + p["phase"])) * dt
            p["y"] += p["vy"] * dt
            s = p["size"]
            if p["y"] < -s - 6 or p["y"] > H + s + 6 or p["x"] < -60 or p["x"] > W + 140:
                self.particles[i] = self._spawn()

    def draw(self, surface: pygame.Surface) -> None:
        if self.kind == "rain":
            col = self.cfg["color"]
            for p in self.particles:
                x, y = int(p["x"]), int(p["y"])
                pygame.draw.line(surface, col, (x, y), (x + 2, y - p["size"]), 1)
            return
        if self._layer is None or self._layer.get_size() != surface.get_size():
            self._layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self._layer.fill((0, 0, 0, 0))
        r, g, b = self.cfg["color"]
        for p in self.particles:
            s = p["size"]
            pygame.draw.rect(self._layer, (r, g, b, p["alpha"]), (int(p["x"]), int(p["y"]), s, s))
        surface.blit(self._layer, (0, 0))


class Vignette:
    """Stepped (pixel-banded) tint around the screen edges."""

    def __init__(self, size: Tuple[int, int] = (640, 360), color=(120, 10, 0),
                 max_alpha: int = 150, bands: int = 14, step: int = 5):
        self.color = color
        self.max_alpha = max_alpha
        self.bands = bands
        self.step = step
        self._surf = None

    def _build(self, size: Tuple[int, int]) -> None:
        w, h = size
        surf = pygame.Surface(size, pygame.SRCALPHA)
        for i in range(self.bands):
            inset = i * self.step
            alpha = int(self.max_alpha * ((self.bands - i) / self.bands) ** 2)
            pygame.draw.rect(surf, (*self.color, alpha),
                             (inset, inset, w - 2 * inset, h - 2 * inset), self.step)
        self._surf = surf

    def draw(self, surface: pygame.Surface, strength: float = 1.0) -> None:
        if self._surf is None or self._surf.get_size() != surface.get_size():
            self._build(surface.get_size())
        self._surf.set_alpha(int(255 * max(0.0, min(1.0, strength))))
        surface.blit(self._surf, (0, 0))


class Darkness:
    """Blackout overlay with a soft, pixel-banded light circle."""

    def __init__(self, size: Tuple[int, int] = (640, 360), color=(4, 6, 18), alpha: int = 160):
        self.size = size
        self.color = color
        self.alpha = alpha
        self._layer = None

    def draw(self, surface: pygame.Surface, center: Tuple[int, int],
             radius: int, steps: int = 9) -> None:
        if self._layer is None or self._layer.get_size() != surface.get_size():
            self._layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        a = int(self.alpha)
        self._layer.fill((*self.color, a))
        for i in range(steps):
            r = max(1, int(radius * (1 - i / steps)))
            aa = int(a * (r / radius) ** 1.6)
            pygame.draw.circle(self._layer, (*self.color, aa), center, r)
        surface.blit(self._layer, (0, 0))


class LightningFlash:
    """Random white flashes (storm)."""

    def __init__(self, interval: Tuple[float, float] = (7.0, 14.0), seed=None):
        self._rnd = random.Random(seed)
        self.interval = interval
        self._timer = self._rnd.uniform(*interval)
        self.flash = 0.0
        self._layer = None

    def update(self, dt: float) -> None:
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self._rnd.uniform(*self.interval)
            self.flash = 1.0
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt * 3.0)

    def draw(self, surface: pygame.Surface) -> None:
        if self.flash <= 0:
            return
        if self._layer is None or self._layer.get_size() != surface.get_size():
            self._layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self._layer.fill((255, 255, 255, int(110 * self.flash)))
        surface.blit(self._layer, (0, 0))


class FlyingDebris:
    """Roof sheets that sweep across a lane inside *zone* (world coordinates).

    A red '!' and a dashed lane warn the player ``warn`` seconds before each
    sheet appears. ``hits(rect)`` reports contact with any live sheet.
    """

    SHEET_W, SHEET_H = 24, 7

    def __init__(self, zone, interval: Tuple[float, float] = (2.6, 4.2),
                 speed: float = 130.0, warn: float = 0.9, seed=None):
        self.zone = pygame.Rect(zone)
        self.interval = interval
        self.speed = speed
        self.warn = warn
        self._rnd = random.Random(seed)
        self._timer = self._rnd.uniform(*interval)
        self.sheets: List[dict] = []
        self.warnings: List[dict] = []
        self._t = 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self._rnd.uniform(*self.interval)
            lane_y = self._rnd.randint(self.zone.top, max(self.zone.top, self.zone.bottom - self.SHEET_H))
            self.warnings.append({"y": lane_y, "dir": self._rnd.choice((-1, 1)), "t": self.warn})
        for wn in self.warnings[:]:
            wn["t"] -= dt
            if wn["t"] <= 0:
                self.warnings.remove(wn)
                x = self.zone.left - 30 if wn["dir"] > 0 else self.zone.right + 30
                self.sheets.append({"x": float(x), "y": wn["y"], "dir": wn["dir"]})
        for s in self.sheets[:]:
            s["x"] += s["dir"] * self.speed * dt
            if s["x"] < self.zone.left - 60 or s["x"] > self.zone.right + 60:
                self.sheets.remove(s)

    def rects(self) -> List[pygame.Rect]:
        return [pygame.Rect(int(s["x"]), s["y"], self.SHEET_W, self.SHEET_H) for s in self.sheets]

    def hits(self, rect: pygame.Rect) -> bool:
        return any(rect.colliderect(r) for r in self.rects())

    def draw(self, surface: pygame.Surface, camera) -> None:
        blink = int(self._t * 8) % 2 == 0
        for wn in self.warnings:
            lane = camera.apply(pygame.Rect(self.zone.left, wn["y"], self.zone.w, self.SHEET_H))
            for x in range(lane.left, lane.right, 8):
                surface.fill((200, 60, 50), (x, lane.centery, 4, 1))
            if blink:
                ex = lane.left + 2 if wn["dir"] > 0 else lane.right - 5
                surface.fill((230, 70, 60), (ex, lane.centery - 6, 3, 7))
                surface.fill((230, 70, 60), (ex, lane.centery + 3, 3, 2))
        for s in self.sheets:
            r = camera.apply(pygame.Rect(int(s["x"]), s["y"], self.SHEET_W, self.SHEET_H))
            trail = r.move(-s["dir"] * 5, 0)
            pygame.draw.rect(surface, (110, 116, 128), trail)
            pygame.draw.rect(surface, (160, 166, 178), r)
            for x in range(r.left + 2, r.right, 4):
                pygame.draw.line(surface, (110, 116, 128), (x, r.top), (x, r.bottom - 1))
            pygame.draw.rect(surface, (24, 22, 32), r, 1)


class MiniGame:
    PANEL_W = 250
    PANEL_H = 96
    END_DELAY = 0.8

    def __init__(self, title: str, hint: str, icon: Optional[str] = None,
                 footer: str = "[SPACE]", win_text: str = "SUCCESS!",
                 fail_text: str = "TRY AGAIN!"):
        self.title = title
        self.hint = hint
        self.icon = icon
        self.footer = footer
        self.win_text = win_text
        self.fail_text = fail_text
        self.state = "playing"     # playing | won | lost
        self.end_timer = 0.0
        self.t = 0.0
        self.kick = 0.0            # tiny shake after each press

    # -- state ---------------------------------------------------------
    @property
    def finished(self) -> bool:
        return self.state != "playing" and self.end_timer <= 0

    @property
    def success(self) -> bool:
        return self.state == "won"

    def _finish(self, won: bool) -> None:
        self.state = "won" if won else "lost"
        self.end_timer = self.END_DELAY

    def update(self, dt: float) -> None:
        self.t += dt
        self.kick = max(0.0, self.kick - dt)
        if self.state == "playing":
            self._tick(dt)
        elif self.end_timer > 0:
            self.end_timer -= dt

    def press(self) -> None:
        if self.state == "playing":
            self.kick = 0.12
            self._on_press()

    # -- hooks for subclasses -----------------------------------------
    def _tick(self, dt: float) -> None:
        pass

    def _on_press(self) -> None:
        pass

    def current_hint(self) -> str:
        return self.hint

    def _draw_body(self, surface: pygame.Surface, rect: pygame.Rect, meter: pygame.Rect) -> None:
        pass

    # -- drawing -------------------------------------------------------
    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        draw_panel(surface, rect, COLOR_UI_PANEL, COLOR_UI_BORDER)
        pad = 8
        jitter = 1 if self.kick > 0 and int(self.t * 40) % 2 == 0 else 0

        tx = rect.x + pad
        if self.icon:
            surface.blit(icon_surface(self.icon, 1), (tx + jitter, rect.y + 6))
            tx += 14
        theme.draw_text(
            surface, ellipsize(self.title, "small", rect.right - pad - tx),
            (tx, rect.y + 7), size="small", color=COLOR_UI_ACCENT,
            shadow=True, anchor="topleft",
        )

        lh = line_height("tiny")
        y = rect.y + 22
        for ln in tu_wrap(self.current_hint(), "tiny", rect.w - pad * 2)[:2]:
            theme.draw_text(surface, ln, (rect.x + pad, y), size="tiny",
                            color=COLOR_UI_TEXT, shadow=False, anchor="topleft")
            y += lh + 1

        meter = pygame.Rect(rect.x + pad + 2, rect.y + 50, rect.w - (pad + 2) * 2, 14)
        self._draw_body(surface, rect, meter)

        if self.state == "playing":
            if int(self.t * 2) % 2 == 0:
                theme.draw_text(surface, self.footer, (rect.centerx, rect.bottom - 14),
                                size="tiny", color=COLOR_UI_ACCENT, shadow=False, anchor="midtop")
        else:
            pygame.draw.rect(surface, (10, 12, 16), meter)
            pygame.draw.rect(surface, COLOR_UI_BORDER, meter, 1)
            won = self.state == "won"
            theme.draw_text(
                surface, self.win_text if won else self.fail_text, meter.center,
                size="small", color=COLOR_UI_SAFE if won else COLOR_UI_DANGER,
                shadow=True, anchor="center",
            )


class TimingMeter(MiniGame):
    """Press SPACE while the marker is inside the green zone."""

    def __init__(self, title: str, hint: str, rounds: int = 3, speed: float = 0.9,
                 zone: float = 0.24, max_misses: int = 3,
                 steps: Optional[Sequence[str]] = None, **kw):
        kw.setdefault("footer", "[SPACE] Stop in the green zone")
        super().__init__(title, hint, **kw)
        self.steps = list(steps) if steps else None
        self.rounds = len(self.steps) if self.steps else rounds
        self.speed = speed
        self.zone_w = zone
        self.max_misses = max_misses
        self.pos = 0.0
        self.dir = 1
        self.hits = 0
        self.misses = 0
        self.zone_c = 0.5
        self.flash = 0.0
        self.flash_good = True
        self._new_zone()

    def _new_zone(self) -> None:
        half = self.zone_w / 2
        self.zone_c = random.uniform(0.12 + half, 0.88 - half)

    def current_hint(self) -> str:
        if self.steps:
            return f"{min(self.hits + 1, self.rounds)}/{self.rounds}: {self.steps[min(self.hits, self.rounds - 1)]}"
        return self.hint

    def _tick(self, dt: float) -> None:
        self.pos += self.dir * self.speed * dt
        if self.pos >= 1.0:
            self.pos, self.dir = 1.0, -1
        elif self.pos <= 0.0:
            self.pos, self.dir = 0.0, 1
        self.flash = max(0.0, self.flash - dt)

    def in_zone(self) -> bool:
        return abs(self.pos - self.zone_c) <= self.zone_w / 2

    def _on_press(self) -> None:
        if self.in_zone():
            self.hits += 1
            self.flash, self.flash_good = 0.25, True
            if self.hits >= self.rounds:
                self._finish(True)
            else:
                self._new_zone()
                self.speed *= 1.08
        else:
            self.misses += 1
            self.flash, self.flash_good = 0.25, False
            if self.misses >= self.max_misses:
                self._finish(False)

    def _draw_body(self, surface, rect, meter) -> None:
        pygame.draw.rect(surface, (18, 20, 26), meter)
        inner = meter.inflate(-4, -4)
        zx = inner.x + int((self.zone_c - self.zone_w / 2) * inner.w)
        zw = max(4, int(self.zone_w * inner.w))
        zone_col = (110, 230, 140) if (self.flash > 0 and self.flash_good) else (60, 170, 90)
        pygame.draw.rect(surface, zone_col, (zx, inner.y, zw, inner.h))
        for i in range(1, 10):
            surface.fill((50, 56, 66), (inner.x + i * inner.w // 10, inner.y, 1, 3))
        mx = inner.x + int(self.pos * inner.w)
        marker_col = (255, 110, 100) if (self.flash > 0 and not self.flash_good) else (245, 245, 240)
        pygame.draw.rect(surface, marker_col, (mx - 1, meter.y, 3, meter.h))
        pygame.draw.rect(surface, COLOR_UI_BORDER, meter, 1)

        # progress pips + misses
        px = rect.x + 12
        for i in range(self.rounds):
            r = pygame.Rect(px + i * 10, rect.y + 69, 7, 7)
            if i < self.hits:
                pygame.draw.rect(surface, (90, 220, 120), r)
            pygame.draw.rect(surface, COLOR_UI_BORDER, r, 1)
        theme.draw_text(
            surface, f"MISS {self.misses}/{self.max_misses}",
            (rect.right - 10, rect.y + 68), size="tiny",
            color=COLOR_UI_DANGER if self.misses else COLOR_UI_TEXT,
            shadow=False, anchor="topright",
        )


class Mash(MiniGame):
    """Mash SPACE to fill the bar; the bar drains and the clock runs."""

    def __init__(self, title: str, hint: str, target: int = 20, decay: float = 2.4,
                 time_limit: float = 9.0, **kw):
        kw.setdefault("footer", "[SPACE] Mash!")
        super().__init__(title, hint, **kw)
        self.target = float(target)
        self.decay = decay
        self.time_limit = time_limit
        self.time_left = time_limit
        self.value = 0.0

    def _tick(self, dt: float) -> None:
        self.value = max(0.0, self.value - self.decay * dt)
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0.0
            self._finish(False)

    def _on_press(self) -> None:
        self.value += 1.0
        if self.value >= self.target:
            self.value = self.target
            self._finish(True)

    def _draw_body(self, surface, rect, meter) -> None:
        draw_bar(surface, meter, self.value / self.target, (90, 200, 120), seg=6)
        ratio = self.time_left / self.time_limit if self.time_limit else 0
        color = COLOR_UI_DANGER if ratio < 0.25 else COLOR_UI_ACCENT
        bar = pygame.Rect(meter.x, rect.y + 69, meter.w, 7)
        draw_bar(surface, bar, ratio, color, seg=4)


class RadioTuning(MiniGame):
    """Tune emergency radio to target frequency (e.g., VHF Ch 16 - 156.80 MHz)."""

    def __init__(self, title: str = "EMERGENCY RADIO TUNER",
                 target_channel: str = "VHF CH 16 (156.8 MHz)",
                 speed: float = 1.05, zone: float = 0.22, rounds: int = 2,
                 max_misses: int = 3, **kw):
        kw.setdefault("hint", f"Lock onto distress frequency: {target_channel}")
        kw.setdefault("footer", "[SPACE] Lock Frequency in the green band")
        kw.setdefault("icon", "radio")
        super().__init__(title, **kw)
        self.target_channel = target_channel
        self.rounds = rounds
        self.hits = 0
        self.misses = 0
        self.max_misses = max_misses
        self.speed = speed
        self.pos = 0.0
        self.dir = 1
        self.zone_w = zone
        self.zone_c = 0.5
        self.flash = 0.0
        self.flash_good = True
        self._new_zone()

    def _new_zone(self) -> None:
        half = self.zone_w / 2
        self.zone_c = random.uniform(0.16 + half, 0.84 - half)

    def _tick(self, dt: float) -> None:
        self.pos += self.dir * self.speed * dt
        if self.pos >= 1.0:
            self.pos, self.dir = 1.0, -1
        elif self.pos <= 0.0:
            self.pos, self.dir = 0.0, 1
        self.flash = max(0.0, self.flash - dt)

    def in_zone(self) -> bool:
        return abs(self.pos - self.zone_c) <= self.zone_w / 2

    def _on_press(self) -> None:
        if self.in_zone():
            self.hits += 1
            self.flash, self.flash_good = 0.3, True
            if self.hits >= self.rounds:
                self._finish(True)
            else:
                self._new_zone()
                self.speed *= 1.15
        else:
            self.misses += 1
            self.flash, self.flash_good = 0.3, False
            if self.misses >= self.max_misses:
                self._finish(False)

    def _draw_body(self, surface: pygame.Surface, rect: pygame.Rect, meter: pygame.Rect) -> None:
        pygame.draw.rect(surface, (12, 16, 22), meter)
        inner = meter.inflate(-4, -4)

        # Radio frequency scale ticks
        for i in range(16):
            tx = inner.x + i * inner.w // 15
            th = 4 if i % 3 == 0 else 2
            surface.fill((45, 60, 80), (tx, inner.y, 1, th))

        # Clear signal band
        zx = inner.x + int((self.zone_c - self.zone_w / 2) * inner.w)
        zw = max(6, int(self.zone_w * inner.w))
        z_col = (80, 225, 140) if (self.flash > 0 and self.flash_good) else (40, 145, 85)
        pygame.draw.rect(surface, z_col, (zx, inner.y, zw, inner.h))

        # Frequency tuner needle
        nx = inner.x + int(self.pos * inner.w)
        needle_col = (255, 90, 80) if (self.flash > 0 and not self.flash_good) else (255, 230, 90)
        pygame.draw.rect(surface, needle_col, (nx - 1, meter.y - 1, 3, meter.h + 2))
        pygame.draw.rect(surface, COLOR_UI_BORDER, meter, 1)

        # Readout text
        status_txt = f"{self.target_channel} [LOCK {self.hits}/{self.rounds}]"
        theme.draw_text(
            surface, status_txt, (inner.x + 2, rect.y + 68), size="tiny",
            color=(100, 230, 160) if self.hits > 0 else COLOR_UI_ACCENT, shadow=False,
        )
        theme.draw_text(
            surface, f"MISS {self.misses}/{self.max_misses}",
            (rect.right - 10, rect.y + 68), size="tiny",
            color=COLOR_UI_DANGER if self.misses else COLOR_UI_TEXT,
            shadow=False, anchor="topright",
        )


class BaseLevel:
    def __init__(
        self,
        game,
        chapter_id: str,
        level_id: str,
        title: str,
        subtitle: str,
        disaster_type: str,
        lesson_source: str,
        lesson_text: str,
    ):
        self.game = game
        self.chapter_id = chapter_id
        self.level_id = level_id
        self.title = title
        self.subtitle = subtitle
        self.disaster_type = disaster_type
        self.lesson_source = lesson_source
        self.lesson_text = lesson_text

        # Ensure session has score system
        if not hasattr(self.game.session, "score_system"):
            self.game.session.score_system = ScoreSystem()
        self.score_system: ScoreSystem = self.game.session.score_system
        self._score_start = self._score_counts()

        # Core systems
        self.decision_system = DecisionSystem(self.score_system)
        self.legend_screen = LegendScreen()
        self.pause_menu = PauseMenu(self.game)

        # Map & Camera (child level sets up self.block_map)
        self.block_map: Optional[BlockMap] = None
        self.camera = Camera(640, 360)

        # Entities
        char_choice = getattr(self.game.session, "character", "juan")
        walk_path = f"assets/images/characters/{char_choice}_walk.png"
        self.player = Player(100, 100, speed=80, walk_path=walk_path)
        self.npcs: List[NPC] = []
        self.hazards: List[BaseHazard] = []

        # Objective tracking
        self.objectives: List[str] = []
        self.current_objective_idx: int = 0
        self.completed: bool = False
        self.show_lesson_modal: bool = False
        # A level can finish on the last line of an important closing scene.
        # Hold the lesson until that dialogue closes so text is never covered.
        self._lesson_after_dialogue: bool = False
        self.guide_points: List[Any] = []

        # Repeat-visit tracking for short NPC reminders and one-shot steps.
        self._npc_visits: Dict[int, int] = {}
        self._step_marked: set = set()

        # Active dialogue state
        self.active_dialogue: Optional[List[str]] = None
        self.dialogue_speaker: str = ""
        self.dialogue_idx: int = 0
        self._dialogue_chars: float = 0.0

        # Structured quest steps + current target
        self._steps: List[Dict[str, Any]] = []
        self._current_step_idx: int = 0

        # Decision feedback line on retry
        self._last_decision_feedback: str = ""

        # On-screen hint banner (used by tutorial / guidance messages)
        self.hint_text: str = ""
        self.hint_timer: float = 0.0

        # Interactable objects / zones (boards, radios, drains, safe zones...)
        self.interactables: List[Dict[str, Any]] = []

        # Overlay boards registered during a draw pass (quest board, hint,
        # dialogue, decision, lesson modal...) so they stay dominant over
        # world labels. Reset at the start of every draw().
        self._board_registrations: List[Any] = []

        # Queued decision (opens after dialogue closes), countdown, danger zones
        self._queued_decision = None
        self.countdown_active: bool = False
        self.countdown_time: float = 0.0
        self.countdown_label: str = ""
        self.countdown_on_expire = None
        self._zone_watches: List[Dict[str, Any]] = []

        # Quest board visibility (expands on new objective / when idle,
        # collapses to a small tab while the player is busy moving).
        self.obj_show_timer: float = self.OBJ_SHOW_TIME
        self.obj_pinned: bool = False
        self._last_obj_idx: int = 0
        self._idle_time: float = 0.0
        self._last_player_pos = None

        # Pixel-game systems: pickups + item tray, HUD meters, mini-games,
        # setbacks (hurt / respawn). All optional; levels opt in.
        self.level_time: float = 0.0
        self._anim_t: float = 0.0
        self.pickups: List[Dict[str, Any]] = []
        self.tray_slots: List[Dict[str, Any]] = []
        self.collected: set = set()
        self._pickup_fx: List[Dict[str, Any]] = []
        self.meters: Dict[str, Dict[str, Any]] = {}
        self.minigame: Optional[MiniGame] = None
        self._minigame_win = None
        self._minigame_fail = None
        self.checkpoint = None
        self.hurt_flash: float = 0.0
        self.invuln: float = 0.0
        self.setbacks: int = 0
        self._jolt: float = 0.0

    # ------------------------------------------------------------------
    # Reusable level helpers
    # ------------------------------------------------------------------
    @staticmethod
    def is_safe_option(opt) -> bool:
        if isinstance(opt, dict):
            return bool(opt.get("safe", False))
        return bool(getattr(opt, "safe", False))

    def _score_counts(self) -> Dict[str, int]:
        """Snapshot the campaign score counters so a mission can use deltas."""
        ss = self.score_system
        return {
            field: int(getattr(ss, field, 0))
            for field in ("warnings_followed", "unsafe_actions",
                          "residents_assisted", "evacuations_completed",
                          "supplies_secured")
        }

    def _item_counts(self) -> Tuple[int, int]:
        """Return (found, total) collectibles for this mission."""
        found = len(self.collected)
        total = len(self.pickups)
        if self.block_map is not None:
            found += sum(1 for item in self.block_map.items if getattr(item, "collected", False))
            total += len(self.block_map.items)
        return found, total

    def build_run_stats(self) -> Dict[str, Any]:
        """Build the mission result used by the local/DB leaderboards."""
        start = getattr(self, "_score_start", self._score_counts())
        now = self._score_counts()
        warnings = max(0, now["warnings_followed"] - start["warnings_followed"])
        unsafe = max(0, now["unsafe_actions"] - start["unsafe_actions"])
        assisted = max(0, now["residents_assisted"] - start["residents_assisted"])

        quests_total = len(self.objectives)
        quests_done = min(self.current_objective_idx, quests_total)
        objective_rate = quests_done / max(1, quests_total)
        items_found, items_total = self._item_counts()
        item_rate = items_found / max(1, items_total)
        time_s = int(self.level_time)

        # Same transparent, capped categories documented in the README.
        objective_points = round(400 * objective_rate)
        supply_points = round(200 * item_rate)
        decision_points = max(0, min(200, 100 + min(100, warnings * 25) - unsafe * 50))
        response_points = max(0, round(100 - time_s * 0.35))
        safety_points = max(0, round(100 - self.setbacks * 8))
        rescue_points = min(200, assisted * 100)
        score = (objective_points + supply_points + decision_points
                 + response_points + safety_points + rescue_points)

        return {
            "time": time_s,
            "score": int(score),
            "max_score": 1200,
            "damage": int(self.setbacks),
            "quests_done": int(quests_done),
            "quests_total": int(quests_total),
            "items_found": int(items_found),
            "items_total": int(items_total),
            "rescues": int(assisted),
            "warnings_followed": int(warnings),
            "unsafe_actions": int(unsafe),
            "completed": True,
            "perfect": (self.setbacks == 0 and unsafe == 0
                        and quests_done >= quests_total and items_found >= items_total),
        }

    def _record_run(self) -> None:
        """Publish this mission's result to the leaderboards."""
        session = getattr(self.game, "session", None)
        if session is None:
            return
        from src.story.chapter_registry import mission_key
        try:
            session.record_run(mission_key(self.chapter_id, self.level_id), self.build_run_stats())
        except Exception as exc:  # never block story progression on a score write
            print(f"[BayanSafe] Could not record mission run: {exc}")

    def record_score(self, field: str, amount: int = 1):
        """Best-effort score update (works with several ScoreSystem styles)."""
        ss = self.score_system
        for name in ("record", "add", "increment"):
            fn = getattr(ss, name, None)
            if callable(fn):
                try:
                    fn(field, amount)
                    return
                except Exception:  # noqa: BLE001
                    pass
        if hasattr(ss, field):
            setattr(ss, field, getattr(ss, field) + amount)

    def queue_decision(self, builder):
        """Open a decision as soon as dialogue/other decisions are closed.

        builder: a function that returns a Decision.
        """
        self._queued_decision = builder

    def ask(self, decision_id: str, prompt: str, options: list, on_safe, retry_hint: str = "Not quite. Think again."):
        """Ask a safe/unsafe question. The unsafe answer shows its lesson and
        asks again; the safe answer calls on_safe()."""

        def builder():
            def on_decide(opt):
                if self.is_safe_option(opt):
                    self._last_decision_feedback = ""
                    on_safe()
                else:
                    lesson = opt.get("lesson", "") if isinstance(opt, dict) else getattr(opt, "lesson", "")
                    feedback = lesson or retry_hint
                    self._last_decision_feedback = feedback
                    self.show_hint(feedback, 4.0)
                    self.queue_decision(builder)

            return Decision(
                decision_id=decision_id,
                prompt=prompt,
                options=options,
                on_resolved=on_decide,
            )

        self.queue_decision(builder)

    def set_steps(self, steps: List[Dict[str, Any]]) -> None:
        """Configure structured quest steps.
        Each step dict:
          - 'text': str (objective text)
          - 'done': callable -> bool
          - 'hint': Optional[str] (hint shown when step becomes active)
          - 'target': Optional[callable or tuple/Rect] (world coordinates for bobbing arrow)
        """
        self._steps = steps
        self._current_step_idx = 0
        self.objectives = [s["text"] for s in steps]
        self.current_objective_idx = 0
        # Every structured step carries a target; mirror them into the shared
        # guide-point list so the same bobbing arrow is used in every mission.
        self.guide_points = [s.get("target") for s in steps]
        if steps and steps[0].get("hint"):
            self.show_hint(steps[0]["hint"], 5.0)

    def restore_progress(self) -> bool:
        """Restore only the saved quest position of a resumed mission.

        All levels construct their own world first; this keeps that world
        intact and simply moves the single active objective marker.
        """
        session = getattr(self.game, "session", None)
        if session is None or not session.consume_level_resume():
            return False
        if not session.has_level_progress(self.chapter_id, self.level_id):
            return False
        progress = session.current_level
        idx = max(0, min(len(self.objectives),
                         int(progress.get("current_objective_idx", 0))))
        self.current_objective_idx = idx
        self._current_step_idx = idx if self._steps else 0
        self._step_marked = set(range(idx))
        self._last_obj_idx = idx
        self.obj_show_timer = self.OBJ_SHOW_TIME
        if idx < len(self._steps) and self._steps[idx].get("hint"):
            self.show_hint(self._steps[idx]["hint"], 4.5)
        return True

    def start_countdown(self, seconds: float, label: str, on_expire=None):
        self.countdown_active = True
        self.countdown_time = seconds
        self.countdown_label = label
        self.countdown_on_expire = on_expire

    def stop_countdown(self):
        self.countdown_active = False

    def watch_zone(self, rect: tuple, on_enter):
        """Call on_enter() once each time the player steps into rect."""
        self._zone_watches.append({"rect": pygame.Rect(rect), "inside": False, "on_enter": on_enter})

    def add_interactable(
        self,
        key: str,
        label: str,
        rect: tuple,
        color: tuple,
        on_interact=None,
        prompt: bool = True,
        alpha: int = 0,
    ) -> Dict[str, Any]:
        """Add a colored block the player can walk up to and press SPACE on.

        key:         unique name, e.g. "drain"
        rect:        (x, y, w, h) in world coordinates
        on_interact: function(item) called when the player presses SPACE nearby
        prompt:      show the "[SPACE]" prompt when near (False for plain zones)
        alpha:       0 = solid block, 1-255 = translucent zone
        """
        item = {
            "key": key,
            "label": label,
            "rect": pygame.Rect(rect),
            "color": color,
            "on_interact": on_interact,
            "prompt": prompt,
            "alpha": alpha,
            "done": False,
        }
        self.interactables.append(item)
        return item

    def _near_interactable(self, item: Dict[str, Any]) -> bool:
        return self.player.rect.colliderect(item["rect"].inflate(24, 24))

    def show_hint(self, text: str, duration: float = 4.5):
        """Show a short hint banner under the objective for `duration` seconds."""
        self.hint_text = text
        self.hint_timer = duration

    def guide_interactable(self, key: str):
        """Return a lazy guide target for an interactable (used by levels)."""
        def target():
            item = next((i for i in self.interactables if i.get("key") == key), None)
            return item["rect"].center if item else None
        return target

    def guide_pickup(self, key: str):
        """Return a lazy guide target for a pickup (used by levels)."""
        def target():
            item = next((i for i in self.pickups if i.get("key") == key), None)
            return item["rect"].center if item else None
        return target

    def guide_npc(self, name: str):
        """Return a lazy guide target for an NPC (used by levels)."""
        def target():
            npc = next((n for n in self.npcs if getattr(n, "name", "") == name), None)
            return npc.rect.midtop if npc else None
        return target

    # ------------------------------------------------------------------
    # Pixel-game helpers: pickups, meters, mini-games, setbacks, hooks
    # ------------------------------------------------------------------
    def is_busy(self) -> bool:
        """True while a dialogue, decision or mini-game has the player's focus."""
        return (
            self.decision_system.is_active()
            or self.active_dialogue is not None
            or self.minigame is not None
        )

    def add_pickup(self, key: str, label: str, pos: tuple, icon: str,
                   on_collect=None, tray: bool = True) -> Dict[str, Any]:
        """Add a collectible. Walk over it to pick it up.

        key:   unique id used with has_item(key)
        pos:   (x, y) world centre of the item
        icon:  name from src.ui.ICONS
        tray:  show it in the item tray (dim until collected)
        """
        item = {
            "key": key,
            "label": label,
            "icon": icon,
            "rect": pygame.Rect(int(pos[0]) - 6, int(pos[1]) - 6, 12, 12),
            "on_collect": on_collect,
            "got": False,
            "phase": len(self.pickups) * 1.3,
        }
        self.pickups.append(item)
        if tray:
            self.tray_slots.append({"key": key, "icon": icon, "label": label})
        return item

    def has_item(self, key: str) -> bool:
        return key in self.collected

    def _collect(self, item: Dict[str, Any]):
        item["got"] = True
        self.collected.add(item["key"])
        self._pickup_fx.append({"pos": item["rect"].center, "t": 0.6})
        self.show_hint(f"Got {item['label']}!", 2.5)
        if item["on_collect"]:
            item["on_collect"](item)

    def _update_pickups(self, dt: float):
        for fx in self._pickup_fx[:]:
            fx["t"] -= dt
            if fx["t"] <= 0:
                self._pickup_fx.remove(fx)
        if self.is_busy():
            return
        for item in self.pickups:
            if not item["got"] and self.player.rect.colliderect(item["rect"].inflate(8, 8)):
                self._collect(item)

    def set_meter(self, key: str, label: str, ratio: float, good_high: bool = True):
        """Show/update a HUD bar (top-right). good_high=False means a full bar is bad."""
        self.meters[key] = {
            "label": label,
            "ratio": max(0.0, min(1.0, float(ratio))),
            "good_high": good_high,
        }

    def clear_meter(self, key: str):
        self.meters.pop(key, None)

    def start_minigame(self, game: MiniGame, on_win=None, on_fail=None):
        """Run a short mini-game (TimingMeter or Mash, defined above); SPACE drives it."""
        self.minigame = game
        self._minigame_win = on_win
        self._minigame_fail = on_fail

    def set_checkpoint(self, pos: tuple):
        self.checkpoint = (int(pos[0]), int(pos[1]))

    def hurt(self, message: str = "", respawn: bool = False, penalty: float = 0.0) -> bool:
        """Setback: red flash + jolt, optional respawn at the checkpoint and
        optional seconds taken off a running countdown. Short invulnerability
        stops it from firing every frame. Returns False if ignored."""
        if self.invuln > 0 or self.completed:
            return False
        self.invuln = 1.2
        self.hurt_flash = 0.45
        self._jolt = 0.3
        self.setbacks += 1
        if penalty and self.countdown_active:
            self.countdown_time = max(1.0, self.countdown_time - penalty)
        if respawn and self.checkpoint is not None:
            cx, cy = self.checkpoint
            self.player.pos = pygame.Vector2(cx, cy)
            self.player.rect.topleft = (cx, cy)
        if message:
            self.show_hint(message, 3.5)
        return True

    # Per-level hooks (override in a level; defaults do nothing)
    def update_level(self, dt: float):
        pass

    def draw_under_player(self, surface: pygame.Surface):
        pass

    def draw_over_world(self, surface: pygame.Surface):
        pass

    def add_npc(self, char_id: str, name: str, pos: tuple, dialogue: List[str], role: str = ""):
        """Add an NPC with preserved character art walk-sheet."""
        npc_data = {
            "id": char_id,
            "name": name,
            "pos": pos,
            "color": (220, 180, 100),
            "dialogue": dialogue,
        }
        npc = NPC(npc_data)
        self.npcs.append(npc)
        return npc

    def _finish_dialogue(self) -> None:
        """Close the active dialogue and reveal a pending lesson safely."""
        self.active_dialogue = None
        self.dialogue_speaker = ""
        if self._lesson_after_dialogue:
            self._lesson_after_dialogue = False
            self.show_lesson_modal = True

    def handle_input(self, action: str) -> bool:
        """Process keyboard / game input."""
        # 1. Legend screen takes input if open
        if self.legend_screen.visible:
            return self.legend_screen.handle_input(action)

        if action == "legend":
            self.legend_screen.toggle()
            return True

        # Optional: pin/unpin the quest board (needs an "objective" action
        # mapped to a key in your input handler, e.g. TAB or O).
        if action == "objective":
            self.obj_pinned = not self.obj_pinned
            return True

        # 2. Stage completion lesson modal
        if self.show_lesson_modal:
            if action in ("confirm", "interact", "cancel", "escape"):
                self.proceed_to_next()
                return True
            return True

        # 3. Pause menu
        if self.pause_menu.visible:
            return self.pause_menu.handle_input(action, level=self)

        # 4. Escape / Pause key during normal gameplay
        if action in ("escape", "pause"):
            if self.active_dialogue is not None:
                # Close dialogue if talking
                self._finish_dialogue()
                return True
            self.pause_menu.show()
            return True

        # 4b. Mini-game takes SPACE presses
        if self.minigame is not None:
            if action in ("confirm", "interact", "space"):
                self.minigame.press()
            return True

        # 5. Decision system takes input if active
        if self.decision_system.is_active():
            return self.decision_system.handle_input(action)

        # 6. Dialogue progression
        if self.active_dialogue is not None:
            if action in ("confirm", "interact", "space"):
                if self.dialogue_idx < len(self.active_dialogue):
                    cur_line = self.active_dialogue[self.dialogue_idx]
                    if self._dialogue_chars < len(cur_line):
                        self._dialogue_chars = float(len(cur_line))
                        return True
                self.dialogue_idx += 1
                self._dialogue_chars = 0.0
                if self.dialogue_idx >= len(self.active_dialogue):
                    self._finish_dialogue()
                return True
            return True

        # 7. World interaction
        if action in ("confirm", "interact"):
            return self._try_interact()

        return False

    def _try_interact(self) -> bool:
        p_center = self.player.rect.center
        for npc in self.npcs:
            dx = npc.rect.centerx - p_center[0]
            dy = npc.rect.centery - p_center[1]
            if (dx * dx + dy * dy) <= (28 * 28):
                key = id(npc)
                visits = self._npc_visits.get(key, 0) + 1
                self._npc_visits[key] = visits
                # First visit plays the full introduction; later visits give
                # a short reminder matched to the current quest step. Level
                # hooks may still replace the dialogue with story-specific
                # lines (as several chapters do).
                lines = npc.dialogue if visits == 1 else self.npc_reminder_lines(npc)
                self.start_dialogue(npc.name, lines)
                self.on_npc_interacted(npc)
                return True

        for item in self.interactables:
            if item["prompt"] and item["on_interact"] and self._near_interactable(item):
                item["on_interact"](item)
                return True
        return False

    def on_npc_interacted(self, npc: NPC):
        pass

    def npc_reminder_lines(self, npc: NPC) -> List[str]:
        """Short, step-aware lines used after the first talk with an NPC."""
        step = ""
        if self.current_objective_idx < len(self.objectives):
            step = self.objectives[self.current_objective_idx]
            step = re.sub(r"^\[\d+/\d+\]\s*", "", step)
        name = getattr(npc, "name", "Friend")
        if step:
            return [
                f"{name}: Still need a hand? Right now we must: {step}",
                "Follow the gold arrow and I will help when you get there.",
            ]
        return [f"{name}: We made it. Follow the evacuation route to safety."]

    def require_step(self, index: int, hint: str = "") -> bool:
        """Return True when *index* is the active step.

        Early interaction gets a clear hint instead of failing silently.
        Levels call this before opening a panel or accepting a trigger.
        """
        if self.completed or int(index) == self.current_objective_idx:
            return True
        text = hint or "Finish first"
        if self.current_objective_idx < len(self.objectives):
            current = self.objectives[self.current_objective_idx]
            current = re.sub(r"^\[\d+/\d+\]\s*", "", current)
            text = f"{text}: {current}" if hint else f"Finish first: {current}"
        self.show_hint(text, 4.0)
        return False

    def start_dialogue(self, speaker: str, lines: List[str]):
        self.dialogue_speaker = speaker
        self.active_dialogue = lines
        self.dialogue_idx = 0
        self._dialogue_chars = 0.0

    def trigger_decision(self, decision: Decision):
        self.decision_system.trigger_decision(decision)

    def complete_objective(self, expected_idx: Optional[int] = None) -> bool:
        """Advance one quest step, at most once.

        ``expected_idx`` is an optional guard: when supplied, the step only
        advances if it is still the current one. This makes repeated calls
        from a single event harmless while keeping the old zero-argument
        API working for every level.
        """
        if self.completed:
            return False
        idx = self.current_objective_idx
        if idx >= len(self.objectives) or idx in self._step_marked:
            return False
        if expected_idx is not None and int(expected_idx) != idx:
            return False
        self._step_marked.add(idx)
        self.current_objective_idx = idx + 1
        session = getattr(self.game, "session", None)
        if session is not None:
            session.update_level_progress(current_objective_idx=self.current_objective_idx)
        if self.current_objective_idx >= len(self.objectives):
            self.complete_level()
        return True

    def complete_level(self):
        if self.completed:
            return
        self.completed = True
        self._record_run()
        if self.active_dialogue is not None:
            self._lesson_after_dialogue = True
        else:
            self.show_lesson_modal = True

    def proceed_to_next(self):
        from src.story.chapter_registry import advance_story
        advance_story(self.game, self.chapter_id, self.level_id)

    def update(self, dt: float):
        if self._lesson_after_dialogue and self.active_dialogue is None:
            self._lesson_after_dialogue = False
            self.show_lesson_modal = True

        if self.legend_screen.visible or self.show_lesson_modal or self.pause_menu.visible:
            return

        if self.hint_timer > 0:
            self.hint_timer -= dt

        # Timed pressure (water rise, surge meters, countdowns) only runs
        # during active play; animations keep ticking so overlays still live.
        if not self.is_busy():
            self.level_time += dt
        self._anim_t += dt
        self.hurt_flash = max(0.0, self.hurt_flash - dt)
        self.invuln = max(0.0, self.invuln - dt)
        self._jolt = max(0.0, self._jolt - dt)

        # Mini-game: tick it, then fire the win/fail callback when it ends
        if self.minigame is not None:
            self.minigame.update(dt)
            if self.minigame.finished:
                mg, self.minigame = self.minigame, None
                cb = self._minigame_win if mg.success else self._minigame_fail
                self._minigame_win = self._minigame_fail = None
                if cb:
                    cb()
                elif not mg.success:
                    self.show_hint("Try again!", 2.5)

        # Typewriter reveal for dialogue
        if self.active_dialogue is not None and self.dialogue_idx < len(self.active_dialogue):
            cur_line = self.active_dialogue[self.dialogue_idx]
            if self._dialogue_chars < len(cur_line):
                self._dialogue_chars = min(float(len(cur_line)), self._dialogue_chars + dt * 42.0)

        # Structured quest steps progression
        if self._steps:
            while self._current_step_idx < len(self._steps):
                check_fn = self._steps[self._current_step_idx].get("done")
                if check_fn and check_fn():
                    self._current_step_idx += 1
                    self.current_objective_idx = self._current_step_idx
                    session = getattr(self.game, "session", None)
                    if session is not None:
                        session.update_level_progress(
                            current_objective_idx=self.current_objective_idx,
                            current_step_idx=self._current_step_idx,
                        )
                    if self._current_step_idx >= len(self._steps):
                        self.complete_level()
                    elif self._steps[self._current_step_idx].get("hint"):
                        self.show_hint(self._steps[self._current_step_idx]["hint"], 4.5)
                else:
                    break

        self._update_objective_visibility(dt)

        # Open a queued decision once dialogue and other decisions are closed
        if (
            self._queued_decision
            and not self.decision_system.is_active()
            and self.active_dialogue is None
            and self.minigame is None
        ):
            builder, self._queued_decision = self._queued_decision, None
            self.trigger_decision(builder())

        # Countdown (pauses during dialogue and decisions)
        if (
            self.countdown_active
            and not self.decision_system.is_active()
            and self.active_dialogue is None
            and self.minigame is None
        ):
            self.countdown_time -= dt
            if self.countdown_time <= 0:
                self.countdown_active = False
                if self.countdown_on_expire:
                    self.countdown_on_expire()

        # Danger-zone watches (frozen while the player is reading a box)
        if not self.is_busy():
            for zw in self._zone_watches:
                inside = self.player.rect.colliderect(zw["rect"])
                if inside and not zw["inside"]:
                    zw["on_enter"]()
                zw["inside"] = inside

        self.decision_system.update(dt)

        # Player movement
        if (not self.decision_system.is_active() and self.active_dialogue is None
                and self.minigame is None):
            wind_push = pygame.Vector2(0, 0)
            for h in self.hazards:
                if hasattr(h, "get_wind_push"):
                    wind_push += h.get_wind_push()

            walls = self.block_map.collision_rects if self.block_map else []
            self.player.update(dt, walls=walls, push=wind_push)

            # Check item pickups
            if self.block_map:
                picked = self.block_map.check_item_pickup(self.player.rect)
                if picked:
                    if hasattr(self.game.session, "inventory"):
                        self.game.session.inventory.add_item(picked.item_id)
                    self.on_item_collected(picked.item_id)

            # Check triggers with generous collision bounds for safe zones / high ground
            if self.block_map:
                triggers = self.block_map.check_triggers(self.player.rect.inflate(12, 12))
                for tr in triggers:
                    self.on_trigger_activated(tr)

        # Pixel-game pickups and per-level logic
        self._update_pickups(dt)
        self.update_level(dt)

        # Timed hazards (rising water, debris) freeze during dialogue,
        # decisions and mini-games so reading can never cost the player.
        if not self.is_busy():
            for h in self.hazards:
                h.update(dt, self.player.pos, self.block_map)

        # Update NPCs
        for npc in self.npcs:
            if hasattr(npc, "update"):
                npc.update(dt, self.block_map.collision_rects if self.block_map else [])

        # Update block map animations
        if self.block_map:
            self.block_map.update(dt)

        # Update camera follow
        self.camera.follow(self.player.rect)

    def on_item_collected(self, item_id: str):
        pass

    def on_trigger_activated(self, trigger_id: str):
        pass

    def draw(self, surface: pygame.Surface):
        self._drawn_label_rects = []
        self._board_registrations = []
        w, h = surface.get_size()
        shake_offset = (0, 0)
        for hz in self.hazards:
            sx, sy = hz.get_screen_shake()
            if sx != 0 or sy != 0:
                shake_offset = (sx, sy)
                break

        if shake_offset == (0, 0) and self._jolt > 0:
            amp = 2 if self._jolt > 0.15 else 1
            shake_offset = (random.choice((-amp, 0, amp)), random.choice((-amp, 0, amp)))

        world_surf = surface
        if shake_offset != (0, 0):
            world_surf = surface.copy()

        # 1. Draw Code-Rendered BlockMap
        if self.block_map:
            self.block_map.draw(world_surf, self.camera)

        # 1b. Draw interactable blocks and zones
        self._draw_interactables(world_surf)
        self._draw_pickups(world_surf)
        self.draw_under_player(world_surf)

        # 2. Draw NPCs (preserved character art)
        drawn_label_rects = self._drawn_label_rects

        for npc in self.npcs:
            if hasattr(npc, "draw"):
                npc.draw(world_surf, self.camera)
            else:
                s_rect = self.camera.apply(npc.rect)
                pygame.draw.rect(world_surf, (220, 180, 100), s_rect)

            # Use the sprite's real on-screen rect so the name is centred
            # above its head for every NPC size (not its feet/centre).
            if hasattr(npc, "sprite_screen_rect"):
                sprite_rect = npc.sprite_screen_rect(self.camera)
            else:
                s_rect = self.camera.apply(npc.rect)
                sprite_size = getattr(npc, "WORLD_SPRITE_SIZE", (18, 27))
                sprite_rect = pygame.Rect(
                    0, 0,
                    round(sprite_size[0] * self.camera.zoom),
                    round(sprite_size[1] * self.camera.zoom),
                )
                sprite_rect.midbottom = (
                    s_rect.centerx,
                    s_rect.bottom + round(2 * self.camera.zoom),
                )

            # Only draw the name label if its sprite is on screen.
            if not (0 <= sprite_rect.centerx <= w and 0 <= sprite_rect.top <= h):
                continue

            self._draw_entity_name_label(
                world_surf, npc.name, sprite_rect, drawn_label_rects,
            )

        # 3. Draw Player (preserved character art)
        if hasattr(self.player, "draw"):
            self.player.draw(world_surf, self.camera)
        else:
            p_screen = self.camera.apply(self.player.rect)
            pygame.draw.rect(world_surf, (255, 200, 60), p_screen)

        # 4. Draw Hazard Visual Effects
        for hz in self.hazards:
            hz.draw_effects(world_surf, self.camera)

        self.draw_over_world(world_surf)
        self._draw_quest_target_arrow(world_surf)

        if shake_offset != (0, 0):
            surface.blit(world_surf, shake_offset)

        self._draw_hurt_flash(surface)

        # 5. Draw HUD
        self._draw_hud(surface)
        self._draw_hint(surface)
        self._draw_countdown(surface)
        self._draw_meters_and_tray(surface)

        # 6. Dialogue Box
        if self.active_dialogue is not None and self.dialogue_idx < len(self.active_dialogue):
            self._draw_dialogue_box(surface)

        # 7. Decision Box
        if self.decision_system.is_active():
            self._draw_decision_box(surface)

        # 7b. Mini-game panel
        if self.minigame is not None:
            self._draw_minigame(surface)

        # 8. Lesson Modal
        if self.show_lesson_modal:
            self._draw_lesson_modal(surface)

        # 9. Legend Screen
        if self.legend_screen.visible:
            self._register_board(surface.get_rect())
            self.legend_screen.draw(surface)

        # 10. Pause Menu
        if self.pause_menu.visible:
            self._register_board(surface.get_rect())
            self.pause_menu.draw(surface)

        # 11. Boards dominate: any text queued before a board (NPC names,
        # item/house labels, earlier boards) is discarded when it would
        # render on top of that board.
        self._apply_board_dominance()

    # ── HUD layout helpers ──────────────────────────────────────────
    # Kept separate from drawing so world labels can avoid the HUD areas.
    HUD_BAR_H = 14
    HUD_PAD = 4

    # Quest board: compact, anchored top-left just under the status bar.
    OBJ_PAD_X = 5
    OBJ_PAD_Y = 3
    OBJ_MAX_LINES = 3
    OBJ_FONT = "small"    # one step down from "body"; use "body" if too small
    OBJ_MIN_W = 90        # never narrower than this
    OBJ_MAX_W = 150       # never wider than this
    OBJ_MARGIN = 4        # distance from the left edge of the screen
    OBJ_SHOW_TIME = 6.0   # seconds the board stays open after a new objective
    OBJ_IDLE_SHOW = 2.0   # seconds standing still before the board reopens
    OBJ_TAB_TEXT = "OBJ"  # label on the collapsed tab
    NAME_LABEL_GAP = 6

    def _update_objective_visibility(self, dt: float):
        """Track when the quest board should be open or collapsed."""
        if self.current_objective_idx != self._last_obj_idx:
            self._last_obj_idx = self.current_objective_idx
            self.obj_show_timer = self.OBJ_SHOW_TIME
        if self.obj_show_timer > 0:
            self.obj_show_timer -= dt

        pos = tuple(self.player.rect.center)
        if pos == self._last_player_pos:
            self._idle_time += dt
        else:
            self._idle_time = 0.0
            self._last_player_pos = pos

    def _objective_expanded(self) -> bool:
        return (
            self.obj_pinned
            or self.obj_show_timer > 0
            or self._idle_time >= self.OBJ_IDLE_SHOW
        )

    def _objective_box(self, w):
        """Return ``(rect, wrapped_lines, line_height)`` for the quest board.

        The board is anchored to a fixed screen position (top-left, just
        below the status bar), so the camera never moves it and it cannot
        collide with world objects. It is sized to fit its own text
        (clamped between ``OBJ_MIN_W`` and ``OBJ_MAX_W``), keeping it a
        small tab that is still high-contrast and readable.
        """
        # Collapsed: just a small tab while the player is busy.
        if not self._objective_expanded():
            tw, th = measure_text(self.OBJ_TAB_TEXT, "tiny")
            tab = pygame.Rect(
                self.OBJ_MARGIN, self.HUD_BAR_H + 3, tw + 10, th + 4,
            )
            return tab, [self.OBJ_TAB_TEXT], th

        obj_raw = (
            self.objectives[self.current_objective_idx]
            if self.current_objective_idx < len(self.objectives)
            else "All Objectives Complete"
        )
        total = len(self.objectives)
        curr = min(total, self.current_objective_idx + 1)
        if total > 0 and self.current_objective_idx < total and not obj_raw.startswith("["):
            obj_display = f"[{curr}/{total}] {obj_raw}"
        else:
            obj_display = obj_raw

        max_box_w = min(w - self.OBJ_MARGIN * 2, self.OBJ_MAX_W)
        inner_w = max(1, max_box_w - self.OBJ_PAD_X * 2)
        obj_lines = tu_wrap(obj_display, self.OBJ_FONT, inner_w)
        if len(obj_lines) > self.OBJ_MAX_LINES:
            obj_lines = obj_lines[:self.OBJ_MAX_LINES]
            obj_lines[-1] = ellipsize(
                obj_lines[-1] + "...", self.OBJ_FONT, inner_w,
            )
        widest = max(measure_text(line, self.OBJ_FONT)[0] for line in obj_lines)
        box_w = min(max_box_w, max(self.OBJ_MIN_W, widest + self.OBJ_PAD_X * 2))
        lh = line_height(self.OBJ_FONT)
        line_gap = 2
        obj_box_h = (self.OBJ_PAD_Y * 2 + lh * len(obj_lines)
                     + line_gap * max(0, len(obj_lines) - 1))
        rect = pygame.Rect(
            self.OBJ_MARGIN, self.HUD_BAR_H + 3, box_w, obj_box_h,
        )
        return rect, obj_lines, lh

    def _register_board(self, rect: pygame.Rect):
        """Declare an overlay board (quest board, hint, dialogue, lesson...).

        Text already queued when the board registers — world labels such as
        NPC names, item names and house names, plus earlier boards — is
        discarded if it lands inside the board. This is needed because
        queued text is flushed on top of the scaled canvas, so without
        this any world label would float over an opaque board.
        """
        self._board_registrations.append(
            (len(theme.TEXT_QUEUE), pygame.Rect(rect))
        )

    def _apply_board_dominance(self):
        """Drop queued text that would show through a registered board."""
        boards = getattr(self, "_board_registrations", [])
        if not boards:
            return
        kept = []
        for idx, item in enumerate(theme.TEXT_QUEUE):
            font, text, _color, (x, y), _shadow = item
            tw, th = font.size(text)
            rect = pygame.Rect(x, y, tw, th)
            behind_board = any(
                idx < mark and rect.colliderect(board_rect)
                for mark, board_rect in boards
            )
            if not behind_board:
                kept.append(item)
        theme.TEXT_QUEUE[:] = kept

    def _draw_entity_name_label(
        self,
        surface: pygame.Surface,
        name: str,
        sprite_rect: pygame.Rect,
        drawn_label_rects: List[pygame.Rect],
    ) -> Optional[pygame.Rect]:
        """Draw *name* centred in a small gap directly above an entity sprite.

        The position comes from the sprite's real on-screen top edge and
        horizontal centre, so it works for any entity size. Returns the
        label rect, or ``None`` when the label must be hidden (off-screen or
        under a HUD panel).
        """
        w, _h = surface.get_size()
        nw, nh = measure_text(name, "tiny")
        rect = pygame.Rect(0, 0, nw, nh)
        rect.midtop = (
            sprite_rect.centerx,
            sprite_rect.top - self.NAME_LABEL_GAP - nh,
        )

        # Keep the label inside the playfield horizontally.
        if rect.left < 2:
            rect.left = 2
        elif rect.right > w - 2:
            rect.right = w - 2

        # Avoid overlapping previously drawn world labels; nudge upward.
        while any(rect.colliderect(r) for r in drawn_label_rects):
            rect.y -= nh + 2
            if rect.top < 2:
                break

        # Queued text renders on top of the HUD, so hide any label that
        # would sit over a HUD panel rather than drawing through it.
        if rect.top < 2 or any(
            rect.colliderect(r) for r in self._hud_reserved_rects(w, _h)
        ):
            return None

        drawn_label_rects.append(rect)
        theme.draw_text(
            surface, name, rect.midtop,
            size="tiny", color=COLOR_UI_TEXT, shadow=True, anchor="midtop",
        )
        return rect

    def _hint_box(self, w, h):
        """Return ``(rect, wrapped_lines, line_height)`` for the hint banner."""
        if self.hint_timer <= 0 or not self.hint_text:
            return None

        max_w = w - 8
        cd_rect = self._countdown_rect(w)
        if cd_rect is not None:
            max_w = min(max_w, w - cd_rect.w - 12)

        box_w = min(max_w, 260)
        lines = tu_wrap(self.hint_text, "tiny",
                        box_w - self.HUD_PAD * 2)[:self.HINT_MAX_LINES]
        lh = line_height("tiny")
        box_h = (self.HUD_PAD * 2 + lh * len(lines)
                 + max(0, len(lines) - 1))
        obj_rect, _, _ = self._objective_box(w)
        rect = pygame.Rect(4, obj_rect.bottom + 2, box_w, box_h)
        return rect, lines, lh

    def _countdown_rect(self, w):
        """Return the screen rect of the countdown text, or ``None``."""
        if not self.countdown_active or self.show_lesson_modal:
            return None
        secs = max(0, int(self.countdown_time) + 1)
        tw, th = measure_text(f"{self.countdown_label} {secs}s", "tiny")
        # Fixed top-right slot (the quest board lives on the left now)
        return pygame.Rect(w - 4 - tw, self.HUD_BAR_H + 3, tw, th)

    def _hud_reserved_rects(self, w, h):
        """Areas covered by HUD panels/boards that world labels must avoid."""
        # A full-screen board (lesson modal, legend, pause menu) owns the
        # whole screen: no world label may show above it.
        if (self.show_lesson_modal or self.legend_screen.visible
                or self.pause_menu.visible):
            return [pygame.Rect(0, 0, w, h)]

        rects = [pygame.Rect(0, 0, w, self.HUD_BAR_H),
                 self._objective_box(w)[0]]
        hint = self._hint_box(w, h)
        if hint is not None:
            rects.append(hint[0])
        cd_rect = self._countdown_rect(w)
        if cd_rect is not None:
            rects.append(cd_rect)
        if (self.active_dialogue is not None
                and self.dialogue_idx < len(self.active_dialogue)):
            rects.append(self._dialogue_box_layout(w, h)[0])
        if self.decision_system.is_active():
            rects.append(self._decision_box_layout(w, h)[0])
        for extra in (self._meters_rect(w), self._tray_rect(w)):
            if extra is not None:
                rects.append(extra)
        if self.minigame is not None:
            rects.append(self._minigame_rect(w, h))
        return rects

    def _draw_hud(self, surface: pygame.Surface):
        """Top bar (disaster status + controls) and dominant quest board.

        The quest board is the last thing drawn in the HUD layer: after
        the world, NPCs, item labels and all other world labels. Its
        background is fully opaque and anything queued before it that
        lands inside it is discarded by ``_apply_board_dominance``, so
        nothing can show through or draw on top of it.

        The board bottom is stored in ``self._obj_box_bottom`` so that
        ``_draw_hint`` and ``_draw_countdown`` stack below it.
        """
        w, h = surface.get_size()
        obj_rect, obj_lines, lh = self._objective_box(w)

        # ── top bar ──────────────────────────────────────────────────
        BAR_H = self.HUD_BAR_H
        self._register_board(pygame.Rect(0, 0, w, BAR_H))
        pygame.draw.rect(surface, (20, 24, 28), (0, 0, w, BAR_H))
        pygame.draw.line(surface, COLOR_UI_BORDER, (0, BAR_H), (w, BAR_H), 1)

        controls = "ESC:Pause L:Legend SPC:Act"
        ctrl_w = measure_text(controls, "tiny")[0]
        avail_left = w - 16 - ctrl_w - 4      # room for the disaster label

        disaster_label = f"STATUS: {self.disaster_type.upper()}"
        disaster_label = ellipsize(disaster_label, "tiny", avail_left)

        theme.draw_text(
            surface, disaster_label, (4, 2),
            size="tiny", color=COLOR_UI_DANGER, shadow=False, anchor="topleft",
        )
        theme.draw_text(
            surface, controls, (w - 4, 2),
            size="tiny", color=COLOR_UI_ACCENT, shadow=False, anchor="topright",
        )

        # ── quest board (highest HUD draw order) ─────────────────────
        self._register_board(obj_rect)
        if not self._objective_expanded():
            # Collapsed tab: small, unobtrusive, still opaque.
            pygame.draw.rect(surface, COLOR_UI_PANEL, obj_rect)
            pygame.draw.rect(surface, COLOR_UI_BORDER, obj_rect, 1)
            pygame.draw.rect(
                surface, COLOR_UI_ACCENT,
                pygame.Rect(obj_rect.x, obj_rect.y, 2, obj_rect.h),
            )
            theme.draw_text(
                surface, self.OBJ_TAB_TEXT,
                (obj_rect.centerx + 1, obj_rect.y + 2),
                size="tiny", color=COLOR_UI_ACCENT, shadow=False,
                anchor="midtop",
            )
        else:
            PAD_Y = self.OBJ_PAD_Y
            # Soft drop shadow lifts the board off the busy world art.
            pygame.draw.rect(surface, (12, 9, 6), obj_rect.move(1, 2))
            pygame.draw.rect(surface, COLOR_UI_PANEL, obj_rect)  # fully opaque
            pygame.draw.rect(surface, COLOR_UI_BORDER, obj_rect, 1)
            # Accent stripe on the left edge reads as a "quest" marker.
            pygame.draw.rect(
                surface, COLOR_UI_ACCENT,
                pygame.Rect(obj_rect.x, obj_rect.y, 3, obj_rect.h),
            )

            # Left-aligned text, indented past the accent stripe.
            for i, line in enumerate(obj_lines):
                theme.draw_text(
                    surface, line,
                    (obj_rect.x + self.OBJ_PAD_X + 2,
                     obj_rect.y + PAD_Y + i * (lh + 2)),
                    size=self.OBJ_FONT, color=COLOR_UI_TEXT, shadow=True,
                    anchor="topleft",
                )

        # Save bottom for dependent elements
        self._obj_box_bottom = obj_rect.bottom

    def _draw_countdown(self, surface: pygame.Surface):
        cd_rect = self._countdown_rect(surface.get_width())
        if cd_rect is None:
            return
        self._register_board(cd_rect)
        secs = max(0, int(self.countdown_time) + 1)
        color = COLOR_UI_DANGER if secs <= 10 else COLOR_UI_ACCENT
        theme.draw_text(
            surface,
            f"{self.countdown_label} {secs}s",
            cd_rect.topright,
            size="tiny",
            color=color,
            shadow=True,
            anchor="topright",
        )

    def _draw_interactables(self, surface: pygame.Surface):
        w, h = surface.get_size()
        drawn_label_rects = getattr(self, "_drawn_label_rects", [])
        self._drawn_label_rects = drawn_label_rects
        hud_rects = self._hud_reserved_rects(w, h)

        for item in self.interactables:
            s_rect = self.camera.apply(item["rect"])

            if item["alpha"]:
                color = item["color"]
                if item["done"]:
                    color = tuple(int(c * 0.45) for c in color)
                zone = pygame.Surface(s_rect.size, pygame.SRCALPHA)
                zone.fill((*color, item["alpha"]))
                surface.blit(zone, s_rect.topleft)
                pygame.draw.rect(surface, COLOR_UI_BORDER, s_rect, 1)
            else:
                self._draw_interactable_sprite(surface, item, s_rect)

            on_screen = 0 <= s_rect.centerx <= w and 0 <= s_rect.top <= h
            if not on_screen:
                continue

            if not item["label"]:
                self._draw_interact_prompt(surface, item, s_rect, w, h)
                continue

            # Clamp label horizontally & prevent overlap
            label = item["label"]
            lw, lh = measure_text(label, "tiny")
            lx = s_rect.centerx
            ly = s_rect.top - 8

            rect = pygame.Rect(lx - lw // 2, ly, lw, lh)
            while any(rect.colliderect(r) for r in drawn_label_rects):
                rect.y -= (lh + 2)
                if rect.y < 2:
                    rect.y = s_rect.bottom + 2
                    break
            rect.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
            # Never let a world/item label sit over the objective banner.
            if any(rect.colliderect(r) for r in hud_rects):
                continue
            drawn_label_rects.append(rect)

            theme.draw_text(
                surface, label, (rect.centerx, rect.top),
                size="tiny", color=COLOR_UI_TEXT, shadow=True, anchor="midtop",
            )
            if item["prompt"] and not item["done"] and self._near_interactable(item):
                pw, ph = measure_text("[SPACE]", "tiny")
                prompt_y = min(s_rect.bottom + 2, h - ph - 2)
                p_rect = pygame.Rect(s_rect.centerx - pw // 2, prompt_y, pw, ph)
                p_rect.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
                theme.draw_text(
                    surface, "[SPACE]", (p_rect.centerx, p_rect.top),
                    size="tiny", color=COLOR_UI_ACCENT, shadow=True, anchor="midtop",
                )

    def _draw_interactable_sprite(self, surface, item, s_rect):
        """Draw a hard-coded pixel sprite for an interactable object.

        The object keeps a colour-coded plate (so a level stays readable and
        colour-blind friendly) with its matching code-rendered sprite on top.
        """
        done = item["done"]

        # Soft drop shadow so the object reads as standing on the ground.
        pygame.draw.rect(surface, (10, 12, 14), s_rect.move(0, 2), border_radius=2)

        # Colour-coded plate, dimmed once the object has been used.
        if done:
            plate = tuple(int(c * 0.45) for c in item["color"])
        else:
            plate = theme.mix(theme.WOOD_DARK, item["color"], 0.45)
        pygame.draw.rect(surface, plate, s_rect, border_radius=2)
        pygame.draw.rect(surface, COLOR_UI_BORDER, s_rect, 1, border_radius=2)

        # Dark backing keeps the sprite readable on every plate colour.
        art = interactable_art_name(item["key"], item["label"])
        icon = icon_surface(art, 1, dim=done)
        icon_rect = icon.get_rect(center=s_rect.center)
        pygame.draw.rect(
            surface, (16, 16, 22), icon_rect.inflate(2, 2).clip(s_rect), border_radius=2
        )
        surface.blit(icon, icon_rect)

    def _draw_interact_prompt(self, surface, item, s_rect, w, h):
        if item["prompt"] and not item["done"] and self._near_interactable(item):
            pw, ph = measure_text("[SPACE]", "tiny")
            prompt_y = min(s_rect.bottom + 2, h - ph - 2)
            p_rect = pygame.Rect(s_rect.centerx - pw // 2, prompt_y, pw, ph)
            p_rect.clamp_ip(pygame.Rect(2, 2, w - 4, h - 4))
            theme.draw_text(
                surface, "[SPACE]", (p_rect.centerx, p_rect.top),
                size="tiny", color=COLOR_UI_ACCENT, shadow=True, anchor="midtop",
            )

    def _draw_pickups(self, surface: pygame.Surface):
        w, h = surface.get_size()
        scale = max(1, int(round(getattr(self.camera, "zoom", 1) or 1)))
        for it in self.pickups:
            if it["got"]:
                continue
            s = self.camera.apply(it["rect"])
            if not (-12 <= s.centerx <= w + 12 and -12 <= s.centery <= h + 12):
                continue
            bob = int(round(math.sin(self._anim_t * 3.0 + it["phase"]) * 1.5))
            pygame.draw.ellipse(surface, (10, 14, 12), (s.centerx - 5, s.bottom - 1, 10, 4))
            icon = icon_surface(it["icon"], scale)
            surface.blit(icon, icon.get_rect(center=(s.centerx, s.centery + bob - 1)))
            if int(self._anim_t * 2.5 + it["phase"]) % 2 == 0:
                draw_sparkle(surface, s.right + 1, s.top - 2 + bob)
            pdx = self.player.rect.centerx - it["rect"].centerx
            pdy = self.player.rect.centery - it["rect"].centery
            if pdx * pdx + pdy * pdy <= 44 * 44:
                theme.draw_text(
                    surface, it["label"], (s.centerx, s.top - 13 + bob),
                    size="tiny", color=COLOR_UI_ACCENT, shadow=True, anchor="midtop",
                )
        for fx in self._pickup_fx:
            cx, cy = self.camera.apply(pygame.Rect(fx["pos"][0], fx["pos"][1], 1, 1)).topleft
            r = int((0.6 - fx["t"]) * 40) + 3
            for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r)):
                draw_sparkle(surface, cx + dx, cy + dy)

    def _draw_hurt_flash(self, surface: pygame.Surface):
        if self.hurt_flash <= 0:
            return
        a = int(120 * min(1.0, self.hurt_flash / 0.45))
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        layer.fill((200, 30, 30, a))
        surface.blit(layer, (0, 0))

    # Right-hand HUD column (below the countdown): meters, then item tray.
    METER_W = 56
    RIGHT_COL_Y = 32

    def _meter_row_h(self):
        return line_height("tiny") + 7

    def _meters_rect(self, w):
        if not self.meters:
            return None
        width = self.METER_W + 6
        return pygame.Rect(
            w - 4 - width, self.RIGHT_COL_Y, width,
            4 + len(self.meters) * self._meter_row_h(),
        )

    def _tray_rect(self, w):
        if not self.tray_slots:
            return None
        top = self.RIGHT_COL_Y
        mr = self._meters_rect(w)
        if mr is not None:
            top = mr.bottom + 2
        width = len(self.tray_slots) * 15 + 3
        return pygame.Rect(w - 4 - width, top, width, 17)

    def _draw_meters_and_tray(self, surface: pygame.Surface):
        w, _h = surface.get_size()
        mr = self._meters_rect(w)
        if mr is not None:
            self._register_board(mr)
            pygame.draw.rect(surface, COLOR_UI_PANEL, mr)
            pygame.draw.rect(surface, COLOR_UI_BORDER, mr, 1)
            row_h = self._meter_row_h()
            lh = line_height("tiny")
            for i, m in enumerate(self.meters.values()):
                y = mr.y + 2 + i * row_h
                theme.draw_text(
                    surface, m["label"], (mr.x + 3, y),
                    size="tiny", color=COLOR_UI_TEXT, shadow=False, anchor="topleft",
                )
                r = m["ratio"]
                bad = (r < 0.25) if m["good_high"] else (r > 0.75)
                mid = (r < 0.5) if m["good_high"] else (r > 0.5)
                color = (220, 70, 60) if bad else ((240, 190, 70) if mid else (90, 200, 120))
                draw_bar(
                    surface, pygame.Rect(mr.x + 3, y + lh + 1, self.METER_W, 5),
                    r, color, seg=3,
                )
        tr = self._tray_rect(w)
        if tr is not None:
            self._register_board(tr)
            pygame.draw.rect(surface, COLOR_UI_PANEL, tr)
            pygame.draw.rect(surface, COLOR_UI_BORDER, tr, 1)
            for i, slot in enumerate(self.tray_slots):
                got = slot["key"] in self.collected
                box = pygame.Rect(tr.x + 2 + i * 15, tr.y + 2, 13, 13)
                pygame.draw.rect(surface, (38, 42, 52), box)
                draw_icon(surface, slot["icon"], box.center, 1, dim=not got)
                if got:
                    surface.fill((90, 220, 120), (box.right - 3, box.bottom - 3, 3, 3))

    def _minigame_rect(self, w, h):
        mg = self.minigame
        rect = pygame.Rect(0, 0, min(w - 16, mg.PANEL_W), mg.PANEL_H)
        rect.midbottom = (w // 2, h - 8)
        return rect

    def _draw_minigame(self, surface: pygame.Surface):
        w, h = surface.get_size()
        rect = self._minigame_rect(w, h)
        self._register_board(rect)
        self.minigame.draw(surface, rect)

    # Maximum hint lines before truncation.
    HINT_MAX_LINES = 2

    def _draw_hint(self, surface: pygame.Surface):
        """Draw the hint banner below the quest board while its timer runs."""
        w, h = surface.get_size()
        layout = self._hint_box(w, h)
        if layout is None:
            return

        PAD = self.HUD_PAD
        box_rect, lines, lh = layout
        self._register_board(box_rect)
        pygame.draw.rect(surface, COLOR_UI_PANEL, box_rect)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, box_rect, 1)
        for i, line in enumerate(lines):
            theme.draw_text(
                surface, line,
                (box_rect.x + PAD, box_rect.y + PAD + i * (lh + 1)),
                size="tiny", color=COLOR_UI_TEXT, shadow=False, anchor="topleft",
            )

    def _draw_quest_target_arrow(self, surface: pygame.Surface) -> None:
        """Bobbing gold arrow over current objective target."""
        if self.completed:
            return
        if (self.active_dialogue is not None or self.decision_system.is_active()
                or self.minigame is not None or self.show_lesson_modal
                or self.legend_screen.visible or self.pause_menu.visible):
            return

        step_idx = getattr(self, "current_objective_idx", 0)
        target = None
        if hasattr(self, "guide_points") and self.guide_points and 0 <= step_idx < len(self.guide_points):
            target = self.guide_points[step_idx]
        elif hasattr(self, "ARROW_POINTS") and self.ARROW_POINTS and 0 <= step_idx < len(self.ARROW_POINTS):
            target = self.ARROW_POINTS[step_idx]
        elif getattr(self, "_steps", None) and 0 <= step_idx < len(self._steps):
            target = self._steps[step_idx].get("target")

        if not target:
            return
        t_pos = target() if callable(target) else target
        if not t_pos:
            return
        if hasattr(t_pos, "center"):
            tx, ty = t_pos.centerx, t_pos.top
        else:
            tx, ty = t_pos[0], t_pos[1]

        # Hide arrow if player is close enough (within ~28 px)
        px, py = self.player.rect.center
        if (px - tx) ** 2 + (py - ty) ** 2 <= 28 * 28:
            return

        s_pos = self.camera.apply(pygame.Rect(int(tx), int(ty), 1, 1))
        sx, sy = s_pos.x, s_pos.y
        w, h = surface.get_size()
        sx = max(8, min(w - 8, sx))
        sy = max(20, min(h - 8, sy))

        bob = int(round(math.sin(self.level_time * 5.0) * 2))
        tip = sy + bob
        pygame.draw.polygon(surface, (24, 22, 32), [(sx - 7, tip - 11), (sx + 7, tip - 11), (sx, tip + 3)])
        pygame.draw.polygon(surface, (250, 210, 90), [(sx - 5, tip - 9), (sx + 5, tip - 9), (sx, tip)])

    def _draw_portrait(self, surface: pygame.Surface, rect: pygame.Rect, speaker: str) -> None:
        """Draw a retro pixel RPG character badge/portrait in a small box."""
        pygame.draw.rect(surface, (18, 22, 30), rect)
        pygame.draw.rect(surface, COLOR_UI_BORDER, rect, 1)

        sp = speaker.upper()
        if "RICO" in sp or "BEN" in sp or "JUAN" in sp:
            skin_col = (235, 180, 130)
            hair_col = (40, 32, 28)
            shirt_col = (60, 130, 190) if "RICO" in sp else (200, 70, 50)
        elif "MARIA" in sp or "NURSE" in sp or "LITA" in sp:
            skin_col = (240, 190, 150)
            hair_col = (60, 40, 30)
            shirt_col = (190, 80, 120)
        elif "TITO" in sp or "RAMON" in sp or "MAYOR" in sp:
            skin_col = (220, 165, 120)
            hair_col = (150, 150, 150)
            shirt_col = (210, 150, 40)
        elif "VOSS" in sp or "DOCTOR" in sp or "DR" in sp:
            skin_col = (230, 185, 140)
            hair_col = (220, 220, 225)
            shirt_col = (140, 160, 180)
        elif "RADIO" in sp or "BROADCAST" in sp or "DISPATCH" in sp:
            r_surf = icon_surface("radio", 2)
            surface.blit(r_surf, r_surf.get_rect(center=rect.center))
            return
        else:
            init = (sp[:2] if len(sp) >= 2 else sp)
            theme.draw_text(surface, init, rect.center, size="small",
                            color=COLOR_UI_ACCENT, shadow=True, anchor="center")
            return

        cx, cy = rect.centerx, rect.centery
        pygame.draw.rect(surface, hair_col, (cx - 5, cy - 8, 10, 5))
        pygame.draw.rect(surface, skin_col, (cx - 4, cy - 4, 8, 7))
        surface.fill((30, 30, 30), (cx - 3, cy - 2, 2, 2))
        surface.fill((30, 30, 30), (cx + 1, cy - 2, 2, 2))
        pygame.draw.rect(surface, shirt_col, (cx - 6, cy + 3, 12, 6))

    def _dialogue_box_layout(self, w, h):
        """Return (rect, display_lines, line_height, pad) for dialogue box."""
        PAD = 4
        box_w = min(w - 16, 296)
        port_w = 26
        inner_w = box_w - PAD * 2 - port_w - 6

        lh = line_height("tiny")
        current_line = self.active_dialogue[self.dialogue_idx]

        lines = tu_wrap(current_line, "tiny", inner_w)
        display_lines = lines[:4]

        text_h = (lh + 1) * max(2, len(display_lines))
        footer_h = lh + 1
        box_h = PAD * 2 + text_h + footer_h + 2

        box_x = (w - box_w) // 2
        box_y = h - box_h - 6
        rect = pygame.Rect(box_x, box_y, box_w, box_h)
        return rect, display_lines, lh, PAD

    def _draw_dialogue_box(self, surface: pygame.Surface):
        w, h = surface.get_size()
        box_rect, display_lines, lh, PAD = self._dialogue_box_layout(w, h)
        box_x, box_y = box_rect.x, box_rect.y
        box_w, box_h = box_rect.w, box_rect.h
        speaker = self.dialogue_speaker.upper()

        tab_pad = 4
        sp_w, sp_h = measure_text(speaker, "tiny")
        tab_w = sp_w + tab_pad * 2 + 4
        tab_h = sp_h + 3
        tab_rect = pygame.Rect(box_x + 8, box_y - tab_h + 1, tab_w, tab_h)

        full_bound = box_rect.union(tab_rect)
        self._register_board(full_bound)

        # Shared wood-and-brass panel styling.
        theme.draw_panel(surface, box_rect, accent=theme.HONEY, alpha=238)

        # Speaker tab
        pygame.draw.rect(surface, theme.SHADOW, tab_rect.move(1, 1))
        theme.draw_panel(surface, tab_rect, accent=theme.BRASS, alpha=238)
        theme.draw_text(
            surface, speaker,
            (tab_rect.x + tab_pad + 2, tab_rect.y + 1),
            size="tiny", color=COLOR_UI_ACCENT, shadow=True, anchor="topleft",
        )

        # Portrait slot
        port_rect = pygame.Rect(box_x + PAD + 2, box_y + PAD + 2, 22, 22)
        self._draw_portrait(surface, port_rect, self.dialogue_speaker)

        # Typewriter text reveal
        text_x = box_x + PAD + 28
        curr_y = box_y + PAD + 2
        cur_line = self.active_dialogue[self.dialogue_idx]
        rev_count = int(self._dialogue_chars)

        for line in display_lines:
            if rev_count <= 0:
                break
            if rev_count >= len(line):
                shown = line
                rev_count -= len(line)
            else:
                shown = line[:rev_count]
                rev_count = 0
            theme.draw_text(
                surface, shown,
                (text_x, curr_y),
                size="tiny", color=COLOR_UI_TEXT, shadow=False, anchor="topleft",
            )
            curr_y += lh + 1

        # Blinking continue prompt & triangle
        if self._dialogue_chars >= len(cur_line):
            blink = int(self.level_time * 3.5) % 2 == 0
            prompt_color = COLOR_UI_ACCENT if blink else (160, 180, 200)
            theme.draw_text(
                surface, "[SPACE] Continue",
                (box_x + box_w - PAD - 12, box_y + box_h - PAD - 1),
                size="tiny", color=prompt_color, shadow=False, anchor="bottomright",
            )
            if blink:
                tri_x = box_x + box_w - PAD - 5
                tri_y = box_y + box_h - PAD - 4
                pygame.draw.polygon(surface, COLOR_UI_ACCENT, [
                    (tri_x - 3, tri_y - 4), (tri_x + 3, tri_y - 4), (tri_x, tri_y)
                ])

    def _decision_box_layout(self, w, h):
        """Return layout data for the decision box (rect, lines, lh, pad, footer)."""
        dec = self.decision_system.current_decision
        screen_rect = pygame.Rect(0, 0, w, h)
        PAD = 4
        box_w = min(w - 16, 296)
        inner_w = box_w - PAD * 2

        lh = line_height("tiny")

        prompt_lines = tu_wrap(dec.prompt, "tiny", inner_w - 4)
        prompt_h = lh * len(prompt_lines) + max(0, len(prompt_lines) - 1)

        feedback_h = 0
        if getattr(self, "_last_decision_feedback", ""):
            fb_lines = tu_wrap(f"[!] {self._last_decision_feedback}", "tiny", inner_w - 8)
            feedback_h = lh * len(fb_lines) + 4

        opt_wrapped = []
        for opt in dec.options:
            opt_lines = tu_wrap(opt['text'], "tiny", inner_w - 16)
            opt_wrapped.append(opt_lines)
        opts_h = 0
        for ol in opt_wrapped:
            opts_h += lh * len(ol) + 7

        footer_h = lh
        box_h = PAD + lh + 4 + prompt_h + 3 + feedback_h + opts_h + 3 + footer_h + PAD

        box_x = (w - box_w) // 2
        box_y = h - box_h - 6
        box_rect = clamp_rect(pygame.Rect(box_x, box_y, box_w, box_h), screen_rect)
        return box_rect, prompt_lines, opt_wrapped, lh, PAD, footer_h

    def _draw_decision_box(self, surface: pygame.Surface):
        dec = self.decision_system.current_decision
        if not dec:
            return
        w, h = surface.get_size()
        box_rect, prompt_lines, opt_wrapped, lh, PAD, footer_h = (
            self._decision_box_layout(w, h)
        )
        box_x, box_y = box_rect.x, box_rect.y
        box_w, box_h = box_rect.w, box_rect.h
        inner_w = box_w - PAD * 2

        self._register_board(box_rect)
        border_col = theme.CORAL if getattr(self, "_last_decision_feedback", "") else theme.HONEY
        theme.draw_panel(surface, box_rect, accent=border_col, alpha=240)

        cy = box_y + PAD
        title_text = "PREPAREDNESS DECISION"
        theme.draw_text(
            surface, title_text, (w // 2, cy),
            size="tiny", color=COLOR_UI_ACCENT, shadow=True, anchor="midtop",
        )
        cy += lh + 3

        if getattr(self, "_last_decision_feedback", ""):
            fb_lines = tu_wrap(f"[!] {self._last_decision_feedback}", "tiny", inner_w - 8)[:2]
            fb_h = lh * len(fb_lines) + 3
            fb_rect = pygame.Rect(box_x + PAD + 2, cy, inner_w - 4, fb_h)
            pygame.draw.rect(surface, theme.PLUM, fb_rect)
            pygame.draw.rect(surface, theme.CORAL, fb_rect, 1)
            f_y = cy + 1
            for fl in fb_lines:
                theme.draw_text(
                    surface, fl, (box_x + PAD + 6, f_y),
                    size="tiny", color=theme.CREAM, shadow=False, anchor="topleft",
                )
                f_y += lh
            cy += fb_h + 3

        for line in prompt_lines:
            theme.draw_text(
                surface, line, (box_x + PAD + 4, cy),
                size="tiny", color=COLOR_UI_TEXT, shadow=False, anchor="topleft",
            )
            cy += lh + 1
        cy += 2

        for idx, (opt, ol) in enumerate(zip(dec.options, opt_wrapped)):
            is_sel = idx == dec.selected_index
            row_h = lh * len(ol) + 4
            row_rect = pygame.Rect(box_x + PAD + 2, cy, inner_w - 4, row_h)

            theme.draw_option_row(surface, row_rect, selected=is_sel, accent=theme.HONEY)
            if is_sel:
                prefix = "> "
                txt_col = theme.HONEY
            else:
                prefix = "  "
                txt_col = theme.CREAM

            opt_y = cy + 2
            for li, line in enumerate(ol):
                txt = f"{prefix}{line}" if li == 0 else f"  {line}"
                theme.draw_text(
                    surface, txt, (box_x + PAD + 6, opt_y),
                    size="tiny", color=txt_col, shadow=False, anchor="topleft",
                )
                opt_y += lh
            cy += row_h + 3

        footer_text = "[UP/DOWN] Select  [SPACE] Confirm"
        theme.draw_text(
            surface, footer_text, (w // 2, box_rect.bottom - PAD - footer_h),
            size="tiny", color=COLOR_UI_ACCENT, shadow=False, anchor="midtop",
        )

    def _draw_lesson_modal(self, surface: pygame.Surface):
        w, h = surface.get_size()
        screen_rect = pygame.Rect(0, 0, w, h)
        # The dim + panel cover the whole screen, so this board owns it.
        self._register_board(screen_rect)
        theme.fade(surface, 230)

        PAD = 6
        box_w = min(w - 16, 300)
        inner_w = box_w - PAD * 2
        lh = line_height("tiny")
        lh_small = line_height("small")

        # Title
        title_text = "STAGE COMPLETE - LESSON"

        # Source line (ellipsized)
        source_text = ellipsize(f"SOURCE: {self.lesson_source}", "tiny", inner_w)

        # Body: wrap ALL lesson lines, never truncate
        raw_lines = self.lesson_text.split("\n")
        body_lines = []
        for raw in raw_lines:
            stripped = raw.strip()
            if stripped:
                body_lines.extend(tu_wrap(stripped, "tiny", inner_w - 4))
            else:
                body_lines.append("")

        # Compute heights
        title_h = lh_small + 2
        source_h = lh + 4
        body_h = (lh + 1) * len(body_lines)
        footer_h = lh + 2

        box_h = PAD + title_h + source_h + body_h + 6 + footer_h + PAD
        # Clamp to screen
        max_box_h = h - 8
        if box_h > max_box_h:
            box_h = max_box_h
            # Recalculate max body lines that fit
            avail_body = box_h - PAD - title_h - source_h - 6 - footer_h - PAD
            max_body_lines = max(1, avail_body // (lh + 1))
            if len(body_lines) > max_body_lines:
                body_lines = body_lines[:max_body_lines]
                if body_lines:
                    body_lines[-1] = ellipsize(body_lines[-1] + "...", "tiny", inner_w - 4)

        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2
        box_rect = clamp_rect(pygame.Rect(box_x, box_y, box_w, box_h), screen_rect)
        box_x, box_y = box_rect.x, box_rect.y

        theme.draw_panel(surface, box_rect, accent=theme.SAGE, alpha=242)

        cy = box_y + PAD
        # Title
        theme.draw_text(
            surface, title_text, (w // 2, cy),
            size="small", color=COLOR_UI_SAFE, shadow=True, anchor="midtop",
        )
        cy += title_h

        # Source
        theme.draw_text(
            surface, source_text, (box_x + PAD, cy),
            size="tiny", color=COLOR_UI_ACCENT, shadow=False, anchor="topleft",
        )
        cy += source_h

        # Body lines
        for line in body_lines:
            theme.draw_text(
                surface, line, (box_x + PAD + 2, cy),
                size="tiny", color=COLOR_UI_TEXT, shadow=False, anchor="topleft",
            )
            cy += lh + 1

        # Footer
        theme.draw_text(
            surface, "[SPACE] / [ENTER] Continue",
            (w // 2, box_rect.bottom - PAD - 2),
            size="tiny", color=COLOR_UI_ACCENT, shadow=True, anchor="midbottom",
        )