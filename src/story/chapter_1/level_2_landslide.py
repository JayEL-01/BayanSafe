"""Chapter 1 - Level 2: Landslide Threat (North West Plateau). Interactive version.

Location: Highland Ridgeline & Terraces.
Disaster: Rain-Induced Landslide & Slope Collapse.

What the player does:
  0. Inspect 3 warning signs (2 TENSION CRACKS and the LEANING POLE).
  1. Find Mang Lito at his barn, then choose the safe route (decision).
  2. Reach the BEDROCK RIDGE before the slope slips. Avoid the ROCKFALL DEBRIS.
"""

import math
import pygame
from src.story.base_level import BaseLevel, Mash
from src.maps.block_map import BlockMap
from src.hazards.landslide import LandslideHazard
from src.config.palette import COLOR_GROUND_PLATEAU


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (60, 175)
SAFE_TRIGGER = "bedrock_safe"

DEBRIS_RECT = (220, 150, 120, 50)

# (key, label, rect, color)
INSPECTS = [
    ("crack_a", "TENSION CRACK", (92, 168, 22, 9), (60, 40, 30)),
    ("crack_b", "TENSION CRACK", (150, 176, 22, 9), (60, 40, 30)),
    ("pole", "LEANING POLE", (196, 128, 10, 26), (110, 110, 120)),
]
INSPECT_LINES = {
    "crack_a": ["A fresh crack runs across the trail, wider than a hand.",
                "Tension cracks mean the slope is starting to separate."],
    "crack_b": ["Another crack, and the ground below it has sunk slightly.",
                "Water is seeping out of the crack. Very bad sign."],
    "pole": ["This utility pole is leaning downhill.",
             "Leaning poles and trees mean the soil is creeping."],
}

SLOPE_SECONDS = 90.0
SLOPE_RETRY_SECONDS = 45.0

LITO_LINES = [
    "The soil was groaning before sunrise! Half my banana terrace slid down into the gorge!",
    "The main dirt road is buried under three meters of mud and heavy boulders.",
    "Is the upper bedrock trail still solid? Let's take that path to safety!",
]

HINTS = {
    1: "Warning signs logged. Find Mang Lito at his barn.",
    2: "Take the upper trail to the BEDROCK RIDGE. Hurry!",
}

C_MUD = (112, 80, 52)
C_MUD_LIGHT = (150, 115, 80)
C_ROCK = (120, 118, 122)
C_ROCK_LIGHT = (160, 158, 162)
C_ROCK_DARK = (70, 68, 74)
C_TRUNK = (90, 64, 40)
C_LEAF = (50, 110, 60)
C_LEAF_LIGHT = (72, 140, 78)
C_POLE = (70, 70, 78)
C_WIRE = (40, 40, 46)
C_FENCE = (120, 90, 55)
C_CRACK = (34, 26, 22)


class Chapter1Level2Landslide(BaseLevel):
    _t = 0.0
    _tint = None

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_2_landslide",
            title="Chapter 1 - Level 2: The Sliding Ridge",
            subtitle="North West Plateau - Mountain Slope Failure",
            disaster_type="Rain-Induced Landslide Hazard",
            lesson_source="DENR-MGB Geohazard Assessment & Slope Stability Guidelines",
            lesson_text=(
                "Key warning signs of an impending landslide include:\n"
                "new tension cracks in the ground, leaning utility poles or trees,\n"
                "fences pulling apart, and sudden muddying of clear spring waters.\n"
                "Never cross a freshly collapsed mudslide; secondary slides follow rapidly."
            ),
        )
        self._inspected = set()
        self._build_world()
        self.hazards.append(LandslideHazard())
        self.objectives = [
            "You inspect three warning signs along the trail",
            "You find Mang Lito at his terraced field",
            "You reach the bedrock ridge above the debris",
        ]
        self.guide_points = [
            lambda: next((i["rect"].center for i in self.interactables
                          if not i["done"]), INSPECTS[0][2][:2]),
            self.guide_npc("Mang Lito"),
            (520, 100),
        ]
        self.show_hint("Look for cracks and leaning poles. Press SPACE to inspect.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Plateau Mountain Slope", width=MAP_W, height=MAP_H,
                                  ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # Main ridge trail and the alternate high bedrock trail
        bm.add_path(40, 160, 560, 32)
        bm.add_path(180, 70, 240, 26)

        # Blocked lower trail with landslide debris
        bm.add_hazard_zone("landslide", *DEBRIS_RECT, label="ROCKFALL DEBRIS")

        # Farm buildings and bedrock safe zone
        bm.add_building("house", "MANG LITO'S BARN", 80, 80, 75, 55)
        bm.add_building("damaged_house", "COLLAPSED SHED", 360, 220, 80, 60)
        bm.add_safe_zone(460, 60, 120, 80, label="BEDROCK RIDGE", trigger_id=SAFE_TRIGGER)

        # Inspectable warning signs (translucent so the scenery shows through)
        for key, label, rect, color in INSPECTS:
            self.add_interactable(key, label, rect, color, self._inspect, alpha=70)
        self.add_pickup("fieldbook", "SLOPE FIELD BOOK", (70, 215), "book")
        self.watch_zone(DEBRIS_RECT, self._on_enter_debris)

        # NPC
        self.add_npc("mang_lito", "Mang Lito", (110, 140), LITO_LINES, role="resident")

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
            self.start_countdown(SLOPE_SECONDS, "SLOPE CREEPING", self._on_slope_slip)
        else:
            self.stop_countdown()

    def _on_slope_slip(self):
        self.record_score("evacuations_delayed")
        self.show_hint("The slope is slipping! Reach the BEDROCK RIDGE!", 4.0)
        self.start_countdown(SLOPE_RETRY_SECONDS, "SLOPE CREEPING", self._on_slope_slip)

    def _on_enter_debris(self):
        self.record_score("unsafe_actions")
        self.show_hint("ROCKFALL DEBRIS! Active mud can collapse. Take the upper trail!", 4.5)

    # ------------------------------------------------------------------
    # Step 0: inspect warning signs
    # ------------------------------------------------------------------
    def _inspect(self, item):
        if self.current_objective_idx != 0 or item["done"]:
            self.show_hint("Already inspected.", 2.5)
            return
        item["done"] = True
        self._inspected.add(item["key"])
        self.start_dialogue("Slope Check", INSPECT_LINES[item["key"]])
        self.record_score("hazards_reported")
        if len(self._inspected) >= len(INSPECTS):
            self.start_minigame(
                Mash(
                    "LOG THE SIGNS", "Mash SPACE to mark the slope hazards!",
                    target=8, decay=1.8, time_limit=6.0,
                    icon="book", win_text="SIGNS LOGGED!",
                ),
                on_win=self._next,
                on_fail=lambda: self.show_hint("Log the signs before moving on.", 3.0),
            )
        else:
            self.show_hint(f"Warning sign logged ({len(self._inspected)}/{len(INSPECTS)}).", 3.5)

    # ------------------------------------------------------------------
    # Step 1: Mang Lito (decision)
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Mang Lito":
            return
        idx = self.current_objective_idx
        if idx < 1:
            self.show_hint(f"Inspect the slope warning signs first ({len(self._inspected)}/{len(INSPECTS)}).", 4.0)
        elif idx == 1:
            self._ask_about_route()

    def _ask_about_route(self):
        def on_safe():
            self.score_system.assist_resident("Mang Lito")
            self._next()

        self.ask(
            decision_id="landslide_route_choice",
            prompt="The lower path is covered in sliding mud. Safest route?",
            options=[
                {
                    "text": "Turn back and climb the upper bedrock ridge path",
                    "safe": True,
                    "lesson": "Bedrock resists rainfall saturation far better than steep clay slopes.",
                },
                {
                    "text": "Climb over the wet mudflow while rocks still tumble",
                    "safe": False,
                    "lesson": "Active mudflows have strong suction and can trigger fatal secondary collapses.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Never cross fresh mudflow. Find the bedrock route.",
        )

    # ------------------------------------------------------------------
    # Step 2: bedrock ridge, ends the level
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == SAFE_TRIGGER and self.current_objective_idx == 2:
            self.score_system.complete_evacuation("ch1_2")
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
        """Rain, lightning, tint and vignette, drawn under the HUD."""
        w, h = surface.get_size()
        if self._tint is None or self._tint.get_size() != (w, h):
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill((40, 50, 45, 50))
            for i in range(6):
                pygame.draw.rect(tint, (0, 0, 0, 14), (i * 3, i * 3, w - i * 6, h - i * 6), 3)
            self._tint = tint
        surface.blit(self._tint, (0, 0))

        t = self._t
        for i in range(34):
            x = int((i * 37 + t * 30) % w)
            y = int((i * 53 + t * 140) % h)
            pygame.draw.line(surface, (170, 200, 225), (x, y), (x - 1, y + 2))

        phase = t % 14.0
        if phase < 0.10 or 0.22 < phase < 0.30:
            flash = pygame.Surface((w, h), pygame.SRCALPHA)
            flash.fill((235, 240, 255, 70))
            surface.blit(flash, (0, 0))

        super()._draw_hud(surface)

    def _draw_interactables(self, surface):
        self._draw_scenery(surface)
        super()._draw_interactables(surface)

    def _tree(self, s, x, y):
        px, py = self._p(x, y)
        cx = px + 2 + int(math.sin(self._t * 1.4 + x) * 1)
        pygame.draw.rect(s, C_TRUNK, (px, py, 4, 18))
        pygame.draw.circle(s, C_LEAF, (cx, py - 6), 10)
        pygame.draw.circle(s, C_LEAF_LIGHT, (cx - 3, py - 9), 5)

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

    def _pole(self, s, x, y, h=30, tilt=0):
        bx, by = self._p(x, y + h)
        tx, ty = bx + tilt, by - h
        pygame.draw.line(s, C_POLE, (bx, by), (tx, ty), 2)
        pygame.draw.line(s, C_POLE, (tx - 5, ty + 3), (tx + 5, ty + 3), 1)
        return (tx, ty + 3)

    def _rocks(self, s, rect, n, seed=1, light=False):
        x, y, w, h = rect
        for i in range(n):
            hh = ((i + seed) * 2654435761) & 0xFFFFFF
            rx = x + hh % max(1, w - 8)
            ry = y + (hh >> 5) % max(1, h - 6)
            size = 4 + (hh >> 9) % 5
            r = self._r(rx, ry, size, size - 1)
            pygame.draw.rect(s, C_ROCK_LIGHT if light else C_ROCK, r)
            pygame.draw.line(s, C_ROCK_LIGHT, r.topleft, (r.right - 1, r.top))
            pygame.draw.line(s, C_ROCK_DARK, (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1))

    def _mud(self, s, x, y, w, h):
        """Flat pixel mudflow with slowly crawling streaks."""
        sr = self._r(x, y, w, h)
        vis = sr.clip(s.get_rect())
        if vis.w <= 0 or vis.h <= 0:
            return
        body = pygame.Surface(vis.size, pygame.SRCALPHA)
        body.fill((*C_MUD, 170))
        s.blit(body, vis.topleft)
        for row, ry in enumerate(range(sr.top + 5, sr.bottom, 8)):
            if not (vis.top <= ry < vis.bottom):
                continue
            for k in range(0, w, 28):
                lx = sr.left + (k + row * 11 - int(self._t * 4)) % max(1, w)
                if vis.left <= lx < vis.right - 6:
                    pygame.draw.line(s, C_MUD_LIGHT, (lx, ry), (lx + 5, ry))

    def _arrows(self, s, x, y, n, step=16):
        active = int(self._t * 5) % n
        for i in range(n):
            px, py = self._p(x + i * step, y)
            col = (255, 230, 120) if i == active else (200, 170, 60)
            pygame.draw.lines(s, col, False, [(px, py - 4), (px + 4, py), (px, py + 4)], 2)

    def _draw_scenery(self, s):
        t = self._t
        R, P = self._r, self._p

        # terraced banana field (lower left)
        for i in range(4):
            r = R(40, 230 + i * 20, 290, 18)
            band = pygame.Surface(r.size, pygame.SRCALPHA)
            band.fill((110, 90, 50, 70) if i % 2 == 0 else (90, 110, 60, 60))
            s.blit(band, r.topleft)
            pygame.draw.line(s, (70, 68, 74), r.topleft, r.topright)
        for row in range(4):
            for bx in range(60, 320, 36):
                px, py = P(bx + (row % 2) * 18, 226 + row * 20)
                pygame.draw.line(s, (80, 110, 60), (px, py + 8), (px, py), 1)
                for dx, dy in ((-6, 2), (-3, -1), (3, -1), (6, 2)):
                    pygame.draw.line(s, (60, 130, 70), (px, py), (px + dx, py + dy), 1)

        # mud scar where half the terrace slid away
        scar = [(200, 230), (250, 228), (300, 270), (270, 312), (230, 300), (215, 260)]
        pygame.draw.polygon(s, C_MUD, [P(x, y) for x, y in scar])
        pygame.draw.polygon(s, (70, 50, 34), [P(x, y) for x, y in scar], 1)

        # mudflow over the lower trail, plus tumbling pebbles
        self._mud(s, DEBRIS_RECT[0] + 2, DEBRIS_RECT[1] + 2, DEBRIS_RECT[2] - 4, DEBRIS_RECT[3] - 4)
        self._rocks(s, DEBRIS_RECT, 9, seed=2)
        for i in range(4):
            ph = (t * 0.8 + i * 0.37) % 1.0
            pygame.draw.rect(s, (150, 130, 110), R(int(240 + i * 26), int(128 + ph * 40), 3, 3))

        # fence pulling apart, trees
        self._fence(s, 20, 140, 6, broken=(2, 3))
        for x, y in ((24, 100), (610, 190), (580, 250), (330, 300)):
            self._tree(s, x, y)

        # leaning pole with a sagging wire
        a = self._pole(s, 200, 128, tilt=-7)
        b = self._pole(s, 330, 126)
        mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2 + 9)
        pygame.draw.lines(s, C_WIRE, False, [a, mid, b], 1)

        # cracks at the inspectable spots
        pygame.draw.lines(s, C_CRACK, False, [P(92, 172), P(99, 169), P(103, 175), P(110, 171)], 1)
        pygame.draw.lines(s, C_CRACK, False, [P(150, 180), P(157, 177), P(160, 183), P(170, 179)], 1)

        # bedrock ridge: stone and a flag
        self._rocks(s, (466, 64, 110, 72), 18, seed=3, light=True)
        fx, fy = P(572, 92)
        pygame.draw.line(s, C_POLE, (fx, fy), (fx, fy - 22), 1)
        wv = int(math.sin(t * 4) * 1)
        pygame.draw.polygon(s, (60, 160, 90), [(fx, fy - 22), (fx + 10 + wv, fy - 20),
                                               (fx + 10 - wv, fy - 17), (fx, fy - 15)])

        # guide arrows along the upper trail
        if self.current_objective_idx == 2:
            self._arrows(s, 300, 83, 6, 16)