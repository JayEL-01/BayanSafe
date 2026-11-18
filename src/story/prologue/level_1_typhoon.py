"""Prologue - Level 1: The Gale Rising (Typhoon, San Isidro). Interactive version.

Disaster: Tropical Cyclone Wind Signal (PAGASA TCWS #2).

What the player does:
  0. Find Lola Teresa's medicine pouch (pick it up) and bring it to her.
  1. Secure the barangay: fix the loose ZINC roof, trim the BRANCH, clear the
     CANAL debris (3 interactable blocks, any order).
  2. Deal with the DOWNED WIRE: report it and take the safe path (decision).
  3. Reach the HIGH GROUND before the winds intensify (countdown).

Needs the updated base_level.py (show_hint, add_interactable, ask, countdown).
"""

import pygame
from src.story.base_level import BaseLevel, TimingMeter
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_SAN_ISIDRO


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (60, 175)
SAFE_TRIGGER = "safe_reach"

MEDS_ITEM = ("firstaid", "MEDS", 100, 205)  # Lola's medicine pouch (pickup)

ZINC_RECT = (215, 134, 16, 12)
BRANCH_RECT = (255, 140, 14, 12)
CANAL_RECT = (345, 198, 20, 12)
WIRE_RECT = (425, 166, 22, 10)

COLOR_ZINC = (150, 150, 165)
COLOR_BRANCH = (60, 110, 50)
COLOR_CANAL = (110, 90, 70)
COLOR_WIRE = (230, 60, 60)

WIND_SECONDS = 75.0        # time to reach high ground once everything is ready
WIND_RETRY_SECONDS = 45.0  # extra time if the first countdown runs out
TASKS_NEEDED = 3

LOLA_LINES = [
    "The winds are rattling my shutters, apo!",
    "My medicine pouch fell near the gate. Please find it!",
]
LOLA_THANKS = [
    "Salamat, anak! My maintenance medicines are safe.",
    "Thank you for helping an old grandmother prepare.",
]
BEN_LINES = [
    "Loose zinc sheets are flying across the street!",
    "Keep the canals clear or water will back up fast.",
    "Stay away from dangling power cables. Go to high ground!",
]

HINTS = {
    1: "Secure the town: fix the ZINC, trim the BRANCH, clear the CANAL.",
    2: "A DOWNED WIRE blocks the road. Walk up to it carefully.",
    3: "Winds are rising! Run to the HIGH GROUND at the top right!",
}


class PrologueLevel1Typhoon(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="level_1_typhoon",
            title="Prologue - Level 1: The Gale Rising",
            subtitle="San Isidro - Tropical Cyclone Advisory",
            disaster_type="Typhoon (PAGASA TCWS #2)",
            lesson_source="DOST-PAGASA Tropical Cyclone Wind Signal (TCWS) System & NDRRMC Guidelines",
            lesson_text=(
                "Under TCWS #2 (winds 62-88 km/h expected in 24 hours):\n"
                "Secure tin roofs, trim hanging tree branches, and clear drainage canals.\n"
                "Prioritize the pre-emptive evacuation of vulnerable community members\n"
                "(elderly, persons with disabilities, infants, and pregnant mothers)."
            ),
        )
        self._has_meds = False
        self._lola_helped = False
        self._tasks = set()
        self._wire_reported = False

        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=2))
        self.objectives = [
            "You bring Lola Teresa her medicine at her gate",
            "You secure the zinc, branch, and canal in town",
            "You report the downed wire on the road",
            "You reach High Ground above the coast",
        ]
        self.guide_points = [
            lambda: next(
                (it.rect.center for it in self.block_map.items
                 if it.item_id == MEDS_ITEM[0] and not it.collected),
                MEDS_ITEM[2:4],
            ),
            lambda: next(
                (i["rect"].center for i in self.interactables
                 if i["key"] in ("zinc", "branch", "canal") and not i["done"]),
                ZINC_RECT[:2],
            ),
            self.guide_interactable("wire"),
            (530, 90),
        ]
        self.show_hint("Move with ARROW KEYS / WASD. Find Lola Teresa's MEDS.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "San Isidro Coastline", width=MAP_W, height=MAP_H,
            ground_color=COLOR_GROUND_SAN_ISIDRO,
        )
        bm = self.block_map

        # Coastal road & cross streets
        bm.add_road(40, 160, 560, 30)
        bm.add_road(300, 30, 30, 270)
        # Connecting road ramp leading up to High Ground
        bm.add_road(480, 130, 60, 30)

        # Buildings
        bm.add_building("house", "LOLA TERESA", 90, 80, 80, 55)
        bm.add_building("house", "HOUSE B", 200, 80, 70, 50)
        bm.add_building("damaged_house", "DAMAGED SHED", 360, 80, 60, 50)

        # South sea waters
        bm.add_water(0, 320, 640, 40)

        # Safe assembly zone (unobstructed, walkable high ground)
        bm.add_safe_zone(460, 50, 140, 80, label="HIGH GROUND", trigger_id=SAFE_TRIGGER)

        # Lola's medicine pouch (pickup)
        bm.add_item(*MEDS_ITEM)

        # Optional supply pickup
        self.add_pickup("torch", "TORCH", (180, 205), "flashlight")

        # Interactable blocks
        self.add_interactable("zinc", "ZINC", ZINC_RECT, COLOR_ZINC, self._use_zinc)
        self.add_interactable("branch", "BRANCH", BRANCH_RECT, COLOR_BRANCH, self._use_branch)
        self.add_interactable("canal", "CANAL", CANAL_RECT, COLOR_CANAL, self._use_canal)
        self.add_interactable("wire", "DOWNED WIRE", WIRE_RECT, COLOR_WIRE, self._use_wire)

        # NPCs
        self.add_npc("lola_teresa", "Lola Teresa", (130, 140), LOLA_LINES, role="vulnerable")
        self.add_npc("kuya_ben", "Kuya Ben", (320, 165), BEN_LINES, role="resident")

        self.player.pos = pygame.Vector2(*PLAYER_SPAWN)
        self.player.rect.topleft = PLAYER_SPAWN

    # ------------------------------------------------------------------
    # Objective flow (objectives 0-2 advance as soon as they are met)
    # ------------------------------------------------------------------
    def _check_objectives(self):
        while True:
            i = self.current_objective_idx
            if i == 0 and self._lola_helped:
                pass
            elif i == 1 and len(self._tasks) >= TASKS_NEEDED:
                pass
            elif i == 2 and self._wire_reported:
                pass
            else:
                break
            self.complete_objective()
            self._on_objective_changed()

    def _on_objective_changed(self):
        idx = self.current_objective_idx
        if idx in HINTS:
            self.show_hint(HINTS[idx], 5.0)
        if idx == 3:
            self.start_countdown(WIND_SECONDS, "WINDS RISING", self._on_too_slow)

    def _on_too_slow(self):
        self.record_score("evacuations_delayed")
        self.show_hint("Too slow! Evacuate EARLY. Hurry to HIGH GROUND!", 4.0)
        self.start_countdown(WIND_RETRY_SECONDS, "WINDS RISING", self._on_too_slow)

    # ------------------------------------------------------------------
    # Step 0: Lola's medicine
    # ------------------------------------------------------------------
    def on_item_collected(self, item_id: str):
        if item_id == MEDS_ITEM[0]:
            self._has_meds = True
            self.show_hint("Got Lola's medicine pouch! Bring it to her.", 4.0)

    def on_npc_interacted(self, npc):
        if npc.name == "Lola Teresa" and not self._lola_helped:
            if self._has_meds:
                self._lola_helped = True
                self.score_system.assist_resident("Lola Teresa")
                self.start_dialogue(npc.name, LOLA_THANKS)
                self._check_objectives()
            else:
                self.show_hint("Find Lola's MEDS pouch near her gate first.", 4.0)

    # ------------------------------------------------------------------
    # Step 1: secure the town
    # ------------------------------------------------------------------
    def _do_task(self, item, name: str, message: str):
        if item["done"]:
            self.show_hint(f"The {name} is already done.", 2.5)
            return
        item["done"] = True
        self._tasks.add(name)
        self.show_hint(f"{message} ({len(self._tasks)}/{TASKS_NEEDED})", 3.5)
        self._check_objectives()

    def _use_zinc(self, item):
        self._do_task(item, "zinc", "Loose zinc roof secured!")

    def _use_branch(self, item):
        self._do_task(item, "branch", "Hanging branch trimmed!")

    def _use_canal(self, item):
        self._do_task(item, "canal", "Canal debris cleared!")

    # ------------------------------------------------------------------
    # Step 2: the downed wire (safe / unsafe decision; unsafe asks again)
    # ------------------------------------------------------------------
    def _use_wire(self, item):
        if item["done"]:
            self.show_hint("You already reported this wire.", 2.5)
            return
        self.start_minigame(
            TimingMeter(
                "MARK DOWNED WIRE",
                "",
                steps=["Mark a 10m exclusion zone", "Choose the elevated detour"],
                speed=0.8,
                zone=0.30,
                max_misses=3,
                icon="flashlight",
                win_text="WIRE MARKED!",
                fail_text="MARK IT AGAIN!",
            ),
            on_win=lambda: self._ask_about_wire(item),
            on_fail=lambda: self.show_hint("Mark the hazard carefully. Try again.", 3.0),
        )

    def _ask_about_wire(self, item):
        def on_safe():
            item["done"] = True
            self._wire_reported = True
            self.record_score("hazards_reported")
            self.show_hint("Reported! Take the clear elevated path.", 3.5)
            self._check_objectives()

        self.ask(
            decision_id="typhoon_debris_choice",
            prompt="A downed power line blocks the path ahead:",
            options=[
                {
                    "text": "Report it, stay 10m away, take the elevated path",
                    "safe": True,
                    "lesson": "Never touch fallen power lines or step in puddles near downed wires.",
                },
                {
                    "text": "Push the dangling wire aside with bare hands",
                    "safe": False,
                    "lesson": "High electrocution risk; downed wires can stay live and energize the ground.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Electrocution risk! Think again.",
        )

    # ------------------------------------------------------------------
    # Step 3: high ground
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id != SAFE_TRIGGER:
            return
        if self.current_objective_idx >= 3:
            self.stop_countdown()
            self.score_system.complete_evacuation("prologue_1")
            self.complete_level()
        elif self.hint_timer <= 0:
            self.show_hint("Finish your tasks first, then come back here.", 3.0)