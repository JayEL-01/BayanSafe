"""Chapter 3 - Level 1: Tidal Inundation (Harbor).

Location: Harbor Docks & Pierfront.
Disaster: Flash Flood & Coastal Tidal Backflow.

Mission flow
    1. Buckle a life vest from the dock locker          (timing minigame)
    2. Cross the wet quay - slippery planks             (mash minigame to recover)
    3. Help Tito Ramon: choose safely, then tie lines   (decision + timing minigame)
    4. The surge starts: dodge drifting crates          (countdown + moving hazard)
    5. Force the jammed Harbor Office door              (mash minigame)

Optional supplies (first aid, radio, go-bag) boost the supply score.
"""

import pygame

from src.story.base_level import (
    BaseLevel,
    TimingMeter,
    Mash,
    FlyingDebris,
    ParticleField,
    Vignette,
    LightningFlash,
    ICONS,
    draw_water,
)
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import FlashFloodHazard
from src.config.palette import COLOR_GROUND_HARBOR


# ----------------------------------------------------------------------
# Custom icon for this level (10x10 grid, uses the shared palette letters)
# ----------------------------------------------------------------------
ICONS["lifevest"] = [
    "..kk..kk..",
    ".kook.kook",
    ".kooooook.",
    ".kowwwwok.",
    ".kooooook.",
    ".kowwwwok.",
    ".kooooook.",
    ".kooooook.",
    "..kkkkkk..",
    "..........",
]


class DriftingCrates(FlyingDebris):
    """Cargo crates swept along the quay by the surge.

    Reuses FlyingDebris timing / warning lanes / hit-testing, but draws
    wooden crates instead of roof sheets.
    """

    SHEET_W, SHEET_H = 18, 12

    def draw(self, surface, camera):
        super().draw(surface, camera)  # warning lanes (+ plain sheet underneath)
        for s in self.sheets:
            r = camera.apply(pygame.Rect(int(s["x"]), s["y"], self.SHEET_W, self.SHEET_H))
            pygame.draw.rect(surface, (140, 90, 50), r)
            pygame.draw.line(surface, (100, 64, 36), r.topleft, r.bottomright, 1)
            pygame.draw.line(surface, (100, 64, 36), r.topright, r.bottomleft, 1)
            pygame.draw.rect(surface, (24, 22, 32), r, 1)


class Chapter3Level1FlashFlood(BaseLevel):
    SURGE_TIME = 50.0        # seconds to reach the office once the surge starts
    SURGE_RETRY = 30.0       # seconds given after being swept back

    # Wet plank patches on the quay (world coords)
    WET_PATCHES = [
        (190, 154, 32, 20),
        (305, 172, 36, 20),
        (405, 152, 32, 20),
    ]

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_1_flash_flood",
            title="Chapter 3 - Level 1: The Flooded Pier",
            subtitle="Harbor Docks - Tidal Surge & River Discharge",
            disaster_type="Harbor Flash Flood & High Tide",
            lesson_source="Philippine Ports Authority (PPA) Maritime Port Disaster Safety Standards",
            lesson_text=(
                "During combined river runoff and astronomical high tides, dock quays become submerged.\n"
                "Unsecured shipping containers and cargo drums can float and crush personnel against bulkheads.\n"
                "Always wear approved life vests near harbor quays and keep clear of drifting cargo."
            ),
        )

        # Level state (set before building the world)
        self._cargo_state = "idle"      # idle | busy | done
        self._door_state = "idle"       # idle | busy
        self._door_cd = 0.0
        self._surge_active = False
        self.crates = None
        self._locker = None

        # Atmosphere
        self.rain = ParticleField("rain", seed=3)
        self.lightning = LightningFlash(interval=(6.0, 12.0), seed=11)
        self.vignette = Vignette(color=(10, 30, 70), max_alpha=110)

        self._build_world()

        self.hazards.append(FlashFloodHazard(rise_speed=2.2, max_height=75.0))
        self.objectives = [
            "You buckle a life vest at the dock locker",
            "You help Tito Ramon secure cargo at the pier",
            "You dodge crates to the Harbor Office",
        ]
        self.guide_points = [
            self.guide_interactable("locker"),
            self.guide_npc("Tito Ramon"),
            (520, 90),
        ]
        self.set_meter("tide", "TIDE", 0.0, good_high=False)
        self.show_hint("Wet planks are slippery. Wear a life vest first!", 5.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Harbor Docks & Wharves", width=640, height=360, ground_color=COLOR_GROUND_HARBOR
        )
        bm = self.block_map

        # Wharf, access ramp to the office, and the harbor water
        bm.add_road(30, 150, 580, 45)
        bm.add_road(490, 128, 40, 26)
        bm.add_water(0, 260, 640, 100)

        # Buildings
        bm.add_building("warehouse", "CARGO SHED", 60, 60, 95, 70)
        bm.add_building("warehouse", "COLD STORAGE", 180, 60, 90, 70)
        bm.add_building("shelter", "HARBOR OFFICE", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="HARBOR OFFICE", trigger_id="office_safe")

        # Life vest locker (interactable) + tray slot that stays dim until worn
        self._locker = self.add_interactable(
            "locker", "LIFE VEST", (64, 132, 22, 16), (200, 110, 40),
            on_interact=self._open_locker,
        )
        self.tray_slots.append({"key": "lifevest", "icon": "lifevest", "label": "Life Vest"})

        # Slippery patches: translucent zones + a watcher that triggers the slip
        for i, rect in enumerate(self.WET_PATCHES):
            self.add_interactable(
                f"wet_{i}", "", rect, (70, 130, 190), prompt=False, alpha=80
            )
            self.watch_zone(rect, self._slip)

        # Optional supplies (count toward the supply score)
        self.add_pickup("firstaid", "First Aid Kit", (225, 140), "firstaid")
        self.add_pickup("radio", "Radio", (345, 138), "radio")
        self.add_pickup("gobag", "Go-Bag", (435, 140), "gobag")

        # NPC
        self.add_npc(
            "tito_ramon",
            "Tito Ramon",
            (130, 140),
            [
                "The river water is rushing into the bay faster than the tide can drain it!",
                "These heavy pallet crates are starting to float off the low wharf!",
                "We need to tether them down and move immediately to the elevated Harbor Office!",
            ],
            role="resident",
        )

        # Player start + first checkpoint
        self.player.pos = pygame.Vector2(50, 165)
        self.player.rect.topleft = (50, 165)
        self.set_checkpoint((50, 165))

    # ------------------------------------------------------------------
    # Step 1: life vest minigame
    # ------------------------------------------------------------------
    def _open_locker(self, item):
        if self.has_item("lifevest"):
            self.show_hint("You're already wearing your life vest.", 2.5)
            return
        self.start_minigame(
            TimingMeter(
                "DON LIFE VEST", "",
                steps=["Slip your arms through", "Clip the chest buckle", "Cinch the side straps"],
                speed=0.8, zone=0.30, max_misses=3, icon="lifevest",
                win_text="VEST ON!", fail_text="STRAPS TANGLED!",
            ),
            on_win=self._vest_on,
            on_fail=lambda: self.show_hint("Straps tangled. Try the locker again.", 3.0),
        )

    def _vest_on(self):
        self.collected.add("lifevest")
        self._locker["done"] = True
        self.record_score("warnings_followed")
        self.set_checkpoint((90, 165))
        self.show_hint("Life vest secured. Now find Tito Ramon!", 4.0)
        if self.current_objective_idx == 0:
            self.complete_objective()

    # ------------------------------------------------------------------
    # Step 2: slippery planks
    # ------------------------------------------------------------------
    def _slip(self):
        if self.completed or not self.hurt("Slippery planks!"):
            return
        vest = self.has_item("lifevest")
        self.start_minigame(
            Mash(
                "SLIPPING!", "Mash SPACE to catch your balance!",
                target=4 if vest else 8, decay=1.2, time_limit=3.0,
                icon="stick", win_text="BALANCED!", fail_text="YOU FELL!",
            ),
            on_win=lambda: self.show_hint("Steady! Watch the wet boards.", 2.5),
            on_fail=self._fall,
        )

    def _respawn(self):
        if self.checkpoint is not None:
            cx, cy = self.checkpoint
            self.player.pos = pygame.Vector2(cx, cy)
            self.player.rect.topleft = (cx, cy)

    def _fall(self):
        self._respawn()
        if self.has_item("lifevest"):
            self.show_hint("Your life vest kept you afloat. Back to the checkpoint.", 3.5)
        else:
            self.show_hint("You fell in! A life vest would have helped.", 3.5)

    # ------------------------------------------------------------------
    # Step 3: Tito Ramon - decision, then rope minigame
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Tito Ramon":
            return

        if self._cargo_state == "done":
            self.start_dialogue(
                "Tito Ramon", ["Go, go! The Harbor Office is on high ground. I'm right behind you!"]
            )
            return

        if self._cargo_state == "busy":
            return

        if not self.has_item("lifevest"):
            self.start_dialogue(
                "Tito Ramon", ["Anak, where is your life vest? Get one from the locker first!"]
            )
            return

        self._cargo_state = "busy"
        self.ask(
            "harbor_cargo_tie_choice",
            "Heavy wooden crates are drifting toward the water edge. What is the priority?",
            [
                {
                    "text": "Secure essential lines from safe footing, then retreat to higher ground",
                    "safe": True,
                    "lesson": "Never position yourself between a floating container and a solid wall.",
                },
                {
                    "text": "Jump into the floodwater between moving crates to grab loose ropes",
                    "safe": False,
                    "lesson": "Floating debris exerts crushing forces that cause fatal blunt trauma.",
                },
            ],
            on_safe=self._start_rope_minigame,
            retry_hint="Floating crates can crush you. Choose the safer option.",
        )

    def _start_rope_minigame(self):
        self.start_minigame(
            TimingMeter(
                "SECURE CARGO LINES", "",
                steps=["Loop the rope on the bollard", "Pull the line taut", "Finish the cleat hitch"],
                speed=0.95, zone=0.24, max_misses=3, icon="stick",
                win_text="LINES SECURED!", fail_text="ROPE SLIPPED!",
            ),
            on_win=self._cargo_secured,
            on_fail=self._cargo_failed,
        )

    def _cargo_failed(self):
        self._cargo_state = "idle"
        self.show_hint("The rope slipped. Talk to Tito Ramon to try again.", 3.5)

    def _cargo_secured(self):
        self._cargo_state = "done"
        self.score_system.assist_resident("Tito Ramon")
        self.set_checkpoint((150, 165))
        if self.current_objective_idx == 1:
            self.complete_objective()
        self._begin_surge()

    # ------------------------------------------------------------------
    # Step 4: the surge (countdown + drifting crates)
    # ------------------------------------------------------------------
    def _begin_surge(self):
        self._surge_active = True
        lane = (30, 150, 580, 45)
        self.crates = DriftingCrates(lane, interval=(2.2, 3.6), speed=110.0, warn=1.0, seed=5)
        self.start_countdown(self.SURGE_TIME, "SURGE", self._surge_expired)
        self.show_hint("The surge is here! Dodge the crates and reach the office!", 5.0)

    def _surge_expired(self):
        self.hurt("The surge swept you back to Tito's position!", respawn=True)
        self.start_countdown(self.SURGE_RETRY, "SURGE", self._surge_expired)

    # ------------------------------------------------------------------
    # Step 5: Harbor Office door
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id != "office_safe" or self.completed:
            return
        if self.is_busy() or self._door_cd > 0:
            return

        if self.current_objective_idx < 2:
            self.show_hint("Finish your tasks before sheltering.", 3.0)
            self._door_cd = 3.0
            return

        self._door_state = "busy"
        self.start_minigame(
            Mash(
                "JAMMED DOOR", "Mash SPACE to force the door open!",
                target=14, decay=2.0, time_limit=8.0,
                icon="hardhat", win_text="DOOR OPEN!", fail_text="STUCK!",
            ),
            on_win=self._door_open,
            on_fail=self._door_failed,
        )

    def _door_failed(self):
        self._door_state = "idle"
        self._door_cd = 1.5
        self.show_hint("The door is stuck. Try again!", 2.5)

    def _door_open(self):
        self._door_state = "idle"
        self.stop_countdown()
        self.score_system.complete_evacuation("ch3_1")
        self.complete_objective()  # last objective -> completes the level

    # ------------------------------------------------------------------
    # Per-frame hooks
    # ------------------------------------------------------------------
    def _tide_ratio(self) -> float:
        for hz in self.hazards:
            for attr in ("height", "water_height", "current_height", "level"):
                val = getattr(hz, attr, None)
                if isinstance(val, (int, float)):
                    return max(0.0, min(1.0, val / 75.0))
        # Fallback if the hazard exposes no height value
        return max(0.0, min(1.0, self.level_time / 90.0))

    def update_level(self, dt: float):
        self.rain.update(dt)
        self.lightning.update(dt)
        self._door_cd = max(0.0, self._door_cd - dt)
        self.set_meter("tide", "TIDE", self._tide_ratio(), good_high=False)

        if self.crates is not None and not self.is_busy():
            self.crates.update(dt)
            if self.crates.hits(self.player.rect):
                self.hurt("A drifting crate hit you!", penalty=4.0)

    def draw_under_player(self, surface: pygame.Surface):
        # Animated harbor water + sheen on the wet plank patches
        water = self.camera.apply(pygame.Rect(0, 260, 640, 100))
        draw_water(surface, water, self._anim_t, alpha=90)
        for rect in self.WET_PATCHES:
            draw_water(surface, self.camera.apply(pygame.Rect(rect)), self._anim_t, alpha=40)

    def draw_over_world(self, surface: pygame.Surface):
        if self.crates is not None:
            self.crates.draw(surface, self.camera)
        self.rain.draw(surface)
        self.vignette.draw(surface, strength=0.25 + 0.75 * self._tide_ratio())
        self.lightning.draw(surface)