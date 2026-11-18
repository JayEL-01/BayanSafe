"""Chapter 4 - Level 1: Plains Gale & Farm Defense (North East Plains).

Location: Agricultural Rice Fields & Farm Dikes.
Disaster: Typhoon Wind & Inundating Rain (TCWS #2).
Objectives: Check livestock corral, assist Jun in sandbagging river dike, reach farm hall.

Pixel-game layer:
  * Pickups: BURLAP SANDBAG, HEAVY TETHER ROPE, WORK GLOVES.
  * Mini-games: Livestock Release (TimingMeter), Sandbag Dike Stacking (Mash).
  * Pressure: Gale wind gusts, rising irrigation creek, tethered animal drowning hazard.
  * Visuals: Rain particles, wind drift, lightning flash, agricultural ground.
"""

from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    LightningFlash,
    TimingMeter,
    Mash,
    draw_water,
    draw_wading_ripples,
)
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import (
    COLOR_GROUND_PLAINS,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class Chapter4Level1Typhoon(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    CREEK_RECT = (140, 155, 260, 45)
    CORRAL_POS = (180, 135)
    DIKE_BREACH_POS = (280, 140)
    JUN_POS = (115, 140)
    SILO_ZONE = (460, 50, 120, 80)

    # Pickups
    SANDBAG_POS = (75, 135)
    ROPE_POS = (140, 220)
    GLOVES_POS = (220, 135)

    GALE_TIME = 130.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_1_typhoon",
            title="Chapter 4 - Level 1: Winds Over the Fields",
            subtitle="North East Plains - Agricultural Flood Defense",
            disaster_type="Typhoon (PAGASA TCWS #2)",
            lesson_source="Department of Agriculture (DA) Disaster Risk Reduction & Management in Agriculture Guidelines",
            lesson_text=(
                "Agricultural communities must execute early harvest of mature crops upon storm advisory.\n"
                "Unhitch and move farm work animals (carabaos, cattle) to higher earthen knolls;\n"
                "never tether livestock in low-lying pastures where rising floodwaters cause drowning.\n"
                "Reinforce earthen irrigation bunds with interlocked burlap sandbags."
            ),
        )

        # Progress flags
        self._jun_assisted: bool = False
        self._livestock_freed: bool = False
        self._dike_reinforced: bool = False
        self._gale_intensity: float = 0.20

        # Effects
        self.rain = ParticleField("rain", seed=18, count=36)
        self.lightning = LightningFlash()
        self.vignette = Vignette(color=(25, 40, 30), max_alpha=150)

        # Build world & hazards
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=2))

        # Checkpoint & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("gale", "GALE WIND", 0.20, good_high=False)
        self.start_countdown(self.GALE_TIME, "CREEK CREST", on_expire=self._creek_crest)

        # Structured quest steps
        self.set_steps([
            {
                "text": "Meet Jun at the flooded pasture corral",
                "done": lambda: self._jun_assisted,
                "hint": "Gale winds are howling! Find Jun near the farm corral.",
                "target": self.JUN_POS,
            },
            {
                "text": "Untether trapped animals at the corral",
                "done": lambda: self._livestock_freed,
                "hint": "Interact with the corral gate to release tethered carabaos.",
                "target": self.CORRAL_POS,
            },
            {
                "text": "Sandbag the breached irrigation dike",
                "done": lambda: self._dike_reinforced,
                "hint": "Stack sandbags along the breached dike before floodwater spreads.",
                "target": self.DIKE_BREACH_POS,
            },
            {
                "text": "Evacuate families to the elevated Grain Silo",
                "done": lambda: self.completed,
                "hint": "Reach the concrete high ground at the Grain Silo shelter!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Heavy typhoon gale over the plains! Check on farm animals and dikes.", 5.0)

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("North East Agricultural Plains", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Dirt farm roads and dikes
        bm.add_path(30, 160, 580, 36)
        bm.add_road(300, 30, 36, 270)

        # Irrigation ditch flood zone
        bm.add_hazard_zone("flood", *self.CREEK_RECT, label="IRRIGATION CANAL")
        self.watch_zone(self.CREEK_RECT, self._touch_creek)

        # Buildings
        bm.add_building("house", "FARMHOUSE", 60, 60, 85, 60)
        bm.add_building("warehouse", "CORRAL", 180, 60, 80, 60)
        bm.add_building("shelter", "GRAIN SILO", 460, 50, 120, 80)
        bm.add_safe_zone(*self.SILO_ZONE, label="GRAIN SILO", trigger_id="silo_safe")

        # Interactables
        self.add_interactable(
            "corral_gate", "LIVESTOCK PEN",
            (self.CORRAL_POS[0] - 8, self.CORRAL_POS[1] - 8, 16, 16),
            (140, 100, 50),
            on_interact=self._interact_corral,
        )

        self.add_interactable(
            "dike_breach", "IRRIGATION DIKE",
            (self.DIKE_BREACH_POS[0] - 8, self.DIKE_BREACH_POS[1] - 8, 16, 16),
            (170, 140, 70),
            on_interact=self._interact_dike,
        )

        # Pickups
        self.add_pickup("sandbag", "BURLAP SANDBAG", self.SANDBAG_POS, "gobag")
        self.add_pickup("rope", "HEAVY TETHER ROPE", self.ROPE_POS, "stick")
        self.add_pickup("gloves", "WORK GLOVES", self.GLOVES_POS, "hardhat")

        # NPCs
        self.add_npc(
            "jun",
            "Jun",
            self.JUN_POS,
            [
                "The rain over the plains hasn't stopped for eight hours!",
                "Our carabaos were tethered near the river creek! Rising water will drown them!",
                "Help me untether them to high ground, then sandbag the irrigation bund!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazard Callbacks & Setbacks
    # ------------------------------------------------------------------
    def _touch_creek(self):
        if not self._dike_reinforced and not self.is_busy():
            self.hurt("Swirling irrigation water pulled your boots into deep silt!", penalty=4.0, respawn=True)

    def _creek_crest(self):
        self.hurt("The irrigation creek crested over the low dike! Recover quickly!", penalty=6.0, respawn=True)
        self.start_countdown(50.0, "CREEK RE-CREST", on_expire=self._creek_crest)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Jun" or self.is_busy():
            return

        if not self._jun_assisted:
            self.start_dialogue(
                "Jun",
                [
                    "Listen to the storm wind roaring across the fields! The creek is overflowing!",
                    "Where should we move the carabaos and cattle before the pasture drowns?",
                ],
            )
            self.ask(
                decision_id="plains_animal_rescue_choice",
                prompt="Where should farm livestock be relocated before the river crests?",
                options=[
                    {
                        "text": "Move cattle to designated elevated communal mounds and untether them",
                        "safe": True,
                        "lesson": "Tethered animals drown when water levels rise; elevated mounds preserve herds.",
                    },
                    {
                        "text": "Lock all cattle inside a padlocked low-ground wooden pen near the creek",
                        "safe": False,
                        "lesson": "Confining animals in flood paths leads to 100% livestock mortality.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never tether or padlock animals in low-lying flood paths!",
            )
        elif not self._livestock_freed:
            self.start_dialogue(
                "Jun",
                [
                    "Hurry to the corral gate! Untether the carabaos so they can scramble up the mound!",
                ],
            )
        elif not self._dike_reinforced:
            self.start_dialogue(
                "Jun",
                [
                    "The animals are safe on the knoll! Now pack sandbags along the irrigation breach!",
                ],
            )
        else:
            self.start_dialogue(
                "Jun",
                [
                    "The dike is holding! Run for the Agricultural Grain Silo before the gale intensifies!",
                ],
            )

    def _on_decision_safe(self):
        if not self._jun_assisted:
            self._jun_assisted = True
            self.score_system.assist_resident("Jun")
            self.record_score("warnings_followed", 1)

        self.show_hint("Head to the CORRAL gate to untether the trapped work animals!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Livestock Release & Dike Stacking
    # ------------------------------------------------------------------
    def _interact_corral(self):
        if not self._jun_assisted:
            self.show_hint("Talk to Jun before cutting corral lines.", 3.0)
            return

        if self._livestock_freed:
            self.show_hint("Corral opened! Carabaos are safe on the communal mound.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="UNTETHER WORK ANIMALS",
                hint="Slice heavy hemp tethers cleanly so cattle can run free",
                rounds=2,
                speed=1.0,
                zone=0.25,
                steps=["Cut carabao lead rope", "Open high-mound pasture gate"],
                win_text="ANIMALS FREED TO HIGH MOUND!",
                fail_text="ROPE SNARLED! RETRY",
                icon="stick",
            ),
            on_win=self._corral_success,
            on_fail=lambda: self.show_hint("Tether tangled in the latch. Cut it cleanly!", 3.0),
        )

    def _corral_success(self):
        self._livestock_freed = True
        self.set_checkpoint(self.CORRAL_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Livestock safe! Now head east to sandbag the crumbling DIKE breach!", 5.0)

    def _interact_dike(self):
        if not self._livestock_freed:
            self.show_hint("Free the trapped livestock first so they don't drown!", 3.5)
            return

        if self._dike_reinforced:
            self.show_hint("Sandbag revetment holding firm against the creek current.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="STACK SANDBAG REVETMENT",
                hint="Mash SPACE to hoist and interlock burlap sandbags!",
                target=16,
                decay=2.3,
                time_limit=8.0,
                icon="gobag",
                win_text="DIKE REINFORCED - BREACH SEALED!",
                fail_text="SANDBAG WASHED AWAY! RETRY",
            ),
            on_win=self._dike_success,
            on_fail=lambda: self.show_hint("Current washed the top bag off. Pack tightly and stomp down!", 3.0),
        )

    def _dike_success(self):
        self._dike_reinforced = True
        self.set_checkpoint(self.DIKE_BREACH_POS)
        self.show_hint("The dike is secured! Evacuate to the elevated GRAIN SILO!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "silo_safe" and not self.completed:
            if not self._dike_reinforced:
                self.show_hint("Secure the animals and dike before retreating to shelter!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch4_1")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.rain.update(dt)
        self.lightning.update(dt)

        self._gale_intensity = min(0.85, 0.20 + (self.level_time / 140.0) * 0.65)
        self.set_meter("gale", "GALE WIND", self._gale_intensity, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Irrigation ditch water
        creek_screen = self.camera.apply(pygame.Rect(self.CREEK_RECT))
        draw_water(surface, creek_screen, self._anim_t, alpha=110, color=(50, 110, 170), foam=True, depth=True)

        if self.player.rect.colliderect(pygame.Rect(self.CREEK_RECT)):
            draw_wading_ripples(surface, self.camera, self.player.rect, self._anim_t)

    def draw_over_world(self, surface: pygame.Surface):
        self.rain.draw(surface)
        self.vignette.draw(surface, strength=0.20 + 0.50 * self._gale_intensity)
        self.lightning.draw(surface)
