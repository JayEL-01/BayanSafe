"""Prologue - Level 3: The Sanctuary (Severe Flooding, San Isidro). Interactive version.

Disaster: Severe Flooding / PAGASA Red Rainfall Warning / Storm Surge.

What the player does:
  0. Grab the MED PACK at the start, then reach the Evacuation Center while
     avoiding the DEEP WATER (countdown; stepping into deep water is a mistake).
  1. Report to Captain Reyes, then log the headcount at the REGISTRY.
  2. Deliver the med pack to Nurse Joy, then choose safe drinking water
     (decision). Ends the level.

Visual polish: world-space pixel water (see SevereFloodingHazard), plus
code-drawn scenery: flood marks, tents, sandbags, lamp posts, power lines,
trees, a stranded car, a rescue boat, drifting debris, storm tint + lightning.

Needs the updated base_level.py (show_hint, add_interactable, ask, countdown,
watch_zone) and its draw_under() hazard pass.
"""

import math
import pygame
from src.story.base_level import BaseLevel, TimingMeter
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import COLOR_GROUND_SAN_ISIDRO
from src.ui import theme


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (60, 240)
SAFE_TRIGGER = "evac_center"

PACK_ITEM = ("firstaid", "MED PACK", 90, 235)
DEEP_WATER_RECT = (40, 180, 260, 40)
REGISTRY_RECT = (350, 152, 20, 12)
COLOR_REGISTRY = (230, 200, 60)

WATER_TOP_Y = 170           # everything below this world-Y is flooded
RISING_SECONDS = 70.0       # time to reach the evacuation center
RISING_RETRY_SECONDS = 40.0

CAPTAIN_LINES = [
    "You made it! San Isidro Elementary is holding on the ridge.",
    "Over forty families have registered at the incident desk.",
    "Please log the headcount at the REGISTRY.",
]
NURSE_LINES = [
    "Thank you for bringing these medical packs!",
    "We are treating cuts and giving doxycycline for flood exposure.",
]
REGISTRY_LINES = [
    "REGISTRY: 43 families, 168 people accounted for.",
    "Vulnerable residents are in the protected area.",
]

HINTS = {
    1: "Safe! Talk to Captain Reyes, then use the REGISTRY.",
    2: "Bring the MED PACK to Nurse Joy at the clinic.",
}

# Scenery colors (kept muted so the water and gameplay objects stand out)
C_POLE = (70, 70, 78)
C_LAMP = (255, 220, 120)
C_WIRE = (40, 40, 46)
C_SAND = (176, 150, 100)
C_SAND_EDGE = (120, 100, 60)
C_TENT = (214, 120, 60)
C_TENT_DARK = (150, 80, 40)
C_TRUNK = (90, 64, 40)
C_LEAF = (50, 110, 60)
C_LEAF_LIGHT = (72, 140, 78)
C_FLOODMARK = (30, 60, 90)
C_GLINT = (170, 210, 235)

# Drifting debris: (start_x, y, w, h, color, bob_speed, drift_speed)
DEBRIS = [
    (200, 196, 9, 7, (150, 110, 60), 2.0, 9.0),     # wooden crate
    (120, 205, 6, 8, (60, 90, 160), 1.6, 7.0),      # blue barrel
    (260, 188, 16, 3, (120, 90, 55), 2.4, 11.0),    # plank
    (330, 212, 6, 6, (200, 200, 205), 1.9, 8.0),    # foam box
    (60, 262, 8, 6, (150, 110, 60), 1.7, 6.0),      # crate (lowland)
    (520, 290, 14, 3, (120, 90, 55), 2.2, 10.0),    # plank (lowland)
]


class PrologueLevel3SevereFlooding(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="level_3_severe_flooding",
            title="Prologue - Level 3: The Sanctuary",
            subtitle="San Isidro - Red Alert Inundation",
            disaster_type="Severe Flooding (Red Rainfall Warning)",
            lesson_source="NDRRMC Evacuation Camp Coordination & Camp Management (CCCM) Guidelines",
            lesson_text=(
                "Under Red Rainfall Warnings, evacuation is mandatory, not optional.\n"
                "Evacuation centers must maintain separate hygiene facilities,\n"
                "clean drinking water rations, and special protection areas for vulnerable groups.\n"
                "Boil all tap water or drink only sealed relief water during flood emergencies."
            ),
        )
        self._has_pack = False
        self._captain_talked = False
        self._t = 0.0                 # scenery animation clock
        self._tint = None             # cached storm overlay

        self._build_world()
        self.hazards.append(SevereFloodingHazard(
            shallow_rects=[(0, WATER_TOP_Y, MAP_W, MAP_H - WATER_TOP_Y)],
            deep_rects=[DEEP_WATER_RECT],
        ))
        self.objectives = [
            "You reach the Evacuation Center past deep water",
            "You report to Captain Reyes at the REGISTRY",
            "You deliver the MED PACK to Nurse Joy",
        ]
        self.guide_points = [
            lambda: next(
                (it.rect.center for it in self.block_map.items
                 if it.item_id == PACK_ITEM[0] and not it.collected),
                (470, 105),
            ),
            (470, 105),
            lambda: (
                self.guide_interactable("registry")() if self._captain_talked
                else self.guide_npc("Captain Reyes")()
            ),
            self.guide_npc("Nurse Joy"),
        ]
        self.show_hint("Grab the MED PACK, then avoid the DEEP WATER road!", 6.0)
        self.start_countdown(RISING_SECONDS, "WATER RISING", self._on_too_slow)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "San Isidro Evacuation Sanctuary", width=MAP_W, height=MAP_H,
            ground_color=COLOR_GROUND_SAN_ISIDRO,
        )
        bm = self.block_map

        # Submerged lowland road
        bm.add_road(30, 180, 580, 40)
        bm.add_hazard_zone("flood", *DEEP_WATER_RECT, label="DEEP WATER")

        # Evacuation center complex
        bm.add_building("shelter", "EVACUATION CENTER", 340, 50, 140, 80)
        bm.add_building("clinic", "MEDICAL CLINIC", 500, 50, 100, 70)
        bm.add_safe_zone(340, 50, 260, 110, label="SAFE SANCTUARY", trigger_id=SAFE_TRIGGER)

        # Damaged homes submerged in floodwaters
        bm.add_building("damaged_house", "FLOODED HOME A", 70, 70, 70, 60)
        bm.add_building("damaged_house", "FLOODED HOME B", 160, 70, 70, 60)

        # Medical pack to deliver (pickup near the start)
        bm.add_item(*PACK_ITEM)

        # Optional supply pickup
        self.add_pickup("radio", "HAND RADIO", (310, 210), "radio")

        # Registry (interactable) and the deep-water warning
        self.add_interactable("registry", "REGISTRY", REGISTRY_RECT, COLOR_REGISTRY, self._use_registry)
        self.watch_zone(DEEP_WATER_RECT, self._on_enter_deep_water)

        # NPCs
        self.add_npc("captain_reyes", "Captain Reyes", (380, 140), CAPTAIN_LINES, role="official")
        self.add_npc("nurse_joy", "Nurse Joy", (530, 130), NURSE_LINES, role="medical")

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
        if idx >= 1:
            self.stop_countdown()

    def _on_too_slow(self):
        self.record_score("evacuations_delayed")
        self.show_hint("The water is rising! Reach the EVACUATION CENTER!", 4.0)
        self.start_countdown(RISING_RETRY_SECONDS, "WATER RISING", self._on_too_slow)

    # ------------------------------------------------------------------
    # Step 0: pack, deep water, evacuation center
    # ------------------------------------------------------------------
    def on_item_collected(self, item_id: str):
        if item_id == PACK_ITEM[0]:
            self._has_pack = True
            self.show_hint("Got the MED PACK! Now reach the Evacuation Center.", 4.0)

    def _on_enter_deep_water(self):
        self.record_score("unsafe_actions")
        self.show_hint("DEEP WATER! Currents and sewage. Walk around it!", 4.5)

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == SAFE_TRIGGER and self.current_objective_idx == 0:
            self._next()

    # ------------------------------------------------------------------
    # Step 1: Captain Reyes and the registry
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        idx = self.current_objective_idx

        if npc.name == "Captain Reyes":
            self._captain_talked = True

        elif npc.name == "Nurse Joy":
            if idx < 2:
                self.show_hint("Nurse Joy is busy. Finish reporting first.", 3.5)
            elif idx == 2:
                if self._has_pack:
                    self._ask_about_water()
                else:
                    self.show_hint("You need the MED PACK from the start of the street.", 4.5)

    def _use_registry(self, item):
        idx = self.current_objective_idx
        if idx < 1:
            self.show_hint("Reach the Evacuation Center first.", 3.0)
        elif idx == 1:
            if not self._captain_talked:
                self.show_hint("Talk to Captain Reyes first.", 3.0)
                return
            item["done"] = True
            self.start_minigame(
                TimingMeter(
                    "LOG HEADCOUNT",
                    "",
                    steps=["Count families at the shelter", "Record vulnerable residents"],
                    speed=0.8,
                    zone=0.30,
                    max_misses=3,
                    icon="radio",
                    win_text="HEADCOUNT LOGGED!",
                    fail_text="CHECK THE LIST!",
                ),
                on_win=lambda: self._registry_done(item),
                on_fail=lambda: self._registry_failed(item),
            )
        else:
            self.show_hint("Headcount already reported.", 2.5)

    def _registry_done(self, item):
        self.start_dialogue("Incident Post", REGISTRY_LINES)
        self.record_score("hazards_reported")
        self._next()

    def _registry_failed(self, item):
        item["done"] = False
        self.show_hint("Check the headcount list. Try the REGISTRY again.", 3.0)

    # ------------------------------------------------------------------
    # Step 2: safe drinking water (decision), ends the level
    # ------------------------------------------------------------------
    def _ask_about_water(self):
        def on_safe():
            self.score_system.complete_evacuation("prologue_3")
            self.complete_level()

        self.ask(
            decision_id="flood_water_hygiene_choice",
            prompt="Water is limited. A resident offers tap water from a flooded well:",
            options=[
                {
                    "text": "Refuse it; give sealed bottles and purification tablets",
                    "safe": True,
                    "lesson": "Floods contaminate groundwater with sewage, cholera and E. coli.",
                },
                {
                    "text": "Drink it because the well water looks clear",
                    "safe": False,
                    "lesson": "Clear water can still hold lethal bacteria and chemical toxins.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Clear-looking flood water can still be deadly.",
        )

    # ------------------------------------------------------------------
    # Visual polish
    # ------------------------------------------------------------------
    def update(self, dt: float):
        super().update(dt)
        self._t += dt

    def _r(self, x, y, w, h):
        """World rect -> screen rect through the camera."""
        return self.camera.apply(pygame.Rect(x, y, w, h))

    def _draw_interactables(self, surface):
        # Scenery goes underneath the registry; water is drawn right after
        # this by the base draw(), so low objects look partly submerged.
        self._draw_scenery(surface)
        super()._draw_interactables(surface)

    def _draw_scenery(self, s):
        t = self._t
        R = self._r

        # --- flood marks on the damaged houses ---------------------------
        for hx in (70, 160):
            r = R(hx, 108, 70, 22)
            band = pygame.Surface(r.size, pygame.SRCALPHA)
            band.fill((*C_FLOODMARK, 110))
            s.blit(band, r.topleft)
            for x in range(r.left, r.right, 4):
                s.set_at((x, r.top), C_GLINT)

        # --- trees (lowland) --------------------------------------------
        for tx, ty in ((20, 262), (300, 288), (565, 272), (610, 300)):
            sway = int(math.sin(t * 1.5 + tx) * 1)
            trunk = R(tx, ty, 4, 22)
            pygame.draw.rect(s, C_TRUNK, trunk)
            c = R(tx - 8 + sway, ty - 14, 20, 20).center
            pygame.draw.circle(s, C_LEAF, c, 10)
            pygame.draw.circle(s, C_LEAF_LIGHT, (c[0] - 3, c[1] - 3), 5)

        # --- lamp posts + power line ------------------------------------
        poles = (110, 260, 410, 560)
        tops = []
        for px in poles:
            pole = R(px, 146, 2, 36)
            pygame.draw.rect(s, C_POLE, pole)
            pygame.draw.rect(s, C_POLE, R(px - 4, 148, 10, 2))
            tops.append((pole.centerx, pole.top + 2))
            # lamp that flickers in the storm
            on = (int(t * 7 + px) % 11) != 0
            lamp = R(px - 3, 150, 8, 3)
            pygame.draw.rect(s, C_LAMP if on else (120, 110, 70), lamp)
            if on:
                glow = pygame.Surface((14, 10), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (*C_LAMP, 45), glow.get_rect())
                s.blit(glow, (lamp.centerx - 7, lamp.bottom - 2))
        for a, b in zip(tops, tops[1:]):
            mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2 + 5)
            pygame.draw.lines(s, C_WIRE, False, [a, mid, b], 1)

        # --- evacuation signage ----------------------------------------
        sign = R(300, 158, 38, 11)
        pygame.draw.rect(s, (40, 130, 80), sign)
        pygame.draw.rect(s, (230, 240, 230), sign, 1)
        pygame.draw.rect(s, C_POLE, R(318, 169, 2, 8))
        # Keep the sign text on canvas when the sign is at the screen edge.
        evac_label = "EVAC >"
        evac_w = theme.get_font("tiny").size(evac_label)[0]
        evac_x = max(evac_w // 2 + 2,
                     min(sign.centerx, s.get_width() - evac_w // 2 - 2))
        theme.draw_text(s, evac_label, (evac_x, sign.centery - 3),
                        size="tiny", color=(240, 250, 240), shadow=False, anchor="center")

        # --- shelter banner + clinic cross -------------------------------
        pygame.draw.rect(s, (60, 140, 90), R(360, 56, 100, 6))
        for x in range(364, 456, 8):
            pygame.draw.rect(s, (230, 240, 230), R(x, 58, 4, 2))
        cross = R(545, 56, 14, 14)
        pygame.draw.rect(s, (245, 245, 245), cross)
        pygame.draw.rect(s, (200, 40, 40), (cross.x + 5, cross.y + 2, 4, 10))
        pygame.draw.rect(s, (200, 40, 40), (cross.x + 2, cross.y + 5, 10, 4))

        # --- relief tents ------------------------------------------------
        for tx, ty in ((418, 132), (440, 138)):
            r = R(tx, ty, 20, 14)
            pts = [(r.left, r.bottom), (r.centerx, r.top), (r.right, r.bottom)]
            pygame.draw.polygon(s, C_TENT, pts)
            pygame.draw.polygon(s, C_TENT_DARK, pts, 1)
            door = [(r.centerx - 3, r.bottom), (r.centerx, r.top + 6), (r.centerx + 3, r.bottom)]
            pygame.draw.polygon(s, C_TENT_DARK, door)

        # --- relief crates -----------------------------------------------
        for cx, cy in ((476, 136), (484, 140), (480, 128)):
            pygame.draw.rect(s, (190, 150, 90), R(cx, cy, 7, 6))
            pygame.draw.rect(s, (120, 90, 50), R(cx, cy, 7, 6), 1)

        # --- sandbag walls (look only, no collision) ---------------------
        for sx, sy, n in ((326, 150, 3), (582, 150, 4), (500, 122, 6)):
            for i in range(n):
                pygame.draw.rect(s, C_SAND, R(sx + i * 6, sy, 6, 4))
                pygame.draw.rect(s, C_SAND_EDGE, R(sx + i * 6, sy, 6, 4), 1)
            for i in range(n - 1):
                pygame.draw.rect(s, C_SAND, R(sx + 3 + i * 6, sy - 4, 6, 4))
                pygame.draw.rect(s, C_SAND_EDGE, R(sx + 3 + i * 6, sy - 4, 6, 4), 1)

        # --- stranded car on the road ------------------------------------
        pygame.draw.rect(s, (170, 60, 60), R(440, 194, 36, 12))
        pygame.draw.rect(s, (150, 50, 50), R(448, 188, 20, 8))
        pygame.draw.rect(s, (150, 190, 210), R(451, 190, 6, 5))
        pygame.draw.rect(s, (150, 190, 210), R(459, 190, 6, 5))

        # --- rescue boat (bobs) ------------------------------------------
        bob = int(math.sin(t * 1.8) * 1)
        b = R(200, 262 + bob, 44, 10)
        hull = [(b.left, b.top), (b.right, b.top), (b.right - 7, b.bottom), (b.left + 7, b.bottom)]
        pygame.draw.polygon(s, (225, 225, 230), hull)
        pygame.draw.line(s, (230, 120, 40), (b.left + 2, b.top + 3), (b.right - 2, b.top + 3), 1)
        pygame.draw.polygon(s, (90, 90, 100), hull, 1)

        # --- drifting debris (flows left with the current) ---------------
        for bx, by, w, h, col, bob_sp, drift in DEBRIS:
            x = (bx - t * drift - 30) % 560 + 30
            y = by + math.sin(t * bob_sp + bx) * 1.5
            r = R(int(x), int(y), w, h)
            pygame.draw.rect(s, col, r)
            pygame.draw.rect(s, (30, 30, 36), r, 1)

        # --- wading ripples around the player's feet ---------------------
        p = self.player.rect
        if p.bottom >= WATER_TOP_Y:
            phase = (t * 1.6) % 1.0
            ring = R(p.centerx - 6, p.bottom - 3, 12, 5).inflate(int(phase * 10), int(phase * 4))
            pygame.draw.ellipse(s, C_GLINT, ring, 1)

    def _draw_hud(self, surface):
        """Storm atmosphere under the HUD: cool tint, vignette, lightning."""
        w, h = surface.get_size()
        if self._tint is None or self._tint.get_size() != (w, h):
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill((20, 35, 60, 55))
            for i in range(6):  # stepped vignette (pixel style, no gradients)
                pygame.draw.rect(tint, (0, 0, 0, 14), (i * 3, i * 3, w - i * 6, h - i * 6), 3)
            self._tint = tint
        surface.blit(self._tint, (0, 0))

        # Lightning: a quick double flash every ~11 seconds
        phase = self._t % 11.0
        if phase < 0.10 or 0.22 < phase < 0.30:
            flash = pygame.Surface((w, h), pygame.SRCALPHA)
            flash.fill((235, 240, 255, 70))
            surface.blit(flash, (0, 0))

        super()._draw_hud(surface)