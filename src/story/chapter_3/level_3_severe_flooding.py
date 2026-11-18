"""Chapter 3 - Level 3: Inundated Warehouses & Emergency Radio (Harbor).

Location: Harbor Warehouse District.
Disaster: Severe Flooding & Saltwater Inundation.
Objectives: Navigate flooded alleys, salvage marine radio with Rico dela Cruz, reach lighthouse.

Pixel-game layer:
  * Pickups: DRY BAG, SPARE BATTERY, WATERPROOF FLASHLIGHT.
  * Mini-games: Breaker Isolation (TimingMeter), Radio Frequency Lock (RadioTuning).
  * Pressure: Saltwater flood surge meter, electrocution / submerged obstacle setbacks.
  * Realistic water rendering: multi-layered saltwater with wave highlights, shoreline foam, and player wading ripples.
"""

import math
from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    LightningFlash,
    TimingMeter,
    RadioTuning,
    draw_water,
    draw_wading_ripples,
)
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import (
    COLOR_GROUND_HARBOR,
    COLOR_HAZARD_FLOOD,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
)
from src.ui import theme


class SilentSevereFloodingHazard(SevereFloodingHazard):
    """Severe flooding hazard logic without default flat block drawing,
    allowing custom realistic layered water and wading effects."""

    def draw_effects(self, surface, camera):
        pass


class Chapter3Level3SevereFlooding(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    FLOOD_LANE = (40, 155, 560, 60)
    DEEP_BASIN = (0, 275, 640, 85)
    BREAKER_POS = (112, 134)
    RADIO_BENCH = (212, 140)
    RICO_POS = (235, 140)
    LIGHTHOUSE_ZONE = (460, 45, 120, 90)

    # Submerged forklift hazard areas (standing saltwater obstacles)
    FORKLIFT_1 = (145, 165, 34, 26)
    FORKLIFT_2 = (325, 168, 34, 26)

    # Pickup coordinates
    DRYBAG_POS = (76, 134)
    BATTERY_POS = (275, 134)
    FLASHLIGHT_POS = (385, 138)

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_3_severe_flooding",
            title="Chapter 3 - Level 3: The Flooded Depots",
            subtitle="Harbor Warehouses - Marine Radio Salvage",
            disaster_type="Severe Coastal Flooding & Salt Surge",
            lesson_source="National Telecommunications Commission (NTC) & NDRRMC Emergency Telecoms Cluster Guidelines",
            lesson_text=(
                "Saltwater flooding rapidly corrodes electronic contacts and short-circuits power supplies.\n"
                "Emergency responders must maintain battery-powered high-frequency (HF) and VHF radios\n"
                "sealed in waterproof dry bags, keeping international distress frequency (VHF Ch 16) open.\n"
                "Never operate electrical switchgear while standing in submerged salt floodwater."
            ),
        )

        # Progress flags
        self._rico_assisted: bool = False
        self._breaker_off: bool = False
        self._radio_tuned: bool = False
        self._radio_packed: bool = False
        self._surge_level: float = 0.25

        # Visual atmospheric effects
        self.rain = ParticleField("rain", seed=14, count=28)
        self.lightning = LightningFlash()
        self.vignette = Vignette(color=(20, 35, 55), max_alpha=150)

        # Build world and add hazards
        self._build_world()
        self.hazards.append(SilentSevereFloodingHazard(shallow_rects=[self.FLOOD_LANE], deep_rects=[self.DEEP_BASIN]))

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("surge", "SALT SURGE", 0.25, good_high=False)

        # Structured linear quest steps with bobbing target arrow
        self.set_steps([
            {
                "text": "Cross flooded warehouse yard and speak with Rico dela Cruz",
                "done": lambda: self._rico_assisted,
                "hint": "Saltwater is rising fast! Find Rico near the loading dock of Depot 2.",
                "target": self.RICO_POS,
            },
            {
                "text": "Safely isolate breaker before salvaging the VHF marine radio",
                "done": lambda: self._breaker_off,
                "hint": "Check the dry breaker panel on Depot 1 platform to kill electrical feed.",
                "target": self.BREAKER_POS,
            },
            {
                "text": "Pack radio in dry bag and tune to distress Channel 16",
                "done": lambda: self._radio_tuned,
                "hint": "Lock onto international distress channel 156.80 MHz [CH 16].",
                "target": self.RADIO_BENCH,
            },
            {
                "text": "Carry sealed marine radio to elevated Lighthouse Tower",
                "done": lambda: self.completed,
                "hint": "Climb concrete stairs to the elevated Lighthouse Tower!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Heavy saltwater flood! Watch out for submerged industrial equipment.", 5.0)

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Harbor Warehouse District", width=640, height=360, ground_color=COLOR_GROUND_HARBOR)
        bm = self.block_map

        # Main road & loading alleys
        bm.add_road(30, 160, 580, 40)
        bm.add_road(460, 40, 50, 130)

        # Primary flood hazard zones
        bm.add_hazard_zone("flood", *self.FLOOD_LANE, label="SALTWATER FLOOD")
        bm.add_water(*self.DEEP_BASIN)

        # Submerged machinery hazard watches
        self.watch_zone(self.FORKLIFT_1, lambda: self._touch_submerged("Submerged forklift chassis snagged you!"))
        self.watch_zone(self.FORKLIFT_2, lambda: self._touch_submerged("Exposed battery terminals shocked in saltwater!"))

        # Depots & Lighthouse safe zone
        bm.add_building("warehouse", "DEPOT 1", 60, 50, 100, 80)
        bm.add_building("warehouse", "DEPOT 2", 190, 50, 105, 80)
        bm.add_building("shelter", "LIGHTHOUSE", 460, 40, 120, 95)
        bm.add_safe_zone(*self.LIGHTHOUSE_ZONE, label="LIGHTHOUSE TOWER", trigger_id="lighthouse_safe")

        # Breaker panel on Depot 1 dry platform
        self.add_interactable(
            "breaker", "CIRCUIT BREAKER",
            (self.BREAKER_POS[0] - 8, self.BREAKER_POS[1] - 8, 16, 16),
            (210, 190, 60),
            on_interact=self._interact_breaker,
        )

        # Radio bench on Depot 2 platform
        self.add_interactable(
            "radio_bench", "VHF TRANSCEIVER",
            (self.RADIO_BENCH[0] - 8, self.RADIO_BENCH[1] - 8, 16, 16),
            (60, 140, 210),
            on_interact=self._interact_radio,
        )

        # Pickups
        self.add_pickup("drybag", "DRY BAG", self.DRYBAG_POS, "drybag")
        self.add_pickup("battery", "SPARE BATTERY", self.BATTERY_POS, "battery")
        self.add_pickup("flashlight", "WATERPROOF TORCH", self.FLASHLIGHT_POS, "flashlight")

        # NPCs
        self.add_npc(
            "rico_dela_cruz",
            "Rico dela Cruz",
            self.RICO_POS,
            [
                "The storm surge breached the seawall! Saltwater is creeping onto the loading docks!",
                "Our marine VHF transceiver is our only lifeline to the Coast Guard cutters!",
                "Don't pull the live cord in wet conditions! We must isolate power safely first!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazard Interactions & Setbacks
    # ------------------------------------------------------------------
    def _touch_submerged(self, reason: str):
        if not self.is_busy():
            self.hurt(reason, penalty=5.0, respawn=True)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Rico dela Cruz" or self.is_busy():
            return

        if not self._breaker_off:
            # First interaction: ask safe electrical disconnect decision
            self.start_dialogue(
                "Rico dela Cruz",
                [
                    "Watch out! The radio power cable is dipping straight into the puddle!",
                    "Conductive saltwater makes touching live lines lethal. What should we do?",
                ],
            )
            self.ask(
                decision_id="radio_salvage_choice",
                prompt="The radio is plugged into a flooded wall outlet. How do you safely disconnect it?",
                options=[
                    {
                        "text": "Shut off the master circuit breaker from the dry panel before touching the plug",
                        "safe": True,
                        "lesson": "Isolating electricity upstream prevents electrocution in conductive saltwater.",
                    },
                    {
                        "text": "Yank the live cord directly out of the water with wet hands",
                        "safe": False,
                        "lesson": "Saltwater is highly conductive; pulling live cables in water is fatal.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Touching live cords in saltwater is lethal. Isolate upstream power!",
            )
        elif not self._radio_tuned:
            self.start_dialogue(
                "Rico dela Cruz",
                [
                    "Power is cut! Now seal the transceiver in the dry bag and calibrate Channel 16!",
                    "Interact with the bench right beside me to lock in the emergency frequency.",
                ],
            )
        else:
            self.start_dialogue(
                "Rico dela Cruz",
                [
                    "Distress call broadcast confirmed! Carry the sealed unit to the Lighthouse Tower!",
                    "Keep above the surge line—head up the concrete stairs immediately!",
                ],
            )

    def _on_decision_safe(self):
        if not self._rico_assisted:
            self._rico_assisted = True
            self.score_system.assist_resident("Rico dela Cruz")
            self.record_score("warnings_followed", 1)

        self.show_hint("Head to the yellow breaker switch on Depot 1 platform to kill the power!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Breaker & Radio Tuning
    # ------------------------------------------------------------------
    def _interact_breaker(self):
        if self._breaker_off:
            self.show_hint("Master breaker already isolated. Power is safely cut.", 2.5)
            return

        if not self._rico_assisted:
            self.show_hint("Consult with Rico dela Cruz at Depot 2 before switching master feeds.", 3.5)
            return

        self.start_minigame(
            TimingMeter(
                title="ISOLATE MASTER BREAKER",
                hint="Flip breaker while contacts are clear of arcing moisture",
                rounds=2,
                speed=1.0,
                zone=0.25,
                steps=["Open dry disconnect cover", "Throw master knife switch"],
                win_text="BREAKER OPEN - POWER ISOLATED!",
                fail_text="SWITCH ARCS! RETRY",
                icon="generator",
            ),
            on_win=self._breaker_success,
            on_fail=lambda: self.show_hint("Breaker slipped. Re-align and throw cleanly.", 3.0),
        )

    def _breaker_success(self):
        self._breaker_off = True
        self.set_checkpoint(self.RADIO_BENCH)
        self.show_hint("Power safely killed! Interact with the radio bench to pack and tune VHF Ch 16.", 5.0)

    def _interact_radio(self):
        if not self._breaker_off:
            self.show_hint("DANGER: Outlet is still live! Shut off the breaker panel first.", 3.5)
            return

        if self._radio_tuned:
            self.show_hint("Radio locked to VHF Ch 16. Carry it to the Lighthouse Tower!", 3.0)
            return

        self.start_minigame(
            RadioTuning(
                title="DISTRESS FREQUENCY LOCK",
                target_channel="VHF CH 16 (156.8 MHz)",
                speed=1.1,
                zone=0.22,
                rounds=2,
                win_text="CH 16 LOCKED - BEACON READY!",
                fail_text="STATIC - RETUNE DIAL",
            ),
            on_win=self._radio_success,
            on_fail=lambda: self.show_hint("Signal lost in storm noise. Retune frequency dial.", 3.0),
        )

    def _radio_success(self):
        self._radio_tuned = True
        self._radio_packed = True
        self.record_score("supplies_secured", 1)
        self.show_hint("Radio secure and broadcasting! Flee up to the Lighthouse Tower!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation & Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "lighthouse_safe" and not self.completed:
            if not self._radio_tuned:
                self.show_hint("You cannot evacuate without securing the VHF emergency transceiver!", 3.5)
                return

            self.score_system.complete_evacuation("ch3_3")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visual Rendering
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.rain.update(dt)
        self.lightning.update(dt)

        # Gradual surge rise simulation
        self._surge_level = min(0.85, 0.25 + (self.level_time / 160.0) * 0.6)
        self.set_meter("surge", "SALT SURGE", self._surge_level, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # 1. Main saltwater flood across alleyway with depth & foam shoreline
        flood_screen = self.camera.apply(pygame.Rect(self.FLOOD_LANE))
        draw_water(surface, flood_screen, self._anim_t, alpha=115, color=(35, 95, 160), foam=True, depth=True)

        # 2. Deep harbor basin water
        deep_screen = self.camera.apply(pygame.Rect(self.DEEP_BASIN))
        draw_water(surface, deep_screen, self._anim_t, alpha=140, color=(20, 60, 120), foam=True, depth=True)

        # 3. Submerged forklift obstacles (rusty iron pixel blocks under water)
        for fk_rect in (self.FORKLIFT_1, self.FORKLIFT_2):
            s_fk = self.camera.apply(pygame.Rect(fk_rect))
            pygame.draw.rect(surface, (70, 75, 82), s_fk)
            pygame.draw.rect(surface, (140, 85, 45), s_fk, 1)  # rust edges
            # Water ripples washing over submerged chassis
            draw_water(surface, s_fk, self._anim_t, alpha=65, color=(40, 110, 180))

        # 4. Player wading ripples when walking in the flood lane
        if self.player.rect.colliderect(pygame.Rect(self.FLOOD_LANE)):
            draw_wading_ripples(surface, self.camera, self.player.rect, self._anim_t)

    def draw_over_world(self, surface: pygame.Surface):
        # Draw weather atmospheric overlays
        self.rain.draw(surface)
        self.vignette.draw(surface, strength=0.20 + 0.50 * self._surge_level)
        self.lightning.draw(surface)
