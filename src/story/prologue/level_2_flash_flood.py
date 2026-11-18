"""Prologue - Level 2: Torrential Surge (Flash Flood, San Isidro). Interactive version.

Disaster: Flash Flood / PAGASA Orange Rainfall Warning.

What the player does:
  0. Read the PAGASA rainfall warning board.
  1. Pick up Mila's baby bag and bring it to her.
  2. Ask Berto about the bridge (decision), then CROSS before the bridge closes
     (countdown). Stepping into the floodwater is a mistake.
  3. Reach the HIGH GROUND at the River Safe Haven.

Change from the old version: Berto now stands on the WEST bank, so the bridge
decision happens BEFORE crossing (the old Berto was on the east bank, so the
player had already crossed when asked).

Needs the updated base_level.py (show_hint, add_interactable, ask, countdown,
watch_zone).
"""

import pygame
from src.story.base_level import BaseLevel, TimingMeter
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import FlashFloodHazard
from src.config.palette import COLOR_GROUND_SAN_ISIDRO, COLOR_UI_SAFE


# ---------------------------------------------------------------------------
# Easy-to-edit settings
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (50, 175)
SAFE_TRIGGER = "flood_safe"

BOARD_RECT = (55, 132, 18, 14)
BAG_ITEM = ("firstaid", "BABY BAG", 160, 205)
CHAIRS_RECT = (265, 275, 22, 12)       # trap: patio furniture inside the flood zone
EAST_BANK_RECT = (385, 150, 55, 50)    # reaching this = crossed the bridge
FLOOD_ZONE_RECT = (250, 240, 190, 100)

COLOR_BOARD = (230, 170, 50)
COLOR_CHAIRS = (160, 110, 160)

CROSS_SECONDS = 40.0
CROSS_RETRY_SECONDS = 25.0

BOARD_LINES = [
    "PAGASA ORANGE Rainfall Warning: flooding is threatening.",
    "Rivers can rise in minutes. Move early, not late.",
    "Never wade through moving floodwater.",
]
MILA_LINES = [
    "The water rose from the creek in under ten minutes!",
    "My baby's bag is on the road. Please bring it!",
]
MILA_THANKS = [
    "Thank you! My baby is wrapped in waterproof blankets.",
    "Please lead us across the bridge before it's cut off!",
]
BERTO_LINES = [
    "The upstream torrent is carrying uprooted logs!",
    "Do not step into the dark muddy water.",
]


class PrologueLevel2FlashFlood(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="level_2_flash_flood",
            title="Prologue - Level 2: Torrential Surge",
            subtitle="San Isidro - River Breach & Flash Flood",
            disaster_type="Flash Flood (Orange Warning)",
            lesson_source="PAGASA Color-Coded Heavy Rainfall Advisory & DOH Leptospirosis Advisory",
            lesson_text=(
                "Moving floodwaters just 15 centimeters (6 inches) deep can sweep adults away.\n"
                "Never attempt to wade or cross swollen rivers or submerged bridges.\n"
                "Avoid contact with muddy floodwaters to prevent severe Leptospirosis infection.\n"
                "Always seek elevated high ground immediately upon flash flood warning."
            ),
        )
        self._board_read = False
        self._has_bag = False
        self._mila_helped = False
        self._bridge_cleared = False   # Berto's decision answered safely

        self._build_world()
        self.hazards.append(FlashFloodHazard(rise_speed=2.5, max_height=80.0))
        self.objectives = [
            "You read the PAGASA warning board on the west bank",
            "You bring Mila's baby bag to her home",
            "You ask Berto, then cross the bridge",
            "You reach High Ground at the Safe Haven",
        ]
        self.guide_points = [
            self.guide_interactable("board"),
            lambda: next(
                (it.rect.center for it in self.block_map.items
                 if it.item_id == BAG_ITEM[0] and not it.collected),
                BAG_ITEM[2:4],
            ),
            lambda: (
                (410, 175) if self._bridge_cleared
                else self.guide_npc("Berto")()
            ),
            (530, 110),
        ]
        self.show_hint("Move with ARROW KEYS / WASD. Read the WARNING board.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "San Isidro Riverbank", width=MAP_W, height=MAP_H,
            ground_color=COLOR_GROUND_SAN_ISIDRO,
        )
        bm = self.block_map

        # River slicing vertically through the map, with a wooden bridge
        bm.add_water(310, 0, 70, 360)
        bm.add_bridge(310, 160, 70, 34)

        # West bank
        bm.add_road(30, 160, 280, 34)
        bm.add_building("house", "MILA'S HOME", 70, 90, 75, 55)
        bm.add_building("house", "STORAGE", 180, 90, 65, 50)

        # East bank
        bm.add_road(380, 160, 230, 34)
        bm.add_building("shelter", "RIVER SAFE HAVEN", 480, 80, 100, 60)
        bm.add_safe_zone(480, 80, 100, 60, label="HIGH GROUND", trigger_id=SAFE_TRIGGER)

        # Active flood danger zone at the low-lying river shoulder
        bm.add_hazard_zone("flood", *FLOOD_ZONE_RECT, label="FLASH FLOOD")

        # Mila's baby bag (pickup)
        bm.add_item(*BAG_ITEM)

        # Optional supply pickup
        self.add_pickup("battery", "SPARE BATTERY", (210, 175), "battery")

        # Interactable blocks
        self.add_interactable("board", "WARNING", BOARD_RECT, COLOR_BOARD, self._use_board)
        self.add_interactable("chairs", "PATIO CHAIRS", CHAIRS_RECT, COLOR_CHAIRS, self._use_chairs)
        self._east_rect = pygame.Rect(EAST_BANK_RECT)
        self.add_interactable(
            "east_bank", "EAST BANK", EAST_BANK_RECT, COLOR_UI_SAFE, None, prompt=False, alpha=60
        )

        # Stepping into the flood zone is dangerous
        self.watch_zone(FLOOD_ZONE_RECT, self._on_enter_flood)

        # NPCs (Berto now waits on the west bank, before the bridge)
        self.add_npc("mila", "Mila", (110, 150), MILA_LINES, role="vulnerable")
        self.add_npc("berto", "Berto", (275, 172), BERTO_LINES, role="resident")

        self.player.pos = pygame.Vector2(*PLAYER_SPAWN)
        self.player.rect.topleft = PLAYER_SPAWN

    # ------------------------------------------------------------------
    # Objective flow
    # ------------------------------------------------------------------
    def _check_objectives(self):
        while True:
            i = self.current_objective_idx
            if i == 0 and self._board_read:
                pass
            elif i == 1 and self._mila_helped:
                pass
            else:
                break
            self.complete_objective()
            self._on_objective_changed()

    def _on_objective_changed(self):
        idx = self.current_objective_idx
        if idx == 1:
            self.show_hint("Find Mila's BABY BAG on the road, then talk to her.", 5.0)
        elif idx == 2:
            self.show_hint("Talk to Berto near the bridge.", 5.0)
        elif idx == 3:
            self.stop_countdown()
            self.show_hint("Across! Now run to the HIGH GROUND at the Safe Haven.", 5.0)

    # ------------------------------------------------------------------
    # Step 0: warning board
    # ------------------------------------------------------------------
    def _use_board(self, item):
        if self._board_read:
            self.start_dialogue("PAGASA Warning", BOARD_LINES)
            return
        self.start_minigame(
            TimingMeter(
                "READ RAIN WARNING",
                "",
                steps=["Note the orange warning", "Never wade moving floodwater"],
                speed=0.8,
                zone=0.30,
                max_misses=3,
                icon="radio",
                win_text="WARNING READ!",
                fail_text="READ IT AGAIN!",
            ),
            on_win=self._board_minigame_done,
            on_fail=lambda: self.show_hint("Read the warning carefully. Try again.", 3.0),
        )

    def _board_minigame_done(self):
        self._board_read = True
        board = next(i for i in self.interactables if i["key"] == "board")
        board["done"] = True
        self.start_dialogue("PAGASA Warning", BOARD_LINES)
        self._check_objectives()

    # ------------------------------------------------------------------
    # Step 1: Mila and the baby bag
    # ------------------------------------------------------------------
    def on_item_collected(self, item_id: str):
        if item_id == BAG_ITEM[0]:
            self._has_bag = True
            self.show_hint("Got the baby bag! Bring it to Mila.", 4.0)

    def on_npc_interacted(self, npc):
        idx = self.current_objective_idx

        if npc.name == "Mila" and not self._mila_helped:
            if self._has_bag:
                self._mila_helped = True
                self.score_system.assist_resident("Mila")
                self.start_dialogue(npc.name, MILA_THANKS)
                self._check_objectives()
            else:
                self.show_hint("Find the BABY BAG on the road first.", 4.0)

        elif npc.name == "Berto":
            if idx < 2:
                self.show_hint("Berto: help Mila first, then come see me.", 4.0)
            elif idx == 2 and not self._bridge_cleared:
                self._ask_about_bridge()

    # ------------------------------------------------------------------
    # Step 2: the bridge decision, then a timed crossing
    # ------------------------------------------------------------------
    def _ask_about_bridge(self):
        def on_safe():
            self._bridge_cleared = True
            self.start_countdown(CROSS_SECONDS, "BRIDGE CLOSING", self._on_too_slow)
            self.show_hint("Cross NOW, holding the railing! Reach the EAST BANK.", 5.0)

        self.ask(
            decision_id="flood_wade_choice",
            prompt="Water is spilling onto the bridge ramp. What now?",
            options=[
                {
                    "text": "Cross now while footing is clear, hold the railing",
                    "safe": True,
                    "lesson": "Crossing early, before the crest, prevents being stranded.",
                },
                {
                    "text": "Wade the mudflat to save the patio furniture",
                    "safe": False,
                    "lesson": "Valuing goods over life in a flash flood leads to drowning.",
                },
            ],
            on_safe=on_safe,
            retry_hint="Never risk your life for furniture. Think again.",
        )

    def _on_too_slow(self):
        self.record_score("evacuations_delayed")
        self.show_hint("Hurry! The water is rising. Cross to the EAST BANK!", 4.0)
        self.start_countdown(CROSS_RETRY_SECONDS, "BRIDGE CLOSING", self._on_too_slow)

    def update(self, dt: float):
        super().update(dt)
        if self.legend_screen.visible or self.show_lesson_modal or self.pause_menu.visible:
            return
        if self.current_objective_idx == 2 and self.player.rect.colliderect(self._east_rect):
            if self._bridge_cleared:
                self.complete_objective()
                self._on_objective_changed()
            elif self.hint_timer <= 0:
                self.show_hint("Talk to Berto on the west bank before crossing.", 3.5)

    # ------------------------------------------------------------------
    # Dangers
    # ------------------------------------------------------------------
    def _on_enter_flood(self):
        self.record_score("unsafe_actions")
        self.show_hint("Floodwater! Just 15 cm of moving water can sweep you away.", 4.5)

    def _use_chairs(self, item):
        if item["done"]:
            return
        item["done"] = True
        self.record_score("unsafe_actions")
        self.show_hint("Furniture isn't worth your life! Get back to safety.", 4.5)

    # ------------------------------------------------------------------
    # Step 3: high ground
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id != SAFE_TRIGGER:
            return
        if self.current_objective_idx >= 3:
            self.stop_countdown()
            self.score_system.complete_evacuation("prologue_2")
            self.complete_level()
        elif self.hint_timer <= 0:
            self.show_hint("Finish your earlier tasks before settling here.", 3.0)