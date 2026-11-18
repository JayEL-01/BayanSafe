"""Prologue A - The First Warning (San Isidro): an interactive tutorial level.

Quest (6 steps, shown on the quest board):
  1. Talk to Aling Rosa                         (she teaches the controls)
  2. Read the PAGASA advisory board             (mini-game)
  3. Find the 4 Go-Bag essentials hidden around the map
                                                (walk into them; TV / jewels / game are traps)
  4. Clear the drain and secure the roof        (2 interactions)
  5. Persuade Lola Teresa to evacuate           (decision)
  6. Evacuate -> report to Captain Reyes -> check the radio
                                                (countdown, decision, story reveal)

Step 1 always comes first. Steps 2-4 can then be done in any order.
The tutorial never soft-locks: if the evacuation timer runs out, the player
gets a short retry window.

A small coach system shows one-time tips (movement, interacting, mini-game,
pickups, decisions, evacuation) and a "stuck" hint if the player idles.
"""

import pygame
from src.story.base_level import BaseLevel, TimingMeter
from src.maps.block_map import BlockMap
from src.config.palette import COLOR_GROUND_SAN_ISIDRO, COLOR_UI_SAFE
from src.core.decision_system import Decision


# ---------------------------------------------------------------------------
# Easy-to-edit settings (change numbers here, not inside the code below)
# ---------------------------------------------------------------------------
MAP_W, MAP_H = 640, 360
PLAYER_SPAWN = (100, 175)

# Key names shown in the tutorial text (wording only, not real input).
MOVE_KEYS_LABEL = "ARROW KEYS / WASD"
INTERACT_KEY_LABEL = "E"
MINIGAME_KEY_LABEL = "SPACE"

# Go-Bag essentials: (item_id, label, x, y)  -> spread across the whole map
ESSENTIAL_ITEMS = [
    ("water", "WATER", 60, 290),         # southwest, near the shore
    ("food", "FOOD", 215, 30),           # north, beside House 1
    ("firstaid", "MEDIKIT", 500, 215),   # east, beside House 3
    ("flashlight", "TORCH", 340, 285),   # south-center
]
# Non-essential "traps": picking these is a mistake (limited Go-Bag space)
TRAP_ITEMS = [
    ("tv", "TV", 150, 205),
    ("jewelry", "JEWELS", 235, 205),
    ("game", "GAME", 440, 285),
]
ESSENTIAL_IDS = {item[0] for item in ESSENTIAL_ITEMS}
TRAP_IDS = {item[0] for item in TRAP_ITEMS}

# Interactable blocks: (x, y, w, h)
BOARD_RECT = (250, 135, 18, 14)
DRAIN_RECT = (322, 120, 18, 12)
ROOF_RECT = (205, 128, 18, 12)
RADIO_RECT = (484, 100, 16, 12)
EVAC_RECT = (372, 134, 110, 26)  # safe zone in front of the Barangay Hall

COLOR_BOARD = (230, 200, 60)
COLOR_DRAIN = (110, 110, 125)
COLOR_ROOF = (170, 120, 70)
COLOR_RADIO = (200, 70, 70)

EVAC_SECONDS = 30.0        # time to reach the Barangay Hall after the siren
EVAC_RETRY_SECONDS = 20.0  # extra time if the first countdown runs out

# Tutorial coach settings
MOVE_TIP_DISTANCE = 40     # pixels walked before the "moved" tip fires
NEAR_DISTANCE = 26         # how close counts as "next to" a block
STUCK_SECONDS = 35.0       # no progress for this long -> stuck hint
ROSA_DIALOGUE_WAIT = 0.25  # seconds to wait for the engine's own NPC dialogue
NEAR_NPC_DISTANCE = 70     # pixels: "standing next to Aling Rosa"

DECISION_PERSUADE = "tutorial_persuade_lola"
DECISION_GO_BACK = "tutorial_go_back_for_tv"

# Objective indexes (keeps the code below readable)
OBJ_ROSA, OBJ_BOARD, OBJ_BAG, OBJ_HOME, OBJ_LOLA, OBJ_EVAC = range(6)

# Quest steps (kept short so the quest board stays compact)
OBJECTIVES = [
    "[1/6] Talk to Aling Rosa near the Sari-Sari store",
    "[2/6] Read the PAGASA board near the village center",
    "[3/6] Find the 4 Go-Bag essentials around the village",
    "[4/6] Clear the DRAIN and fix the ROOF",
    "[5/6] Persuade Lola Teresa to evacuate",
    "[6/6] Evacuate, report to Captain Reyes, check the RADIO",
]

# Shown when an objective becomes ACTIVE (key = objective index).
OBJECTIVE_HINTS = {
    OBJ_BOARD: "Good! Now read the PAGASA ADVISORY board.",
    OBJ_BAG: "Find the 4 Go-Bag essentials hidden around the village!",
    OBJ_HOME: "Secure your home: clear the DRAIN and fix the ROOF.",
    OBJ_LOLA: "Talk to Lola Teresa. She refuses to leave her house.",
    OBJ_EVAC: "SIREN! Reach the EVAC CENTER and report to Captain Reyes.",
}

# Shown when the player has not progressed for STUCK_SECONDS.
STUCK_HINTS = {
    OBJ_ROSA: f"Stuck? Walk up to Aling Rosa and press {INTERACT_KEY_LABEL}.",
    OBJ_BOARD: f"Stuck? Find the ADVISORY board and press {INTERACT_KEY_LABEL} next to it.",
    OBJ_BAG: "Stuck? Follow the guide arrow. Items are spread out!",
    OBJ_HOME: f"Stuck? Stand next to the DRAIN / ROOF and press {INTERACT_KEY_LABEL}.",
    OBJ_LOLA: f"Stuck? Walk up to Lola Teresa and press {INTERACT_KEY_LABEL}.",
    OBJ_EVAC: "Stuck? Follow the arrow to the green EVAC CENTER zone.",
}

# One-time coach tips: tip_id -> (text, seconds)
TIPS = {
    "moved": (
        f"Nice! Walk up to Aling Rosa and press {INTERACT_KEY_LABEL} to talk.", 5.5),
    "near_interactable": (
        f"Glowing block nearby! Stand next to it and press {INTERACT_KEY_LABEL}.", 5.0),
    "minigame": (
        f"MINI-GAME: press {MINIGAME_KEY_LABEL} when the marker is in the zone.", 5.0),
    "first_trap": (
        "TRAP! TV, jewels and games are not essentials. "
        "Go-Bag space is for survival items.", 5.5),
    "decision": (
        "DECISION: choose the SAFE option. Wrong answers let you try again.", 5.0),
    "hall_reached": (
        f"You made it! Walk up to Captain Reyes and press {INTERACT_KEY_LABEL}.", 5.0),
}

BOARD_LINES = [
    "PAGASA Tropical Cyclone Advisory No. 1",
    "A cyclone may bring heavy rain and strong winds.",
    "Prepare early: pack a Go-Bag and secure your home.",
    "Listen for barangay evacuation orders.",
]
ROSA_LINES = [
    "Magandang umaga! Welcome to San Isidro.",
    f"Move with {MOVE_KEYS_LABEL}. Press {INTERACT_KEY_LABEL} to use things.",
    "First, read the ADVISORY board in the village center.",
    "Then find water, food, a medikit and a torch for your Go-Bag.",
    "They are spread around the village. Follow the arrow!",
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
        self._rosa_talked = False
        self._board_read = False
        self._drain_done = False
        self._roof_done = False
        self._essentials = 0
        self._persuaded = False
        self._reported = False
        self._radio_played = False
        self._pending_decision = None    # builder of the next Decision (opens after dialogue)

        # Aling Rosa intro tracking (see _update_rosa_intro)
        self._rosa_pending = False
        self._rosa_wait = 0.0
        self._rosa_saw_dialogue = False

        # Tutorial coach state
        self._tips_shown = set()
        self._moved = False
        self._stuck_timer = 0.0
        self._last_idx = 0

        self._build_world()
        self.objectives = list(OBJECTIVES)
        self.guide_points = [
            self.guide_npc("Aling Rosa"),                      # 1 talk to Rosa
            self.guide_interactable("board"),                  # 2 advisory board
            lambda: next(                                      # 3 next essential
                (it.rect.center for it in self.block_map.items
                 if it.item_id in ESSENTIAL_IDS and not it.collected),
                (120, 140),
            ),
            lambda: next(                                      # 4 drain / roof
                (i["rect"].center for i in self.interactables
                 if i["key"] in ("drain", "roof") and not i["done"]),
                DRAIN_RECT[:2],
            ),
            self.guide_npc("Lola Teresa"),                     # 5 persuade Lola
            lambda: (                                          # 6 evac / report / radio
                self._evac_rect.center if self._state == "evac"
                else self.guide_interactable("radio")() if self._reported
                else self.guide_npc("Captain Reyes")()
            ),
        ]
        self.show_hint(
            f"Welcome! Move with {MOVE_KEYS_LABEL}. Find Aling Rosa to begin.", 7.0
        )
        self.enable_world_ambience()

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

        # Village buildings
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

        # Go-Bag essentials (spread out) and the non-essential traps
        for item_id, label, x, y in ESSENTIAL_ITEMS + TRAP_ITEMS:
            bm.add_item(item_id, label, x, y)

        # Interactable blocks and the evacuation zone
        self.add_interactable("board", "ADVISORY", BOARD_RECT, COLOR_BOARD, self._use_board)
        self.add_interactable("drain", "DRAIN", DRAIN_RECT, COLOR_DRAIN, self._use_drain)
        self.add_interactable("roof", "ROOF", ROOF_RECT, COLOR_ROOF, self._use_roof)
        self.add_interactable("radio", "RADIO", RADIO_RECT, COLOR_RADIO, self._use_radio)
        self._evac_rect = pygame.Rect(EVAC_RECT)
        self.add_interactable(
            "evac", "EVAC CENTER", EVAC_RECT, COLOR_UI_SAFE, None, prompt=False, alpha=90
        )

        # NPCs (Aling Rosa stands next to the spawn and starts the tutorial)
        self.add_npc("aling_rosa", "Aling Rosa", (60, 135), ROSA_LINES, role="resident")
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

    @staticmethod
    def _is_safe(opt) -> bool:
        if isinstance(opt, dict):
            return bool(opt.get("safe", False))
        return bool(getattr(opt, "safe", False))

    def _queue_decision(self, builder):
        """Open a decision after the current dialogue closes (avoids overlap)."""
        self._pending_decision = builder

    def _need_rosa(self) -> bool:
        """Block steps 2-4 until the player has talked to Aling Rosa."""
        if self._rosa_talked:
            return False
        self.show_hint("Talk to Aling Rosa first! She will explain what to do.", 4.0)
        return True

    # ------------------------------------------------------------------
    # Tutorial coach
    # ------------------------------------------------------------------
    def _tip(self, tip_id: str) -> bool:
        """Show a one-time tutorial tip. Returns True if it was shown now."""
        if tip_id in self._tips_shown or tip_id not in TIPS:
            return False
        self._tips_shown.add(tip_id)
        text, secs = TIPS[tip_id]
        self.show_hint(text, secs)
        self._stuck_timer = 0.0
        return True

    def _update_coach(self, dt: float):
        """Runs every frame while no dialogue / decision is open."""
        # Movement tip (only before the player has met Aling Rosa)
        if not self._moved:
            moved = self.player.pos.distance_to(pygame.Vector2(*PLAYER_SPAWN))
            if moved >= MOVE_TIP_DISTANCE:
                self._moved = True
                if not self._rosa_talked:
                    self._tip("moved")

        # Interact tip: first time the player is next to a usable block
        elif self._rosa_talked and "near_interactable" not in self._tips_shown:
            zone = self.player.rect.inflate(NEAR_DISTANCE, NEAR_DISTANCE)
            for it in self.interactables:
                if it["key"] == "evac" or it["done"]:
                    continue
                if zone.colliderect(it["rect"]):
                    self._tip("near_interactable")
                    break

        # Stuck hint: no progress for a while -> point the player onward
        if self._state == "prepare" and not self.completed:
            idx = self.current_objective_idx
            if idx != self._last_idx:
                self._last_idx = idx
                self._stuck_timer = 0.0
            self._stuck_timer += dt
            if self._stuck_timer >= STUCK_SECONDS:
                self._stuck_timer = 0.0
                if idx in STUCK_HINTS:
                    self.show_hint(STUCK_HINTS[idx], 5.0)

    def _next(self):
        """Complete the current objective and react to the new one."""
        if self.completed:
            return
        self.complete_objective()
        self._stuck_timer = 0.0
        idx = self.current_objective_idx
        self._last_idx = idx
        if idx in OBJECTIVE_HINTS:
            self.show_hint(OBJECTIVE_HINTS[idx], 5.0)
        if idx == OBJ_EVAC:
            self._start_evacuation()

    def _check_prep_objectives(self):
        """Steps 2-4 can be done in any order; advance as each one is met."""
        while True:
            i = self.current_objective_idx
            done = (
                (i == OBJ_BOARD and self._board_read)
                or (i == OBJ_BAG and self._essentials >= len(ESSENTIAL_ITEMS))
                or (i == OBJ_HOME and self._drain_done and self._roof_done)
            )
            if not done:
                break
            self._next()

    # ------------------------------------------------------------------
    # Step 1: talk to Aling Rosa (controls lesson)
    # ------------------------------------------------------------------
    def _start_rosa_intro(self):
        """Called the first time the player talks to Aling Rosa."""
        if self._rosa_talked or self._rosa_pending:
            return
        self._rosa_pending = True
        self._rosa_wait = 0.0
        self._rosa_saw_dialogue = False

    def _update_rosa_intro(self, dt: float):
        """Completes step 1 only AFTER Rosa's dialogue has been read.

        The engine may already open her NPC dialogue on interaction. If no
        dialogue appears shortly after, we open ROSA_LINES ourselves so the
        lesson is never skipped.
        """
        # Fallback detection: any dialogue opened while the player stands next
        # to Aling Rosa counts as talking to her, even if the engine never
        # calls on_npc_interacted for her.
        if (
            not self._rosa_talked
            and not self._rosa_pending
            and self.active_dialogue is not None
        ):
            try:
                rx, ry = self.guide_npc("Aling Rosa")()
                px, py = self.player.rect.center
                if (rx - px) ** 2 + (ry - py) ** 2 <= NEAR_NPC_DISTANCE ** 2:
                    self._rosa_pending = True
                    self._rosa_saw_dialogue = True
            except Exception:  # noqa: BLE001
                pass

        if not self._rosa_pending:
            return
        if self.active_dialogue is not None:
            self._rosa_saw_dialogue = True
            return
        if not self._rosa_saw_dialogue:
            self._rosa_wait += dt
            if self._rosa_wait >= ROSA_DIALOGUE_WAIT:
                self._rosa_saw_dialogue = True
                self.start_dialogue("Aling Rosa", ROSA_LINES)
            return
        # Dialogue was shown and is now closed -> step 1 done
        self._rosa_pending = False
        self._rosa_talked = True
        self._next()
        self._check_prep_objectives()   # in case steps were already satisfied

    # ------------------------------------------------------------------
    # Step 2: advisory board (mini-game tutorial)
    # ------------------------------------------------------------------
    def _use_board(self, item):
        if self._need_rosa():
            return
        if self._board_read:
            self.start_dialogue("PAGASA Advisory", BOARD_LINES)
            return
        self._tip("minigame")
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
            on_fail=lambda: self.show_hint(
                f"Missed! Wait for the zone, then press {MINIGAME_KEY_LABEL}. Try again.", 4.0
            ),
        )

    def _board_minigame_done(self):
        self._board_read = True
        self._item("board")["done"] = True
        self.start_dialogue("PAGASA Advisory", BOARD_LINES)
        self._check_prep_objectives()

    # ------------------------------------------------------------------
    # Step 3: Go-Bag (walk into items)
    # ------------------------------------------------------------------
    def on_item_collected(self, item_id: str):
        if item_id in TRAP_IDS:
            self._record("unsafe_actions")
            if not self._tip("first_trap"):
                self.show_hint("Not essential! Go-Bag space is for survival items.", 4.5)
            return

        self._essentials = len(
            {it.item_id for it in self.block_map.items if it.collected} & ESSENTIAL_IDS
        )
        total = len(ESSENTIAL_ITEMS)
        if self._essentials < total:
            self.show_hint(f"Go-Bag: {self._essentials}/{total} essentials packed.", 3.5)
            self._stuck_timer = 0.0
        self._check_prep_objectives()

    # ------------------------------------------------------------------
    # Step 4: secure the home (interactables)
    # ------------------------------------------------------------------
    def _use_drain(self, item):
        if self._need_rosa():
            return
        if item["done"]:
            self.show_hint("The drain is already clear.", 2.5)
            return
        item["done"] = True
        self._drain_done = True
        self._record("hazards_reported")
        if self._roof_done:
            self.show_hint("Drain cleared! Rain water can flow away now.", 3.5)
        else:
            self.show_hint("Drain cleared! Now fix the ROOF too.", 3.5)
        self._check_prep_objectives()

    def _use_roof(self, item):
        if self._need_rosa():
            return
        if item["done"]:
            self.show_hint("The roof is already secured.", 2.5)
            return
        item["done"] = True
        self._roof_done = True
        if self._drain_done:
            self.show_hint("Roof secured! Strong winds can't lift it easily.", 3.5)
        else:
            self.show_hint("Roof secured! Now clear the DRAIN too.", 3.5)
        self._check_prep_objectives()

    # ------------------------------------------------------------------
    # NPC talk
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        idx = self.current_objective_idx

        if npc.name == "Aling Rosa":
            if not self._rosa_talked:
                self._start_rosa_intro()
            else:
                self.show_hint(
                    "Aling Rosa: follow the arrow and finish your quest list!", 3.5)

        elif npc.name == "Lola Teresa":
            if idx < OBJ_LOLA:
                self.show_hint("Lola Teresa: finish preparing first, then talk again.", 4.0)
            elif idx == OBJ_LOLA and not self._persuaded:
                self._queue_decision(self._build_persuade_decision)
            elif self._persuaded:
                self.start_dialogue(npc.name, LOLA_AFTER_LINES)

        elif npc.name == "Captain Reyes":
            if self._state == "evac":
                self.show_hint("No time to talk! Get to the EVAC CENTER!", 3.0)
            elif self._state == "hall" and not self._reported:
                self.start_dialogue(npc.name, REYES_AFTER_LINES)
                self._queue_decision(self._build_go_back_decision)
            elif self._reported:
                self.show_hint("Check the damaged RADIO beside the Hall.", 3.5)

    # ------------------------------------------------------------------
    # Step 5: persuade Lola Teresa (decision; unsafe answer asks again)
    # ------------------------------------------------------------------
    def _build_persuade_decision(self):
        def on_decide(opt):
            if self._is_safe(opt):
                self._persuaded = True
                self._next()
            else:
                self.show_hint("Never leave a neighbor behind. Try again.", 3.5)
                self._queue_decision(self._build_persuade_decision)

        self._tip("decision")

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
    # Step 6: evacuate, report, check the radio
    # ------------------------------------------------------------------
    def _start_evacuation(self):
        self._state = "evac"
        self.start_countdown(EVAC_SECONDS, "EVACUATE", self._on_evac_late)

    def _on_evac_late(self):
        if self.completed or self._state != "evac":
            return
        self._record("evacuations_delayed")
        self.show_hint("Too slow! Evacuate EARLY. Hurry to the EVAC CENTER!", 4.0)
        self.start_countdown(EVAC_RETRY_SECONDS, "EVACUATE", self._on_evac_late)

    def update(self, dt: float):
        super().update(dt)
        if self.legend_screen.visible or self.show_lesson_modal or self.pause_menu.visible:
            return

        # Step 1 completes once Aling Rosa's dialogue has been read
        self._update_rosa_intro(dt)

        # Tutorial coach (movement / interact / stuck tips)
        if self.active_dialogue is None and not self.decision_system.is_active():
            self._update_coach(dt)

        # Open any queued decision once dialogue and other decisions are closed
        if (
            self._pending_decision
            and not self.decision_system.is_active()
            and self.active_dialogue is None
        ):
            builder, self._pending_decision = self._pending_decision, None
            self.trigger_decision(builder())

        # The level completes once the radio dialogue is closed
        if self._radio_played and self.active_dialogue is None:
            self._radio_played = False
            self._next()
            return

        if self._state == "evac" and self.player.rect.colliderect(self._evac_rect):
            self._state = "hall"
            self.stop_countdown()
            if not self._tip("hall_reached"):
                self.show_hint("Safe! Report to Captain Reyes at the Barangay Hall.", 4.5)

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

    def _use_radio(self, item):
        if self.current_objective_idx != OBJ_EVAC or self._state != "hall" or not self._reported:
            self.show_hint("The radio is crackling... finish your report first.", 3.5)
            return
        item["done"] = True
        self._radio_played = True
        self.start_dialogue("Damaged Radio", RADIO_LINES)