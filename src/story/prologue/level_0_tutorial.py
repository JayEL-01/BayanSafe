"""Prologue A - The First Warning (San Isidro): an interactive preparation sequence.

The player prepares the barangay for an incoming typhoon. Every step is
something to DO, not just read:

  0. Read the PAGASA advisory board           (interact with the board)
  1. Pack the Go-Bag: pick the 4 essentials,  (walk into items; avoid the
     avoid the non-essentials                  TV / game / jewelry traps)
  2. Secure the home: clear the drain and      (interact with 2 objects)
     secure the roof
  3. Persuade Lola Teresa to evacuate          (talk + decision)
  4. EVACUATE: the siren sounds, reach the     (countdown timer + zone)
     Barangay Hall before time runs out
  5. Report to Captain Reyes: "go back for     (decision: life vs property)
     the TV?"
  6. Check the damaged radio                   (story reveal, ends the level)

Objectives 0-2 can be done in any order. The tutorial never softlocks: if the
evacuation timer runs out, the player gets a short retry window.

Needs the updated base_level.py (show_hint + add_interactable).
"""

import pygame
from src.story.base_level import BaseLevel, TimingMeter
from src.maps.block_map import BlockMap
from src.config.palette import (
    COLOR_GROUND_SAN_ISIDRO,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)
from src.core.decision_system import Decision


# ---------------------------------------------------------------------------
# Easy-to-edit settings (change numbers here, not inside the code below)
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (100, 175)

# Go-Bag essentials: (item_id, label, x, y)
ESSENTIAL_ITEMS = [
    ("water", "WATER", 100, 140),
    ("food", "FOOD", 115, 140),
    ("firstaid", "MEDIKIT", 130, 140),
    ("flashlight", "TORCH", 145, 140),
]
# Non-essential "traps": picking these is a mistake (limited Go-Bag space)
TRAP_ITEMS = [
    ("tv", "TV", 150, 205),
    ("jewelry", "JEWELS", 235, 205),
    ("game", "GAME", 330, 205),
]
ESSENTIAL_IDS = {item[0] for item in ESSENTIAL_ITEMS}
TRAP_IDS = {item[0] for item in TRAP_ITEMS}

# Interactable blocks: (x, y, w, h)
BOARD_RECT = (250, 135, 18, 14)
DRAIN_RECT = (322, 198, 18, 12)
ROOF_RECT = (205, 128, 18, 12)
RADIO_RECT = (484, 100, 16, 12)
EVAC_RECT = (372, 134, 110, 26)  # safe zone in front of the Barangay Hall

COLOR_BOARD = (230, 200, 60)
COLOR_DRAIN = (110, 110, 125)
COLOR_ROOF = (170, 120, 70)
COLOR_RADIO = (200, 70, 70)

EVAC_SECONDS = 30.0        # time to reach the Barangay Hall after the siren
EVAC_RETRY_SECONDS = 20.0  # extra time if the first countdown runs out

DECISION_PERSUADE = "tutorial_persuade_lola"
DECISION_GO_BACK = "tutorial_go_back_for_tv"

# Short messages (the hint banner fits about 2 lines of ~50 characters)
OBJECTIVE_HINTS = {
    1: "Pack your Go-Bag! Walk into the 4 essentials only.",
    2: "Secure your home: clear the DRAIN and fix the ROOF.",
    3: "Talk to Lola Teresa. She refuses to leave her house.",
    4: "SIREN! Reach the EVAC CENTER and report to Captain Reyes.",
}

BOARD_LINES = [
    "PAGASA Tropical Cyclone Advisory No. 1",
    "A cyclone may bring heavy rain and strong winds.",
    "Prepare early: pack a Go-Bag and secure your home.",
    "Listen for barangay evacuation orders.",
]
ROSA_LINES = [
    "Magandang umaga! Is your Go-Bag ready?",
    "Pack only essentials: water, food, medikit, torch.",
    "TVs and jewelry can wait. Lives come first!",
]
LOLA_LINES = [
    "Naku, I will not leave my house, anak.",
    "It has stood here for forty years!",
]
LOLA_AFTER_LINES = ["Salamat, anak. Let's go to the Barangay Hall."]
REYES_LINES = [
    "Attention! PAGASA reports an abnormal cyclonic low.",
    "All barangay volunteers are on Blue Alert.",
    "Prepare your Go-Bag and check our drainage.",
]
REYES_AFTER_LINES = [
    "Well done. Everyone is safe at the center.",
    "But the water is rising fast...",
]
RADIO_LINES = [
    "[STATIC] ...kzzt... coordinates received...",
    "A strange symbol flashes on the radio screen.",
    "Who is sending this signal? Keep this radio safe.",
]


class PrologueTutorialLevel(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="tutorial",
            title="Prologue: The First Warning",
            subtitle="San Isidro - Disaster Preparedness Tutorial",
            disaster_type="Typhoon Advisory",
            lesson_source="NDRRMC National Disaster Risk Reduction & Management Plan (NDRP 2024)",
            lesson_text=(
                "Preparation begins before any storm warning is raised.\n"
                "Every household must maintain a 72-Hour Emergency Go-Bag containing:\n"
                "clean drinking water (1 gal/person/day), non-perishable food, first aid,\n"
                "battery-powered transistor radio, and waterproof identification docs.\n"
                "Evacuate early: property can be replaced, lives cannot."
            ),
        )
        # Progress flags
        self._state = "prepare"          # prepare -> evac -> hall
        self._board_read = False
        self._drain_done = False
        self._roof_done = False
        self._essentials = 0
        self._persuaded = False
        self._reported = False
        self._evac_time = 0.0
        self._evac_failed_once = False
        self._pending_decision = None    # function that builds the next Decision
        self._radio_played = False

        self._build_world()
        self.objectives = [
            "You read the PAGASA board at the village notice area",
            "You pack four Go-Bag essentials at home",
            "You clear the drain and fix the roof at home",
            "You persuade Lola Teresa at her house to evacuate",
            "You evacuate, report, and check the radio at Barangay Hall",
        ]
        self.guide_points = [
            self.guide_interactable("board"),
            lambda: next(
                (it.rect.center for it in self.block_map.items
                 if it.item_id in ESSENTIAL_IDS and not it.collected),
                (120, 140),
            ),
            lambda: next(
                (i["rect"].center for i in self.interactables
                 if i["key"] in ("drain", "roof") and not i["done"]),
                DRAIN_RECT[:2],
            ),
            self.guide_npc("Lola Teresa"),
            lambda: (
                self._evac_rect.center if self._state == "evac"
                else self.guide_interactable("radio")() if self._reported
                else self.guide_npc("Captain Reyes")()
            ),
        ]
        self.show_hint("Use ARROW KEYS / WASD to move. Find the ADVISORY board.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "San Isidro Village", width=MAP_W, height=MAP_H,
            ground_color=COLOR_GROUND_SAN_ISIDRO,
        )
        bm = self.block_map

        # Roads and paths
        bm.add_road(60, 160, 520, 30)
        bm.add_road(280, 40, 30, 260)

        # Village buildings (code-rendered solid rectangles with labels)
        bm.add_building("commercial", "SARI-SARI", 80, 80, 70, 50)
        bm.add_building("shelter", "BRGY HALL", 380, 70, 90, 60)
        bm.add_building("house", "HOUSE 1", 180, 70, 60, 50)
        bm.add_building("house", "HOUSE 2", 120, 220, 70, 50)
        bm.add_building("house", "HOUSE 3", 360, 220, 70, 50)

        # Ocean water boundary at the south
        bm.add_water(0, 320, 640, 40)

        # Natural tree blocks
        for tx in (40, 240, 480, 540):
            bm.add_tree(tx, 40)
            bm.add_tree(tx + 20, 250)

        # Go-Bag essentials
        for item_id, label, x, y in ESSENTIAL_ITEMS:
            bm.add_item(item_id, label, x, y)

        # Non-essential traps (skipped quietly if the item type is unknown)
        for item_id, label, x, y in TRAP_ITEMS:
            try:
                bm.add_item(item_id, label, x, y)
            except Exception as err:  # noqa: BLE001
                print(f"[Prologue] Could not add trap item '{item_id}': {err}")

        # Optional supply pickup (counted in the mission supply score)
        self.add_pickup("whistle", "SAFETY WHISTLE", (270, 178), "whistle")

        # Interactable blocks and the evacuation zone
        self.add_interactable("board", "ADVISORY", BOARD_RECT, COLOR_BOARD, self._use_board)
        self.add_interactable("drain", "DRAIN", DRAIN_RECT, COLOR_DRAIN, self._use_drain)
        self.add_interactable("roof", "ROOF", ROOF_RECT, COLOR_ROOF, self._use_roof)
        self.add_interactable("radio", "RADIO", RADIO_RECT, COLOR_RADIO, self._use_radio)
        self._evac_rect = pygame.Rect(EVAC_RECT)
        self.add_interactable(
            "evac", "EVAC CENTER", EVAC_RECT, COLOR_UI_SAFE, None, prompt=False, alpha=90
        )

        # NPCs
        self.add_npc("aling_rosa", "Aling Rosa", (105, 135), ROSA_LINES, role="resident")
        self.add_npc("lola_teresa", "Lola Teresa", (210, 175), LOLA_LINES, role="resident")
        self.add_npc("captain_reyes", "Captain Reyes", (440, 128), REYES_LINES, role="official")

        # Player spawn
        self.player.pos = pygame.Vector2(*PLAYER_SPAWN)
        self.player.rect.topleft = PLAYER_SPAWN

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _item(self, key):
        return next(i for i in self.interactables if i["key"] == key)

    def _record(self, field: str, amount: int = 1):
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

    def _next(self):
        """Complete the current objective and react to the new one."""
        self.complete_objective()
        self._on_objective_changed()

    def _on_objective_changed(self):
        idx = self.current_objective_idx
        if idx in OBJECTIVE_HINTS:
            self.show_hint(OBJECTIVE_HINTS[idx], 5.0)
        if idx == 4:
            self._start_evacuation()

    def _check_prep_objectives(self):
        """Objectives 0-2 can be done in any order; advance when each is met."""
        while True:
            i = self.current_objective_idx
            if i == 0 and self._board_read:
                pass
            elif i == 1 and self._essentials >= len(ESSENTIAL_ITEMS):
                pass
            elif i == 2 and self._drain_done and self._roof_done:
                pass
            else:
                break
            self._next()

    def _queue_decision(self, builder):
        """Open a decision after the current dialogue closes (avoids overlap)."""
        self._pending_decision = builder

    # ------------------------------------------------------------------
    # Step 0: advisory board
    # ------------------------------------------------------------------
    def _use_board(self, item):
        if self._board_read:
            self.start_dialogue("PAGASA Advisory", BOARD_LINES)
            return
        self.start_minigame(
            TimingMeter(
                "READ PAGASA ADVISORY",
                "",
                steps=["Find the cyclone warning", "Note the preparation advice"],
                speed=0.75,
                zone=0.32,
                max_misses=3,
                icon="megaphone",
                win_text="ADVISORY READ!",
                fail_text="READ IT AGAIN!",
            ),
            on_win=self._board_minigame_done,
            on_fail=lambda: self.show_hint("Read the advisory carefully. Try again.", 3.0),
        )

    def _board_minigame_done(self):
        self._board_read = True
        self._item("board")["done"] = True
        self.start_dialogue("PAGASA Advisory", BOARD_LINES)
        self._check_prep_objectives()

    # ------------------------------------------------------------------
    # Step 1: Go-Bag (walk into items)
    # ------------------------------------------------------------------
    def on_item_collected(self, item_id: str):
        if item_id in TRAP_IDS:
            self._record("unsafe_actions")
            self.show_hint("Not essential! Go-Bag space is for survival items.", 4.5)
            return

        self._essentials = len(
            {it.item_id for it in self.block_map.items if it.collected} & ESSENTIAL_IDS
        )
        if self._essentials < len(ESSENTIAL_ITEMS):
            self.show_hint(f"Go-Bag: {self._essentials}/{len(ESSENTIAL_ITEMS)} essentials packed.", 3.5)
        self._check_prep_objectives()

    # ------------------------------------------------------------------
    # Step 2: secure the home (interactables)
    # ------------------------------------------------------------------
    def _use_drain(self, item):
        if item["done"]:
            self.show_hint("The drain is already clear.", 2.5)
            return
        item["done"] = True
        self._drain_done = True
        self._record("hazards_reported")
        self.show_hint("Drain cleared! Rain water can flow away now.", 3.5)
        self._check_prep_objectives()

    def _use_roof(self, item):
        if item["done"]:
            self.show_hint("The roof is already secured.", 2.5)
            return
        item["done"] = True
        self._roof_done = True
        self.show_hint("Roof secured! Strong winds can't lift it easily.", 3.5)
        self._check_prep_objectives()

    # ------------------------------------------------------------------
    # NPC talk
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        idx = self.current_objective_idx

        if npc.name == "Lola Teresa":
            if idx < 3:
                self.show_hint("Lola Teresa: finish preparing first, then talk again.", 4.0)
            elif idx == 3 and not self._persuaded:
                self._queue_decision(self._build_persuade_decision)
            elif self._persuaded:
                self.start_dialogue(npc.name, LOLA_AFTER_LINES)

        elif npc.name == "Captain Reyes":
            if idx == 4 and self._state == "hall":
                self.start_dialogue(npc.name, REYES_AFTER_LINES)
                self._queue_decision(self._build_go_back_decision)
            elif idx < 4 and self._state == "evac":
                self.show_hint("No time to talk! Get to the EVAC CENTER!", 3.0)

    # ------------------------------------------------------------------
    # Step 3: persuade Lola Teresa (decision; unsafe answer asks again)
    # ------------------------------------------------------------------
    def _build_persuade_decision(self):
        def on_decide(opt):
            if self._is_safe(opt):
                self._persuaded = True
                self._next()
            else:
                self.show_hint("Never leave a neighbor behind. Try again.", 3.5)
                self._queue_decision(self._build_persuade_decision)

        return Decision(
            decision_id=DECISION_PERSUADE,
            prompt="Lola Teresa won't leave her house. What do you do?",
            options=[
                {
                    "text": "Persuade her: lives matter more than the house",
                    "safe": True,
                    "lesson": "Help vulnerable residents evacuate early. A house can be rebuilt.",
                },
                {
                    "text": "Leave her and go on without her",
                    "safe": False,
                    "lesson": "Never leave vulnerable neighbors behind. Persuade them or ask responders for help.",
                },
            ],
            on_resolved=on_decide,
        )

    # ------------------------------------------------------------------
    # Step 4: evacuation countdown
    # ------------------------------------------------------------------
    def _start_evacuation(self):
        self._state = "evac"
        self.start_countdown(EVAC_SECONDS, "EVACUATE", self._on_evac_late)

    def update(self, dt: float):
        super().update(dt)
        if self.legend_screen.visible or self.show_lesson_modal or self.pause_menu.visible:
            return

        # Open any queued decision once dialogue and other decisions are closed
        if (
            self._pending_decision
            and not self.decision_system.is_active()
            and self.active_dialogue is None
        ):
            builder, self._pending_decision = self._pending_decision, None
            self.trigger_decision(builder())

        if self._radio_played and self.active_dialogue is None:
            self._radio_played = False
            self._next()  # last objective: the level completes

        if self._state == "evac" and self.player.rect.colliderect(self._evac_rect):
            self._state = "hall"
            self.stop_countdown()
            self.show_hint("Safe! Report to Captain Reyes at the Barangay Hall.", 4.5)

    def _on_evac_late(self):
        self._record("evacuations_delayed")
        self.show_hint("Too slow! Evacuate EARLY. Hurry to the EVAC CENTER!", 4.0)
        self.start_countdown(EVAC_RETRY_SECONDS, "EVACUATE", self._on_evac_late)

    # ------------------------------------------------------------------
    # Step 5: Captain Reyes asks about going back (life vs property)
    # ------------------------------------------------------------------
    def _build_go_back_decision(self):
        def on_decide(opt):
            if self._is_safe(opt):
                self._reported = True
                self.show_hint("Report logged. Check the damaged RADIO beside the Hall.", 4.5)
            else:
                self.show_hint("Going back is too dangerous. Think again.", 3.5)
                self._queue_decision(self._build_go_back_decision)

        return Decision(
            decision_id=DECISION_GO_BACK,
            prompt="Rising water! A TV was left at home. Go back for it?",
            options=[
                {
                    "text": "No. Stay at the center and tell responders",
                    "safe": True,
                    "lesson": "Never return for belongings during a storm. Life comes before property.",
                },
                {
                    "text": "Yes, run home quickly and grab it",
                    "safe": False,
                    "lesson": "Going back into rising water and wind puts your life at risk.",
                },
            ],
            on_resolved=on_decide,
        )

    @staticmethod
    def _is_safe(opt) -> bool:
        if isinstance(opt, dict):
            return bool(opt.get("safe", False))
        return bool(getattr(opt, "safe", False))

    # ------------------------------------------------------------------
    # Step 6: the radio (story reveal, ends the level)
    # ------------------------------------------------------------------
    def _use_radio(self, item):
        if self.current_objective_idx != 4 or self._state != "hall" or not self._reported:
            self.show_hint("The radio is crackling... finish your report first.", 3.5)
            return
        item["done"] = True
        self._radio_played = True
        self.start_dialogue("Damaged Radio", RADIO_LINES)
        # The level completes in update() once the radio dialogue is closed.