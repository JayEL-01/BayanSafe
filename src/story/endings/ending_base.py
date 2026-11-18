"""Shared, polished presentation for the three campaign endings.

The endings used to be three flat text pages. This module gives them the same
handcrafted look as the chapters and menus:

* an animated dusk backdrop (``theme.CozyBackdrop``) with a mood tint,
* drifting ambient particles (motes / embers / ash),
* a storybook panel with a progressive text reveal,
* stat read-outs with a preparedness bar, and
* a themed footer with page pips and a wooden navigation button.

A subclass only describes its pages (``_build_pages``) and picks a mood
(``accent``, ``mood``, ``particle_kind``, ``emblem``). Everything else -
input, animation, layout, sound - lives here so all three endings stay
consistent.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pygame

from src.core import audio, settings
from src.states.base_state import BaseState
from src.ui import theme
from src.ui.text_utils import wrap_text

W, H = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

# ----------------------------------------------------------------------
# Layout (all in 320x180 canvas pixels)
# ----------------------------------------------------------------------
HEADER_H = 28
PANEL = pygame.Rect(10, 30, 300, 114)
CONTENT_TOP = PANEL.y + 30          # first content row (below title + sub)
CONTENT_BOTTOM = PANEL.bottom - 6   # last usable row
FOOTER_Y = 146
NAV_RECT = pygame.Rect(192, 152, 116, 20)

# Page-turn timing (seconds).
REVEAL_STEP = 0.09                  # delay between revealed lines
INTRO_TIME = 0.55                   # open fade
FLASH_TIME = 0.22                   # page-turn flash


class EndingState(BaseState):
    """Base class for a polished, multi-page ending screen."""

    # --- subclass configuration --------------------------------------
    ending_id: str = ""
    title: str = ""
    subtitle: str = ""
    accent: Tuple[int, int, int] = theme.HONEY
    mood: Tuple[int, int, int] = (0, 0, 0)
    mood_alpha: int = 0
    particle_kind: str = "mote"     # "mote" | "ember" | "ash"
    emblem: str = "medal"           # "medal" | "shield" | "warning"

    def __init__(self, game, summary: Dict[str, Any]):
        super().__init__(game)
        self.summary = summary or {}
        self.pages: List[Dict[str, Any]] = self._build_pages()
        self.max_pages = max(1, len(self.pages))
        self.page = 0
        self.timer = 0.0
        self.page_time = 0.0
        self._intro = 1.0
        self._flash = 0.0
        self._nav_hover = False

        self._backdrop = theme.CozyBackdrop(seed=abs(hash(self.ending_id)) % 997 + 3)
        self._rng = random.Random(abs(hash(self.ending_id)) % 97 + 1)
        self._particles: List[List[float]] = [
            self._spawn_particle(initial=True) for _ in range(26)
        ]

    # ------------------------------------------------------------------
    # Content (subclasses override)
    # ------------------------------------------------------------------
    def _build_pages(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def enter(self) -> None:
        self._intro = 1.0
        audio.play("whoosh", 0.35)

    def update(self, dt: float) -> None:
        self.timer += dt
        self.page_time += dt
        self._intro = max(0.0, self._intro - dt / INTRO_TIME)
        self._flash = max(0.0, self._flash - dt)
        self._update_particles(dt)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                self._advance()
                return True
            if event.key == pygame.K_ESCAPE:
                self._exit_to_menu()
                return True
        elif event.type == pygame.MOUSEMOTION:
            self._nav_hover = NAV_RECT.collidepoint(self._to_canvas(event.pos))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if NAV_RECT.collidepoint(self._to_canvas(event.pos)):
                self._advance()
                return True
        return False

    def _to_canvas(self, pos) -> Tuple[int, int]:
        fn = getattr(self.game, "to_canvas_pos", None)
        return fn(pos) if callable(fn) else pos

    def _advance(self) -> None:
        if self.page >= self.max_pages - 1:
            audio.play("confirm", 0.5)
            self._exit_to_menu()
            return
        self.page += 1
        self.page_time = 0.0
        self._flash = FLASH_TIME
        audio.play("tick", 0.4)

    def _exit_to_menu(self) -> None:
        from src.states.main_menu import MainMenu
        self.game.state_manager.change(MainMenu(self.game))

    def _nav_label(self) -> str:
        return "NEXT PAGE  >" if self.page < self.max_pages - 1 else "RETURN TO TITLE"

    # ------------------------------------------------------------------
    # Particles
    # ------------------------------------------------------------------
    def _spawn_particle(self, initial: bool = False) -> List[float]:
        r = self._rng
        if initial:
            x, y = r.uniform(0, W), r.uniform(0, H)
        else:
            x, y = r.uniform(0, W), H + 4 if self.particle_kind != "ash" else -4
        return [x, y, r.uniform(5, 16), r.choice((1, 1, 2)), r.uniform(0, math.tau)]

    def _update_particles(self, dt: float) -> None:
        rising = self.particle_kind != "ash"
        for i, p in enumerate(self._particles):
            p[1] += (-p[2] if rising else p[2]) * dt
            p[0] += math.sin(self.timer * 1.6 + p[4]) * 6.0 * dt
            if p[1] < -6 or p[1] > H + 6:
                self._particles[i] = self._spawn_particle()

    def _draw_particles(self, surface: pygame.Surface) -> None:
        kind = self.particle_kind
        for x, y, _sp, size, phase in self._particles:
            glow = 0.55 + 0.45 * math.sin(self.timer * 3 + phase)
            if kind == "ember":
                color = theme.mix(theme.CORAL, theme.HONEY, glow)
            elif kind == "ash":
                color = theme.mix(theme.CREAM_DIM, theme.PLUM_LIGHT, glow)
            else:
                color = theme.mix(theme.CREAM_DIM, theme.HONEY, glow)
            surface.fill(color, (int(x), int(y), size, size))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        page = self.pages[min(self.page, self.max_pages - 1)]

        self._backdrop.draw(surface, self.timer)
        if self.mood_alpha:
            tint = pygame.Surface((W, H), pygame.SRCALPHA)
            tint.fill((*self.mood, self.mood_alpha))
            surface.blit(tint, (0, 0))
        self._draw_particles(surface)

        self._draw_header(surface)

        theme.draw_panel(surface, PANEL, title=page.get("heading", ""),
                         accent=self.accent, alpha=244)
        sub = page.get("sub", "")
        if sub:
            theme.draw_text(surface, sub, (PANEL.centerx, PANEL.y + 18), "tiny",
                            theme.CREAM_DIM, anchor="midtop", shadow=False)

        rows_top = CONTENT_TOP
        if page.get("bar"):
            self._draw_bar(surface, page["bar"])
            rows_top = CONTENT_TOP + 28
        if page.get("stats"):
            self._draw_stats(surface, page["stats"], rows_top)
        if page.get("body"):
            self._draw_body(surface, page["body"], rows_top)

        self._draw_footer(surface)
        self._draw_overlays(surface)

    def _draw_header(self, surface: pygame.Surface) -> None:
        strip = pygame.Surface((W, HEADER_H), pygame.SRCALPHA)
        strip.fill((*theme.SHADOW, 155))
        surface.blit(strip, (0, 0))
        pygame.draw.line(surface, theme.mix(theme.PLUM_LIGHT, self.accent, 0.6),
                         (0, HEADER_H - 1), (W, HEADER_H - 1), 1)
        self._draw_emblem(surface, 21, 14)
        theme.draw_text(surface, self.title, (W // 2, 3), "small", self.accent,
                        anchor="midtop", shadow=True)
        theme.draw_text(surface, self.subtitle, (W // 2, 17), "tiny",
                        theme.CREAM_DIM, anchor="midtop", shadow=False)

    def _draw_body(self, surface: pygame.Surface, entries: Sequence[str], top: int) -> None:
        gap = theme.line_height("tiny") + 2
        lines: List[str] = []
        for entry in entries:
            lines.extend(wrap_text(entry, "tiny", PANEL.w - 20))
        room = max(0, (CONTENT_BOTTOM - top) // gap)
        lines = lines[:room]
        shown = int(self.page_time / REVEAL_STEP) + 2
        for i, line in enumerate(lines):
            if i >= shown:
                break
            theme.draw_text(surface, line, (PANEL.x + 10, top + i * gap), "tiny",
                            theme.CREAM, anchor="topleft", shadow=False)

    def _draw_stats(self, surface: pygame.Surface,
                    stats: Sequence[Sequence[Any]], top: int) -> None:
        gap = theme.line_height("tiny") + 3
        shown = int(self.page_time / REVEAL_STEP) + 2
        for i, (label, value, color) in enumerate(stats):
            if i >= shown:
                break
            y = top + i * gap
            theme.draw_text(surface, label, (PANEL.x + 10, y), "tiny",
                            theme.CREAM_DIM, anchor="topleft", shadow=False)
            theme.draw_text(surface, str(value), (PANEL.right - 10, y), "tiny",
                            color, anchor="topright", shadow=False)

    def _draw_bar(self, surface: pygame.Surface, bar: Sequence[Any]) -> None:
        label, ratio, color = bar
        ratio = max(0.0, min(1.0, float(ratio)))
        theme.draw_text(surface, label, (PANEL.x + 10, CONTENT_TOP - 2), "tiny",
                        theme.CREAM, anchor="topleft", shadow=False)
        theme.draw_text(surface, f"{int(round(ratio * 100))}%",
                        (PANEL.right - 10, CONTENT_TOP - 2), "tiny", color,
                        anchor="topright", shadow=False)
        rect = pygame.Rect(PANEL.x + 10, CONTENT_TOP + 10, PANEL.w - 20, 8)
        theme.draw_bar(surface, rect, ratio * 100, 100, color)

    def _draw_footer(self, surface: pygame.Surface) -> None:
        strip = pygame.Surface((W, H - FOOTER_Y), pygame.SRCALPHA)
        strip.fill((*theme.SHADOW, 125))
        surface.blit(strip, (0, FOOTER_Y))
        theme.draw_text(surface, f"PAGE {self.page + 1} / {self.max_pages}",
                        (16, FOOTER_Y + 4), "tiny", theme.CREAM_DIM,
                        anchor="topleft", shadow=False)
        for i in range(self.max_pages):
            cx, cy = 18 + i * 10, FOOTER_Y + 22
            color = self.accent if i == self.page else theme.PLUM_LIGHT
            pygame.draw.rect(surface, color, (cx - 2, cy - 2, 4, 4))
        theme.draw_button(surface, NAV_RECT, self._nav_label(),
                          selected=self._nav_hover, t=self.timer)

    def _draw_overlays(self, surface: pygame.Surface) -> None:
        if self._flash > 0:
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((*self.accent, int(80 * (self._flash / FLASH_TIME))))
            surface.blit(flash, (0, 0))
        if self._intro > 0:
            fade = pygame.Surface((W, H), pygame.SRCALPHA)
            fade.fill((*theme.SHADOW, int(210 * self._intro)))
            surface.blit(fade, (0, 0))

    # ------------------------------------------------------------------
    # Code-drawn ending emblems (no image assets)
    # ------------------------------------------------------------------
    def _draw_emblem(self, surface: pygame.Surface, cx: int, cy: int) -> None:
        if self.emblem == "medal":
            self._emblem_medal(surface, cx, cy)
        elif self.emblem == "shield":
            self._emblem_shield(surface, cx, cy)
        else:
            self._emblem_warning(surface, cx, cy)

    @staticmethod
    def _star(surface, color, cx, cy, r, points=5, inner=0.45):
        pts = []
        for i in range(points * 2):
            ang = -math.pi / 2 + i * math.pi / points
            rad = r if i % 2 == 0 else r * inner
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pygame.draw.polygon(surface, color, pts)

    def _emblem_medal(self, surface, cx, cy):
        pygame.draw.polygon(surface, theme.CORAL,
                            [(cx - 5, cy - 10), (cx - 1, cy - 4), (cx - 5, cy - 1)])
        pygame.draw.polygon(surface, theme.SKY,
                            [(cx + 5, cy - 10), (cx + 1, cy - 4), (cx + 5, cy - 1)])
        pygame.draw.circle(surface, theme.BRASS, (cx, cy + 2), 6)
        pygame.draw.circle(surface, theme.HONEY, (cx, cy + 2), 4)
        self._star(surface, theme.CREAM, cx, cy + 2, 3)

    def _emblem_shield(self, surface, cx, cy):
        pts = [(cx, cy - 9), (cx + 8, cy - 5), (cx + 7, cy + 3),
               (cx, cy + 9), (cx - 7, cy + 3), (cx - 8, cy - 5)]
        pygame.draw.polygon(surface, theme.WOOD, pts)
        pygame.draw.polygon(surface, theme.BRASS, pts, 1)
        pygame.draw.line(surface, theme.SHADOW, (cx - 1, cy - 6), (cx + 1, cy), 1)
        pygame.draw.line(surface, theme.SHADOW, (cx + 1, cy), (cx - 2, cy + 6), 1)

    def _emblem_warning(self, surface, cx, cy):
        pygame.draw.polygon(surface, theme.HONEY,
                            [(cx, cy - 10), (cx + 10, cy + 8), (cx - 10, cy + 8)])
        pygame.draw.polygon(surface, theme.SHADOW,
                            [(cx, cy - 10), (cx + 10, cy + 8), (cx - 10, cy + 8)], 1)
        pygame.draw.rect(surface, theme.SHADOW, (cx - 1, cy - 3, 2, 6))
        pygame.draw.rect(surface, theme.SHADOW, (cx - 1, cy + 4, 2, 2))
