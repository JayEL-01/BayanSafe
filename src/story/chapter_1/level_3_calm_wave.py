"""Chapter 1 - Level 3: The Calm Before the Wave (North West Plateau). Interactive version.

Location: Plateau Coastal Overlook.
Disaster: Natural Pre-Tsunami Anomaly (Sea Water Drawback).

What the player does:
  0. Observe the receding sea at the VIEWPOINT.
  1. Warn Tatay Pio and the villagers (decision).
  2. Talk to Berto, then sound the SIREN before the wave arrives. Ends the level.
"""

import math
import pygame
from src.story.base_level import BaseLevel, TimingMeter
from src.maps.block_map import BlockMap
from src.config.palette import COLOR_GROUND_PLATEAU


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (60, 175)

VIEWPOINT_RECT = (100, 128, 22, 10)
SIREN_RECT = (456, 128, 14, 14)
SEABED_RECT = (0, 270, 640, 40)

WAVE_SECONDS = 45.0
WAVE_RETRY_SECONDS = 30.0

PIO_LINES = [
    "Look down at the bay! The sea pulled back almost half a kilometer in two minutes!",
    "Look at all those fish flopping on the dry coral reef! Some young folks want to run down with buckets!",
    "In my sixty years of fishing, I have never seen the ocean empty like this...",
]
BERTO_LINES = [
    "Hold the line! That is the classic precursor to a tsunami wall!",
    "We must activate the mechanical siren and order an immediate vertical evacuation!",
]
VIEW_LINES = [
    "The bay is almost empty. Boats lie tilted on the dry seabed.",
    "Corals and fish are exposed far beyond the normal shoreline.",
    "This is a natural tsunami warning sign. Warn people now!",
]

HINTS = {
    1: "Warn Tatay Pio before anyone goes down to the reef!",
    2: "Talk to Berto, then use the SIREN at the post!",
}

C_SAND = (200, 180, 130)
C_SEA = (40, 110, 150)
C_SEA_GLINT = (170, 215, 235)
C_TRUNK = (90, 64, 40)
C_LEAF = (50, 110, 60)
C_LEAF_LIGHT = (72, 140, 78)
C_POLE = (70, 70, 78)
C_FENCE = (120, 90, 55)

FISH = [(110, 300), (200, 288), (300, 304), (380, 282), (470, 298)]
CORALS = [(60, 285), (150, 292), (240, 282), (330, 295), (420, 286), (510, 292), (590, 284)]
VILLAGERS = [(190, 250, (190, 90, 70)), (214, 256, (70, 120, 180)), (236, 252, (80, 150, 90))]


class Chapter1Level3CalmWave(BaseLevel):
    _t = 0.0
    _tint = None

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_3_calm_wave",
            title="Chapter 1 - Level 3: The Sea Recedes",
            subtitle="North West Plateau - The Calm Before the Wave",
            disaster_type="Tsunami Natural Warning (Rapid Drawback)",
            lesson_source="DOST-PHIVOLCS Tsunami Preparedness: Recognize the 3 Natural Signs (Shake, Drop, Roar)",
            lesson_text=(
                "If you feel a strong earthquake near the coast and notice:\n"
                "1. Rapid receding of sea water exposing the ocean floor and corals,\n"
                "2. A loud roaring sound like a jet aircraft approaching from the sea,\n"
                "DO NOT go down to the shore to pick up flopping fish or take photos!\n"
                "RUN IMMEDIATELY to high ground (at least 30 meters above sea level) inland."
            ),
        )
        self._berto_talked = False
        self._warned_at = None
        self._build_world()
        self.objectives = [
            "You observe the sea from the cliff viewpoint",
            "You stop Tatay Pio at the exposed reef",
            "You sound the siren at Berto's outpost",
        ]
        self.guide_points = [
            self.guide_interactable("viewpoint"),
            self.guide_npc("Tatay Pio"),
            self.guide_interactable("siren"),
        ]
        self.show_hint("Something is wrong with the sea. Check the VIEWPOINT!", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Plateau Coastal Overlook", width=MAP_W, height=MAP_H,
                                  ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # High overlook ridge paths
        bm.add_path(40, 160, 560, 36)
        bm.add_path(420, 50, 36, 250)

        # Buildings
        bm.add_building("commercial", "VIEWPOINT SHED", 70, 70, 75, 55)
        bm.add_building("shelter", "COMMUNITY SIREN POST", 400, 60, 90, 65)

        # Sea and exposed seabed
        bm.add_water(0, 310, 640, 50)
        bm.add_hazard_zone("tsunami", *SEABED_RECT, label="EXPOSED DRY SEA BED")

        # Interactables and the seabed warning
        self.add_interactable("viewpoint", "VIEWPOINT", VIEWPOINT_RECT, (120, 200, 220),
                              self._use_viewpoint, alpha=70)
        self.add_interactable("siren", "SIREN", SIREN_RECT, (230, 70, 70), self._use_siren, alpha=90)
        self.add_pickup("binoculars", "COASTAL BINOCULARS", (180, 205), "light")
        self.watch_zone(SEABED_RECT, self._on_enter_seabed)

        # NPCs
        self.add_npc("tatay_pio", "Tatay Pio", (110, 140), PIO_LINES, role="resident")
        self.add_npc("berto", "Berto", (430, 135), BERTO_LINES, role="resident")

        self.player.pos = pygame.Vector2(*PLAYER_SPAWN)
        self.player.rect.topleft = PLAYER_SPAWN

    # ------------------------------------------------------------------
    # Objective flow
    # ------------------------------------------------------------------
    def _next(self):
        self.complete_objective()
        idx = self.current_objective_idx
        if idx in HINTS:
            self.show_hint(HINTS[idx], 5.0)
        if idx == 2:
            self._warned_at = self._t
            self.start_countdown(WAVE_SECONDS, "WAVE ETA", self._on_wave_late)
        else:
            self.stop_countdown()

    def _on_wave_late(self):
        self.record_score("evacuations_delayed")
        self.show_hint("The wave is almost here! Sound the SIREN NOW!", 4.0)
        self.start_countdown(WAVE_RETRY_SECONDS, "WAVE ETA", self._on_wave_late)

    def _on_enter_seabed(self):
        self.record_score("unsafe_actions")
        self.show_hint("DRY SEABED! The wave will return. Never go down to the reef!", 4.5)

    # ------------------------------------------------------------------
    # Step 0: viewpoint
    # ------------------------------------------------------------------
    def _use_viewpoint(self, item):
        if self.current_objective_idx != 0 or item["done"]:
            self.show_hint("The sea is still pulled back. Keep warning people!", 3.0)
            return
        item["done"] = True
        self.start_dialogue("Viewpoint", VIEW_LINES)
        self.start_minigame(
            TimingMeter(
                "SPOT THE WARNING SIGNS", "",
                steps=["Sea level is falling", "The reef is exposed", "A roar is building"],
                speed=0.85, zone=0.28, max_misses=3,
                icon="light", win_text="NATURAL WARNING CONFIRMED!",
            ),
            on_win=self._next,
            on_fail=lambda: self.show_hint("Watch the receding sea again.", 3.0),
        )

    # ------------------------------------------------------------------
    # Step 1: Tatay Pio (decision) and Berto
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        idx = self.current_objective_idx

        if npc.name == "Tatay Pio":
            if idx < 1:
                self.show_hint("Check the bay from the VIEWPOINT first.", 3.5)
            elif idx == 1:
                self._ask_about_warning()

        elif npc.name == "Berto":
            if idx >= 2:
                self._berto_talked = True
            else:
                self.show_hint("Berto is watching the bay. Warn the villagers first.", 3.5)

    def _ask_about_warning(self):
        def on_safe():
            self.score_system.assist_resident("Tatay Pio")
            self._next()

        self.ask(
            decision_id="tsunami_drawback_choice",
            prompt="Villagers stare at the empty bay. Your urgent command?",
            options=[
                {
                    "text": "Shout: 'Tsunami! Run to the high ground now!'",
                    "safe": True,
                    "lesson": "Natural warning signs are cues to self-evacuate before any siren.",
                },
                {
                    "text": "Let people grab the fish and take photos first",
                    "safe": False,
                    "lesson": "Curiosity near a receding coast is the top cause of preventable tsunami deaths.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Never go to the shore to watch. Warn everyone to run uphill.",
        )

    # ------------------------------------------------------------------
    # Step 2: siren, ends the level
    # ------------------------------------------------------------------
    def _use_siren(self, item):
        idx = self.current_objective_idx
        if idx < 2:
            self.show_hint("Not yet. Warn the villagers first.", 3.0)
        elif not self._berto_talked:
            self.show_hint("Talk to Berto first.", 3.0)
        else:
            item["done"] = True
            self.record_score("hazards_reported")
            self.score_system.complete_evacuation("ch1_3")
            self.show_hint("SIREN SOUNDING! Everyone to high ground!", 4.0)
            self._next()

    # ------------------------------------------------------------------
    # Visual polish
    # ------------------------------------------------------------------
    def update(self, dt: float):
        super().update(dt)
        if not (self.legend_screen.visible or self.show_lesson_modal or self.pause_menu.visible):
            self._t += dt

    def _r(self, x, y, w, h):
        return self.camera.apply(pygame.Rect(x, y, w, h))

    def _p(self, x, y):
        return self.camera.apply(pygame.Rect(x, y, 1, 1)).topleft

    def _draw_hud(self, surface):
        w, h = surface.get_size()
        if self._tint is None or self._tint.get_size() != (w, h):
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill((150, 175, 190, 22))
            for i in range(6):
                pygame.draw.rect(tint, (0, 0, 0, 14), (i * 3, i * 3, w - i * 6, h - i * 6), 3)
            self._tint = tint
        surface.blit(self._tint, (0, 0))
        super()._draw_hud(surface)

    def _draw_interactables(self, surface):
        self._draw_scenery(surface)
        super()._draw_interactables(surface)

    def _palm(self, s, x, y):
        px, py = self._p(x, y)
        sway = int(math.sin(self._t * 1.6 + x) * 2)
        top = (px + 3 + sway, py - 16)
        pygame.draw.line(s, C_TRUNK, (px + 2, py + 6), top, 2)
        for dx, dy in ((-9, 3), (-6, -2), (0, -5), (6, -2), (9, 3)):
            pygame.draw.line(s, C_LEAF, top, (top[0] + dx, top[1] + dy), 2)
        pygame.draw.circle(s, C_LEAF_LIGHT, top, 2)

    def _sea(self, s, x, y, w, h):
        """Flat pixel water with scrolling ripples and a foam edge."""
        sr = self._r(x, y, w, h)
        vis = sr.clip(s.get_rect())
        if vis.w <= 0 or vis.h <= 0:
            return
        body = pygame.Surface(vis.size, pygame.SRCALPHA)
        body.fill((*C_SEA, 170))
        s.blit(body, vis.topleft)
        t = self._t
        for row, ry in enumerate(range(sr.top + 5, sr.bottom, 8)):
            if not (vis.top <= ry < vis.bottom):
                continue
            for k in range(0, w, 28):
                lx = sr.left + (k + row * 11 - int(t * 6)) % max(1, w)
                if vis.left <= lx < vis.right - 6:
                    pygame.draw.line(s, C_SEA_GLINT, (lx, ry), (lx + 5, ry))
        foam = (225, 240, 250)
        for px in range(vis.left, vis.right, 2):
            wy = sr.top + int(math.sin(t * 2.0 + (px - sr.left) * 0.15) * 1.2)
            if vis.top <= wy < vis.bottom:
                s.set_at((px, wy), foam)

    def _arrows(self, s, x, y, n, step=14):
        active = int(self._t * 5) % n
        for i in range(n):
            px, py = self._p(x + i * step, y)
            col = (255, 230, 120) if i == active else (200, 170, 60)
            pygame.draw.lines(s, col, False, [(px, py - 4), (px + 4, py), (px, py + 4)], 2)

    def _draw_scenery(self, s):
        t = self._t
        R, P = self._r, self._p

        # exposed seabed: sand, corals, hopping fish, stranded boat
        bed = R(*SEABED_RECT)
        vis = bed.clip(s.get_rect())
        if vis.w > 0 and vis.h > 0:
            sand = pygame.Surface(vis.size, pygame.SRCALPHA)
            sand.fill((*C_SAND, 150))
            s.blit(sand, vis.topleft)
        for i, (cx, cy) in enumerate(CORALS):
            px, py = P(cx, cy)
            col = (230, 110, 140) if i % 2 == 0 else (240, 160, 80)
            for dx, ch in ((-3, 5), (0, 8), (3, 6)):
                pygame.draw.line(s, col, (px + dx, py), (px + dx, py - ch), 2)
        for fx, fy in FISH:
            hop = abs(math.sin(t * 5 + fx)) * 4
            px, py = P(fx, int(fy - hop))
            pygame.draw.rect(s, (200, 210, 220), (px, py, 5, 2))
            pygame.draw.rect(s, (150, 170, 190), (px + 5, py - 1, 2, 4))
        bx, by = P(540, 276)
        pygame.draw.polygon(s, (150, 110, 70), [(bx, by), (bx + 34, by + 6), (bx + 28, by + 14), (bx + 4, by + 10)])
        pygame.draw.line(s, (90, 70, 50), (bx + 17, by + 3), (bx + 12, by - 12), 1)

        # the retreated sea
        self._sea(s, 0, 310, 640, 50)

        # railing along the overlook edge
        for i in range(72):
            px, py = P(30 + i * 8, 240)
            pygame.draw.rect(s, C_FENCE, (px, py, 2, 9))
            if i + 1 < 72:
                pygame.draw.line(s, C_FENCE, (px, py + 3), (px + 8, py + 3))

        # villagers with buckets (they run uphill once warned)
        run = 0 if self._warned_at is None else min(80, (t - self._warned_at) * 30)
        for vx, vy, col in VILLAGERS:
            px, py = P(vx, int(vy - run))
            pygame.draw.circle(s, (230, 190, 150), (px + 3, py + 2), 2)
            pygame.draw.rect(s, col, (px + 1, py + 4, 5, 7))
            pygame.draw.rect(s, (50, 50, 60), (px + 1, py + 11, 2, 3))
            pygame.draw.rect(s, (50, 50, 60), (px + 4, py + 11, 2, 3))
            pygame.draw.rect(s, (60, 120, 190), (px + 7, py + 8, 3, 3))

        # palms and gulls
        for x, y in ((40, 100), (600, 112), (380, 215), (270, 222)):
            self._palm(s, x, y)
        for i in range(3):
            gx = (t * 18 + i * 110) % 700 - 30
            gy = 22 + i * 7 + math.sin(t * 2 + i) * 3
            px, py = P(int(gx), int(gy))
            pygame.draw.lines(s, (235, 235, 240), False, [(px - 3, py), (px, py + 2), (px + 3, py)], 1)

        # tsunami hazard sign (plain board, no text so it can't clash with labels)
        sg = R(520, 204, 52, 11)
        pygame.draw.rect(s, (40, 90, 150), sg)
        pygame.draw.rect(s, (230, 240, 230), sg, 1)
        pygame.draw.rect(s, C_POLE, (sg.centerx - 1, sg.bottom, 2, 8))
        for k in range(3):
            pygame.draw.line(s, (230, 240, 250), (sg.x + 8 + k * 14, sg.centery + 2),
                             (sg.x + 12 + k * 14, sg.centery - 2), 1)

        # telescope at the viewpoint
        tx, ty = P(112, 128)
        pygame.draw.line(s, (60, 60, 66), (tx - 3, ty + 12), (tx, ty + 4), 1)
        pygame.draw.line(s, (60, 60, 66), (tx + 3, ty + 12), (tx, ty + 4), 1)
        pygame.draw.line(s, (200, 200, 205), (tx, ty + 4), (tx + 8, ty - 1), 2)

        # siren horn on the post roof (blinks once the wave is imminent)
        hx, hy = P(440, 52)
        pygame.draw.rect(s, (90, 90, 100), (hx, hy, 3, 8))
        pygame.draw.polygon(s, (200, 200, 210), [(hx, hy), (hx + 10, hy - 4), (hx + 10, hy + 4)])
        if self.current_objective_idx >= 2 and int(t * 3) % 2 == 0:
            pygame.draw.circle(s, (255, 60, 60), (hx + 1, hy - 3), 2)

        # evacuation route arrows after the warning
        if self.current_objective_idx == 2:
            self._arrows(s, 340, 178, 5, 14)