"""Chapter 1 - Level 4: Tsunami Surge (Mount Dayaw Summit). Interactive version.

Location: Mount Dayaw Summit Trail.
Disaster: Catastrophic Tsunami Surge.

What the player does:
  0. Grab the BATTERY BANK at the start and climb to the second tier of the
     switchback (avoid the INUNDATION ZONE, NEXT WAVE countdown).
  1. Bring the battery bank to Rico, then choose the safe answer (decision).
  2. Reach the Sanctuary and broadcast on the VHF RADIO. Ends the level.
"""

import math
import pygame
from src.story.base_level import BaseLevel, RadioTuning
from src.maps.block_map import BlockMap
from src.hazards.landslide import TsunamiHazard
from src.config.palette import COLOR_GROUND_PLATEAU


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (50, 180)
SAFE_TRIGGER = "dayaw_safe"

# Uses "firstaid", the item id your prologue already proves works.
BATTERY_ITEM = ("firstaid", "BATTERY BANK", 90, 182)
CHECKPOINT_RECT = (240, 112, 24, 28)    # start of the second tier
INUNDATION_RECT = (0, 220, 640, 140)
RADIO_RECT = (500, 110, 16, 10)
COLOR_RADIO = (80, 200, 120)

INUNDATION_VISUAL = True    # set False if TsunamiHazard already draws its own water

WAVE_SECONDS = 80.0
WAVE_RETRY_SECONDS = 40.0

RICO_LINES = [
    "The wave hit the harbor jetty at over eighty kilometers per hour!",
    "All landlines and mobile towers along the coast just collapsed!",
    "Help me carry the battery bank for the VHF radio to the summit shelter!",
]

HINTS = {
    1: "Find Rico on the upper trail. Bring the BATTERY BANK!",
    2: "Reach the Sanctuary and use the VHF RADIO.",
}

C_SEA = (40, 90, 140)
C_SEA_GLINT = (150, 200, 230)
C_ROOF = (160, 60, 50)
C_TRUNK = (90, 64, 40)
C_PINE = (36, 88, 66)
C_PINE_LIGHT = (52, 110, 84)
C_POLE = (70, 70, 78)
C_FENCE = (120, 90, 55)

# Floating debris: (start_x, y, w, h, color, drift_speed)
DEBRIS = [
    (60, 262, 10, 6, (150, 110, 60), 12.0),
    (250, 250, 16, 3, (120, 90, 55), 16.0),
    (380, 270, 8, 7, (60, 90, 160), 10.0),
    (500, 254, 12, 4, (120, 90, 55), 14.0),
    (600, 276, 9, 6, (200, 200, 205), 11.0),
]


class Chapter1Level4Tsunami(BaseLevel):
    _t = 0.0
    _tint = None

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_4_tsunami",
            title="Chapter 1 - Level 4: The Inundation",
            subtitle="Mount Dayaw Summit - Vertical Evacuation",
            disaster_type="Tsunami Surge (Extreme Danger)",
            lesson_source="DOST-PHIVOLCS & IOC-UNESCO Tsunami Ready Program Standards",
            lesson_text=(
                "A tsunami is not a single wave, but a series of waves arriving over several hours.\n"
                "The first wave is rarely the largest; later waves can be vastly more destructive.\n"
                "Never return to the lowland coast after the first wave recedes.\n"
                "Remain at high elevation until the official 'All Clear' is broadcast by PHIVOLCS/MDRRMC."
            ),
        )
        self._has_pack = False
        self._radio_hint_shown = False
        self._build_world()
        self.hazards.append(TsunamiHazard())
        self.objectives = [
            "You climb the switchback with the BATTERY BANK",
            "You bring the battery bank to Rico dela Cruz",
            "You use the VHF RADIO at the Sanctuary",
        ]
        self.guide_points = [
            lambda: next(
                (it.rect.center for it in self.block_map.items
                 if it.item_id == BATTERY_ITEM[0] and not it.collected),
                BATTERY_ITEM[2:4],
            ),
            self.guide_npc("Rico dela Cruz"),
            self.guide_interactable("radio"),
        ]
        self.show_hint("Grab the BATTERY BANK, then climb away from the valley!", 6.0)
        self.start_countdown(WAVE_SECONDS, "NEXT WAVE", self._on_wave)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Mount Dayaw Summit Trail", width=MAP_W, height=MAP_H,
                                  ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # Lower valley inundated by the surge
        bm.add_hazard_zone("tsunami", *INUNDATION_RECT, label="TSUNAMI INUNDATION ZONE")

        # Ascending switchback trail
        bm.add_path(40, 170, 240, 30)
        bm.add_path(240, 110, 220, 30)
        bm.add_path(420, 50, 180, 30)

        # High elevation sanctuary
        bm.add_building("shelter", "DAYAW SANCTUARY", 460, 40, 120, 65)
        bm.add_safe_zone(460, 40, 120, 65, label="HIGH GROUND SANCTUARY", trigger_id=SAFE_TRIGGER)

        # Battery pickup, radio, and watches
        bm.add_item(*BATTERY_ITEM)

        # Optional supply pickup
        self.add_pickup("torch", "TORCH", (150, 185), "flashlight")
        self.add_interactable("radio", "VHF RADIO", RADIO_RECT, COLOR_RADIO, self._use_radio)
        self.watch_zone(INUNDATION_RECT, self._on_enter_inundation)
        self.watch_zone(CHECKPOINT_RECT, self._on_checkpoint)

        # NPC
        self.add_npc("rico_dela_cruz", "Rico dela Cruz", (270, 95), RICO_LINES, role="resident")

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
        if idx >= 2:
            self.stop_countdown()

    def _on_wave(self):
        self.record_score("evacuations_delayed")
        self.show_hint("Another wave is coming! Keep climbing!", 4.0)
        self.start_countdown(WAVE_RETRY_SECONDS, "NEXT WAVE", self._on_wave)

    # ------------------------------------------------------------------
    # Step 0: battery bank, inundation zone, switchback checkpoint
    # ------------------------------------------------------------------
    def on_item_collected(self, item_id: str):
        if item_id == BATTERY_ITEM[0]:
            self._has_pack = True
            self.show_hint("Got the BATTERY BANK! Now climb the switchback.", 4.0)

    def _on_enter_inundation(self):
        self.record_score("unsafe_actions")
        self.show_hint("INUNDATION ZONE! Surge water and debris. Stay uphill!", 4.5)

    def _on_checkpoint(self):
        if self.current_objective_idx == 0:
            if self._has_pack:
                self._next()
            else:
                self.show_hint("Go back for the BATTERY BANK near the trail start.", 4.0)

    # ------------------------------------------------------------------
    # Step 1: Rico (decision)
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Rico dela Cruz":
            return
        idx = self.current_objective_idx
        if idx < 1:
            self.show_hint("Climb the switchback first.", 3.5)
        elif idx == 1:
            self._ask_about_return()

    def _ask_about_return(self):
        def on_safe():
            self.score_system.assist_resident("Rico dela Cruz")
            self._next()

        self.ask(
            decision_id="tsunami_after_wave_choice",
            prompt="The first wave receded. Someone wants their vehicle back:",
            options=[
                {
                    "text": "Forbid it; later waves can be even higher",
                    "safe": True,
                    "lesson": "Tsunami crests can arrive 10 to 60 minutes apart.",
                },
                {
                    "text": "Let them run down before the water returns",
                    "safe": False,
                    "lesson": "Returning too early is a leading cause of tsunami deaths.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Nobody goes down until the official All Clear.",
        )

    # ------------------------------------------------------------------
    # Step 2: sanctuary and radio, ends the level
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if (trigger_id == SAFE_TRIGGER and self.current_objective_idx == 2
                and not self._radio_hint_shown):
            self._radio_hint_shown = True
            self.show_hint("Sanctuary reached! Use the VHF RADIO to call for help.", 5.0)

    def _use_radio(self, item):
        idx = self.current_objective_idx
        if idx < 2:
            self.show_hint("The radio needs the battery bank. Help Rico first.", 3.5)
            return
        self.start_minigame(
            RadioTuning(
                title="VHF MAYDAY",
                target_channel="VHF CH 16 (156.8 MHz)",
                speed=1.0,
                zone=0.26,
                rounds=2,
                win_text="MAYDAY SENT!",
                fail_text="STATIC - RETUNE!",
            ),
            on_win=lambda: self._radio_done(item),
            on_fail=lambda: self.show_hint("Signal lost. Try the VHF RADIO again.", 3.0),
        )

    def _radio_done(self, item):
        item["done"] = True
        self.record_score("hazards_reported")
        self.score_system.complete_evacuation("ch1_4")
        self.show_hint("MAYDAY sent! Rescue teams are on the way.", 4.0)
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
            tint.fill((15, 25, 55, 70))
            for i in range(6):
                pygame.draw.rect(tint, (0, 0, 0, 14), (i * 3, i * 3, w - i * 6, h - i * 6), 3)
            self._tint = tint
        surface.blit(self._tint, (0, 0))
        super()._draw_hud(surface)

    def _draw_interactables(self, surface):
        self._draw_scenery(surface)
        super()._draw_interactables(surface)

    def _pine(self, s, x, y):
        px, py = self._p(x, y)
        cx = px + 2 + int(math.sin(self._t * 1.4 + x) * 1)
        pygame.draw.rect(s, C_TRUNK, (px, py, 4, 14))
        for i in range(3):
            half = 9 - 2 * i
            base = py + 2 - i * 7
            pygame.draw.polygon(s, C_PINE, [(cx - half, base), (cx, base - 11), (cx + half, base)])
            pygame.draw.line(s, C_PINE_LIGHT, (cx, base - 11), (cx + half, base))

    def _fence(self, s, x, y, n):
        for i in range(n):
            px, py = self._p(x + i * 8, y)
            pygame.draw.rect(s, C_FENCE, (px, py, 2, 9))
            if i + 1 < n:
                pygame.draw.line(s, C_FENCE, (px, py + 3), (px + 8, py + 3))
                pygame.draw.line(s, C_FENCE, (px, py + 6), (px + 8, py + 6))

    def _surge(self, s, x, y, w, h):
        """Flat pixel floodwater with fast ripples and a foam edge."""
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
                lx = sr.left + (k + row * 11 - int(t * 14)) % max(1, w)
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

        # retaining walls under each trail tier
        for x, y, w in ((40, 200, 240), (240, 140, 220), (420, 80, 180)):
            pygame.draw.rect(s, (70, 68, 74), R(x, y, w, 5))
            for rx in range(x, x + w, 12):
                pygame.draw.line(s, (50, 48, 54), P(rx, y), P(rx, y + 4))
        self._fence(s, 40, 163, 30)
        self._fence(s, 240, 103, 27)

        # wrecked houses and a capsized boat, with the surge drawn over them
        if INUNDATION_VISUAL:
            for hx, hy in ((90, 240), (210, 252), (430, 242)):
                pts = [P(hx, hy + 8), P(hx + 20, hy - 8), P(hx + 40, hy + 8)]
                pygame.draw.polygon(s, C_ROOF, pts)
                pygame.draw.polygon(s, (100, 40, 34), pts, 1)
                pygame.draw.rect(s, (110, 110, 118), R(hx + 28, hy - 6, 4, 8))
            bx, by = P(330, 262)
            hull = [(bx, by), (bx + 30, by), (bx + 24, by + 8), (bx + 6, by + 8)]
            pygame.draw.polygon(s, (225, 225, 230), hull)
            pygame.draw.polygon(s, (90, 90, 100), hull, 1)

            self._surge(s, 0, 224, 640, 136)

            for bx0, by0, w, h, col, drift in DEBRIS:
                x = (bx0 - t * drift) % 620 + 10
                y = by0 + math.sin(t * 2 + bx0) * 1.5
                r = R(int(x), int(y), w, h)
                pygame.draw.rect(s, col, r)
                pygame.draw.rect(s, (30, 30, 36), r, 1)

        # pines on the mountainside
        for x, y in ((20, 130), (200, 70), (330, 62), (600, 110), (620, 150)):
            self._pine(s, x, y)

        # emergency sign (plain board with an arrow, no text)
        sg = R(284, 150, 56, 11)
        pygame.draw.rect(s, (40, 130, 80), sg)
        pygame.draw.rect(s, (230, 240, 230), sg, 1)
        pygame.draw.rect(s, C_POLE, (sg.centerx - 1, sg.bottom, 2, 8))
        pygame.draw.lines(s, (240, 250, 240), False,
                          [(sg.centerx - 8, sg.centery), (sg.centerx + 8, sg.centery)], 1)
        pygame.draw.lines(s, (240, 250, 240), False,
                          [(sg.centerx + 4, sg.centery - 3), (sg.centerx + 8, sg.centery),
                           (sg.centerx + 4, sg.centery + 3)], 1)

        # sanctuary: banner, antenna, dish
        pygame.draw.rect(s, (60, 140, 90), R(480, 46, 80, 6))
        for x in range(484, 556, 8):
            pygame.draw.rect(s, (230, 240, 230), R(x, 48, 4, 2))
        ax, ay = P(570, 40)
        pygame.draw.line(s, (90, 90, 100), (ax, ay), (ax, ay - 30), 1)
        if int(t * 2) % 2 == 0:
            pygame.draw.circle(s, (255, 60, 60), (ax, ay - 31), 2)
        dx, dy = P(520, 98)
        pygame.draw.ellipse(s, (200, 200, 210), (dx, dy, 12, 8))
        pygame.draw.line(s, (90, 90, 100), (dx + 6, dy + 8), (dx + 6, dy + 14), 1)

        # relief tents and villagers on the summit
        for tx, ty in ((586, 90), (604, 96)):
            r = R(tx, ty, 18, 12)
            tent = [(r.left, r.bottom), (r.centerx, r.top), (r.right, r.bottom)]
            pygame.draw.polygon(s, (214, 120, 60), tent)
            pygame.draw.polygon(s, (150, 80, 40), tent, 1)
        for vx, vy, col in ((570, 112, (190, 90, 70)), (584, 116, (70, 120, 180)), (598, 112, (80, 150, 90))):
            px, py = P(vx, vy)
            pygame.draw.circle(s, (230, 190, 150), (px + 3, py + 2), 2)
            pygame.draw.rect(s, col, (px + 1, py + 4, 5, 7))
            pygame.draw.rect(s, (50, 50, 60), (px + 1, py + 11, 2, 3))
            pygame.draw.rect(s, (50, 50, 60), (px + 4, py + 11, 2, 3))

        # guide arrows for the current step
        idx = self.current_objective_idx
        if idx == 0:
            self._arrows(s, 130, 185, 5, 16)
        elif idx == 2:
            self._arrows(s, 340, 65, 5, 14)