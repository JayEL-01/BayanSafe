"""Chapter 1 - Level 1: Highland Tremor (North West Plateau). Interactive version.

Location: North West Highland Plateau (Mount Dayaw Foothills).
Disaster: Earthquake (PHIVOLCS PEIS Intensity VI - Very Strong).

What the player does:
  0. The ground is shaking: reach the SCHOOL DESK and choose Drop-Cover-Hold
     (SHAKING countdown, avoid the FALLING DEBRIS by the barn).
  1. Talk to Sari and choose how to lead her out safely.
  2. Muster at the open field before the next AFTERSHOCK. Ends the level.
"""

import math
import pygame
from src.story.base_level import BaseLevel, Mash
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.config.palette import COLOR_GROUND_PLATEAU


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (80, 175)
SAFE_TRIGGER = "open_field"

DESK_RECT = (86, 158, 22, 10)
COLOR_DESK = (150, 100, 60)
DEBRIS_RECT = (195, 118, 90, 26)

SHAKE_SECONDS = 25.0          # time to take cover
AFTERSHOCK_SECONDS = 60.0     # time to reach the field
AFTERSHOCK_RETRY_SECONDS = 40.0

SARI_LINES = [
    "The blackboard was shaking so loudly! We were reading our textbooks when it hit!",
    "Our teacher told us to protect our heads under our desks.",
    "Can you help me get to the open grass field? I want to wait for my family there.",
]

HINTS = {
    1: "Safe! Now find Sari near the school and talk to her.",
    2: "Lead Sari to the OPEN FIELD, away from poles and walls!",
}

C_RIDGE = (88, 104, 96)
C_BRICK = (150, 70, 55)
C_TRUNK = (90, 64, 40)
C_PINE = (36, 88, 66)
C_PINE_LIGHT = (52, 110, 84)
C_POLE = (70, 70, 78)
C_WIRE = (40, 40, 46)
C_FENCE = (120, 90, 55)
C_CRACK = (34, 26, 22)


class Chapter1Level1Earthquake(BaseLevel):
    _t = 0.0
    _tint = None

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_1_earthquake",
            title="Chapter 1 - Level 1: The Shaking Highland",
            subtitle="North West Plateau - Tectonic Tremor",
            disaster_type="Earthquake (PEIS Intensity VI)",
            lesson_source="DOST-PHIVOLCS Earthquake Preparedness Guide & Duck-Cover-Hold Protocol",
            lesson_text=(
                "During an earthquake, immediately DROP to hands and knees,\n"
                "COVER your head and neck under a sturdy table or desk,\n"
                "and HOLD ON until the violent shaking completely ceases.\n"
                "Once shaking stops, evacuate to an open field away from facades and power poles."
            ),
        )
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=6))
        self.objectives = [
            "You take cover at the school desk",
            "You assist Sari near the plateau schoolhouse",
            "You muster at the open field beside the school",
        ]
        self.guide_points = [
            self.guide_interactable("desk"),
            self.guide_npc("Sari"),
            (470, 255),
        ]
        self.show_hint("EARTHQUAKE! Reach the SCHOOL DESK and press SPACE!", 6.0)
        self.start_countdown(SHAKE_SECONDS, "SHAKING", self._on_shake_timeout)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("North West Plateau - Village", width=MAP_W, height=MAP_H,
                                  ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # Plateau paths and trails
        bm.add_path(50, 160, 540, 36)
        bm.add_path(260, 40, 36, 260)

        # School and masonry buildings
        bm.add_building("house", "PLATEAU SCHOOL", 70, 60, 95, 65)
        bm.add_building("damaged_house", "DAMAGED BARN", 200, 60, 80, 60)
        bm.add_building("house", "FARM HOUSE", 380, 60, 75, 55)

        # Falling debris beside the damaged barn + open field safe zone
        bm.add_hazard_zone("debris", *DEBRIS_RECT, label="FALLING DEBRIS")
        bm.add_safe_zone(380, 200, 180, 110, label="OPEN RECREATION FIELD", trigger_id=SAFE_TRIGGER)

        # Desk (interactable) and the debris warning
        self.add_interactable("desk", "SCHOOL DESK", DESK_RECT, COLOR_DESK, self._use_desk)
        self.add_pickup("helmet", "SCHOOL HELMET", (120, 205), "hardhat")
        self.watch_zone(DEBRIS_RECT, self._on_enter_debris)

        # NPCs
        self.add_npc("sari", "Sari", (115, 135), SARI_LINES, role="vulnerable")

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
            self.start_countdown(AFTERSHOCK_SECONDS, "AFTERSHOCK", self._on_aftershock)
        else:
            self.stop_countdown()

    def _on_shake_timeout(self):
        self.record_score("unsafe_actions")
        self.show_hint("Still shaking! Get to the SCHOOL DESK and take cover!", 4.0)
        self.start_countdown(SHAKE_SECONDS, "SHAKING", self._on_shake_timeout)

    def _on_aftershock(self):
        self.record_score("evacuations_delayed")
        self.show_hint("AFTERSHOCK! Keep moving to the open field!", 4.0)
        self.start_countdown(AFTERSHOCK_RETRY_SECONDS, "AFTERSHOCK", self._on_aftershock)

    def _on_enter_debris(self):
        self.record_score("unsafe_actions")
        self.show_hint("FALLING DEBRIS! Stay clear of the damaged barn wall!", 4.5)

    # ------------------------------------------------------------------
    # Step 0: take cover (decision)
    # ------------------------------------------------------------------
    def _use_desk(self, item):
        if self.current_objective_idx > 0 or item["done"]:
            self.show_hint("You already took cover. Stay alert for aftershocks.", 3.0)
            return

        def on_safe():
            self.start_minigame(
                Mash(
                    "HOLD ON", "Mash SPACE to hold the desk steady!",
                    target=8, decay=1.8, time_limit=6.0,
                    icon="hardhat", win_text="YOU HELD ON!",
                ),
                on_win=lambda: self._desk_secured(item),
                on_fail=lambda: self.show_hint("Keep holding! Try again.", 3.0),
            )

        self.ask(
            decision_id="earthquake_cover_choice",
            prompt="The ground is shaking hard! What do you do?",
            options=[
                {
                    "text": "DROP, COVER and HOLD ON under the sturdy desk",
                    "safe": True,
                    "lesson": "Protecting the head and neck from falling debris is paramount.",
                },
                {
                    "text": "Run out the door through the falling debris",
                    "safe": False,
                    "lesson": "Running during shaking causes falls, and facades can collapse outward.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Don't run during shaking. Drop, cover and hold!",
        )

    def _desk_secured(self, item):
        item["done"] = True
        self._next()

    # ------------------------------------------------------------------
    # Step 1: Sari (decision)
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Sari":
            return
        idx = self.current_objective_idx
        if idx < 1:
            self.show_hint("Take cover at the SCHOOL DESK first!", 3.5)
        elif idx == 1:
            self._ask_about_escape()

    def _ask_about_escape(self):
        def on_safe():
            self.score_system.assist_resident("Sari")
            self._next()

        self.ask(
            decision_id="earthquake_escape_choice",
            prompt="Aftershocks rumble on. How do you lead Sari out?",
            options=[
                {
                    "text": "Cover heads with bags, walk in single file to the field",
                    "safe": True,
                    "lesson": "Protecting the head from falling glass and masonry is paramount.",
                },
                {
                    "text": "Run down the hall, looking up at the swinging fans",
                    "safe": False,
                    "lesson": "Running frantically during tremors causes stampedes and falls.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Running in a panic is dangerous. Move calmly, head covered.",
        )

    # ------------------------------------------------------------------
    # Step 2: open field, ends the level
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == SAFE_TRIGGER and self.current_objective_idx == 2:
            self.score_system.complete_evacuation("ch1_1")
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
            tint.fill((40, 34, 24, 38))
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

    def _fence(self, s, x, y, n, broken=()):
        for i in range(n):
            px, py = self._p(x + i * 8, y)
            if i in broken:
                pygame.draw.line(s, C_FENCE, (px, py + 9), (px + 4, py + 3), 2)
                continue
            pygame.draw.rect(s, C_FENCE, (px, py, 2, 9))
            if i + 1 < n and (i + 1) not in broken:
                pygame.draw.line(s, C_FENCE, (px, py + 3), (px + 8, py + 3))
                pygame.draw.line(s, C_FENCE, (px, py + 6), (px + 8, py + 6))

    def _pole(self, s, x, y, h=34, tilt=0):
        bx, by = self._p(x, y + h)
        tx, ty = bx + tilt, by - h
        pygame.draw.line(s, C_POLE, (bx, by), (tx, ty), 2)
        pygame.draw.line(s, C_POLE, (tx - 5, ty + 3), (tx + 5, ty + 3), 1)
        return (tx, ty + 3)

    def _cracks(self, s, pts):
        pygame.draw.lines(s, C_CRACK, False, [self._p(x, y) for x, y in pts], 1)

    def _arrows(self, s, x, y, n, step=14):
        active = int(self._t * 5) % n
        for i in range(n):
            px, py = self._p(x + i * step, y)
            col = (255, 230, 120) if i == active else (200, 170, 60)
            pygame.draw.lines(s, col, False, [(px, py - 4), (px + 4, py), (px, py + 4)], 2)

    def _draw_scenery(self, s):
        t = self._t
        R, P = self._r, self._p

        # distant ridge along the north edge
        ridge = [(0, 40), (50, 18), (95, 32), (150, 8), (205, 30), (260, 14), (330, 36),
                 (400, 12), (470, 30), (540, 10), (600, 28), (640, 20), (640, 40)]
        pygame.draw.polygon(s, C_RIDGE, [P(x, y) for x, y in ridge])
        for cx, cy in ((150, 8), (400, 12), (540, 10)):
            px, py = P(cx, cy)
            pygame.draw.polygon(s, (220, 228, 232), [(px - 5, py + 5), (px, py), (px + 5, py + 5)])

        # pines and a broken fence
        for x, y in ((20, 70), (30, 120), (320, 50), (335, 95), (590, 70), (610, 130), (560, 38)):
            self._pine(s, x, y)
        self._fence(s, 300, 148, 8, broken=(3,))

        # school flag
        fx, fy = P(160, 62)
        pygame.draw.line(s, C_POLE, (fx, fy), (fx, fy - 22), 1)
        wv = int(math.sin(t * 4) * 1)
        pygame.draw.polygon(s, (200, 50, 50), [(fx, fy - 22), (fx + 10 + wv, fy - 20),
                                               (fx + 10 - wv, fy - 17), (fx, fy - 15)])

        # open field markings
        for i in range(0, 6, 2):
            r = R(380 + i * 30, 200, 30, 110)
            band = pygame.Surface(r.size, pygame.SRCALPHA)
            band.fill((255, 255, 255, 14))
            s.blit(band, r.topleft)
        pygame.draw.line(s, (220, 235, 220), P(470, 203), P(470, 307))
        pygame.draw.circle(s, (220, 235, 220), P(470, 255), 14, 1)
        for gx in (384, 552):
            pygame.draw.rect(s, (235, 235, 235), R(gx, 240, 2, 22))
            pygame.draw.rect(s, (235, 235, 235), R(gx - 3, 240, 8, 2))

        # cracks in the ground and the barn wall
        self._cracks(s, [(100, 166), (106, 171), (103, 176), (110, 181), (108, 188)])
        self._cracks(s, [(180, 174), (188, 170), (194, 177), (203, 172)])
        self._cracks(s, [(330, 182), (338, 178), (344, 185), (352, 180)])
        self._cracks(s, [(228, 62), (231, 72), (227, 82), (232, 92)])

        # fallen bricks by the barn
        for i in range(8):
            pygame.draw.rect(s, C_BRICK, R(200 + (i * 7) % 32, 124 + (i * 5) % 14, 5, 3))

        # tilted pole with a sparking wire
        a = self._pole(s, 340, 118, tilt=5)
        b = self._pole(s, 520, 120)
        mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2 + 8)
        pygame.draw.lines(s, C_WIRE, False, [a, mid, b], 1)
        end = (a[0] + 9, a[1] + 15)
        pygame.draw.line(s, C_WIRE, a, end, 1)
        if int(t * 10) % 3 == 0:
            pygame.draw.rect(s, (255, 230, 90), (end[0], end[1], 2, 2))

        # hay bales
        for hx, hy in ((500, 166), (514, 166), (507, 160)):
            pygame.draw.circle(s, (190, 160, 90), P(hx, hy), 5)

        # dust falling from the school roof while the shaking continues
        if self.current_objective_idx == 0:
            for i in range(8):
                x = 70 + (i * 13) % 95
                y = 66 + (t * 30 + i * 17) % 56
                pygame.draw.rect(s, (200, 190, 170), R(int(x), int(y), 2, 2))

        # guide arrows toward the field
        if self.current_objective_idx == 2:
            self._arrows(s, 320, 178, 4, 14)