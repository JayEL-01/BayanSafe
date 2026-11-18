"""Chapter 4 - Level 2: Canal Breach & Escalating Inundation (North East Plains).

Location: Plains Irrigation Canal Network.
Disaster: Flash Flood to Severe Flooding (Canal Dike Collapse).
Objectives: Navigate rising plains water, rescue stranded farming family, reach Grain Terminal.

Pixel-game layer:
  * Pickups: WALKING STICK, WATERPROOF TARP, FIRST AID KIT.
  * Mini-games: Road Crown Probing (TimingMeter), Elevate Grain Harvest (Mash).
  * Pressure: Rising flood depth meter, submerged ditch drop-offs, hidden culvert setbacks.
  * Realistic water rendering: layered agricultural floodwater, shoreline foam, wading ripples.
"""

from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    TimingMeter,
    Mash,
    draw_water,
    draw_wading_ripples,
)
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import (
    COLOR_GROUND_PLAINS,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class SilentPlainsFloodingHazard(SevereFloodingHazard):
    """Custom hazard logic without duplicate flat drawing, allowing custom
    multi-layered realistic floodwater and wading ripples."""

    def draw_effects(self, surface, camera):
        pass


class Chapter4Level2FlashFlood(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    ROAD_LANE = (30, 160, 580, 40)
    CANAL_BREACH = (150, 0, 60, 360)
    SURGE_ZONE = (180, 160, 220, 40)
    DITCH_HAZARD_1 = (210, 185, 45, 20)
    DITCH_HAZARD_2 = (330, 185, 45, 20)
    ROSA_POS = (115, 140)
    HARVEST_RACK_POS = (240, 140)
    TERMINAL_ZONE = (460, 50, 120, 80)

    # Pickups
    STICK_POS = (85, 215)
    TARP_POS = (145, 135)
    FIRSTAID_POS = (285, 135)

    FLOOD_PEAK_TIME = 120.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_2_flash_flood",
            title="Chapter 4 - Level 2: The Dike Breaks",
            subtitle="North East Plains - Severe Agricultural Inundation",
            disaster_type="Canal Breach / Severe Flooding",
            lesson_source="National Irrigation Administration (NIA) & NDRRMC Dam & Dike Safety Advisory",
            lesson_text=(
                "When agricultural canals or river dikes fail, flat plains inundate with deceptive speed.\n"
                "Water depth can double in under five minutes as water spreads laterally across fields.\n"
                "Never drive or walk across flooded plains roads; obscured ditches and culverts are fatal.\n"
                "Evacuate perpendicularly away from the canal breach to natural ridge lines."
            ),
        )

        # Progress flags
        self._rosa_assisted: bool = False
        self._road_probed: bool = False
        self._harvest_saved: bool = False
        self._flood_level: float = 0.25

        # Visuals
        self.rain = ParticleField("rain", seed=9, count=32)
        self.vignette = Vignette(color=(20, 38, 45), max_alpha=155)

        # Build world & hazards
        self._build_world()
        self.hazards.append(SilentPlainsFloodingHazard(shallow_rects=[self.SURGE_ZONE], deep_rects=[self.CANAL_BREACH]))

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("flood", "CANAL FLOOD", 0.25, good_high=False)
        self.start_countdown(self.FLOOD_PEAK_TIME, "CREEK PEAK", on_expire=self._flood_peak)

        # Structured quest steps
        self.set_steps([
            {
                "text": "You evade the canal surge at the breach",
                "done": lambda: self._rosa_assisted,
                "hint": "Irrigation canal collapsed! Find Aling Rosa near the threshing barn.",
                "target": self.ROSA_POS,
            },
            {
                "text": "You probe the submerged causeway with a pole",
                "done": lambda: self._road_probed,
                "hint": "Grab the walking stick and probe the submerged road crown.",
                "target": (180, 175),
            },
            {
                "text": "Aling Rosa lifts grain sacks at the rack",
                "done": lambda: self._harvest_saved,
                "hint": "Interact with the harvest storage rack to hoist community rice sacks.",
                "target": self.HARVEST_RACK_POS,
            },
            {
                "text": "You evacuate to the Grain Terminal",
                "done": lambda: self.completed,
                "hint": "Cross causeway to the concrete Grain Terminal on high ground!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Canal dike ruptured! Obscured roadside ditches are extremely dangerous.", 5.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Plains Irrigation Breach", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Breached canal water spreading across road
        bm.add_water(*self.CANAL_BREACH)
        bm.add_road(*self.ROAD_LANE)
        # Road causeway over the breach
        bm.add_bridge(150, 160, 60, 40)
        bm.add_hazard_zone("flood", *self.SURGE_ZONE, label="CANAL SURGE")

        # Submerged ditch drop-off watches
        self.watch_zone(self.DITCH_HAZARD_1, lambda: self._touch_ditch("Stepped into deep submerged irrigation ditch!"))
        self.watch_zone(self.DITCH_HAZARD_2, lambda: self._touch_ditch("Submerged culvert drop-off pulled you down!"))

        # Buildings
        bm.add_building("house", "THRESHING BARN", 60, 60, 90, 70)
        bm.add_building("shelter", "GRAIN TERMINAL", 460, 50, 120, 80)
        bm.add_safe_zone(*self.TERMINAL_ZONE, label="GRAIN TERMINAL", trigger_id="terminal_safe")

        # Interactables
        self.add_interactable(
            "road_probe", "SUBMERGED CROWN",
            (175, 168, 16, 16),
            (180, 160, 80),
            on_interact=self._interact_probe,
        )

        self.add_interactable(
            "harvest_rack", "GRAIN SACK RACK",
            (self.HARVEST_RACK_POS[0] - 8, self.HARVEST_RACK_POS[1] - 8, 16, 16),
            (210, 170, 70),
            on_interact=self._interact_harvest,
        )

        # Pickups
        self.add_pickup("stick", "WALKING STICK", self.STICK_POS, "stick")
        self.add_pickup("tarp", "WATERPROOF TARP", self.TARP_POS, "drybag")
        self.add_pickup("firstaid", "FIRST AID KIT", self.FIRSTAID_POS, "firstaid")

        # NPCs
        self.add_npc(
            "aling_rosa",
            "Aling Rosa",
            self.ROSA_POS,
            [
                "The earthen wall collapsed with a loud splash! The entire paddy is underwater!",
                "The current is washing away our harvest sacks and our boots are sinking in mud!",
                "Lead us toward the concrete Grain Terminal! Its foundation is built five meters above the plain!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_ditch(self, msg: str):
        if not self.is_busy():
            self.hurt(msg, penalty=4.0, respawn=True)

    def _flood_peak(self):
        self.hurt("The canal surge swept across the road! Recover immediately!", penalty=6.0, respawn=True)
        self.start_countdown(50.0, "SURGE WAVE", on_expire=self._flood_peak)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Aling Rosa" or self.is_busy():
            return

        if not self._rosa_assisted:
            self.start_dialogue(
                "Aling Rosa",
                [
                    "Look at the road ahead—knee-deep muddy water completely hides the drainage ditches!",
                    "If we slip into the deep canal cuts, we'll be trapped under the current! How should we cross?",
                ],
            )
            self.ask(
                decision_id="plains_flood_evac_choice",
                prompt="The road ahead is covered in knee-deep water. Ditches are completely submerged. How do you proceed?",
                options=[
                    {
                        "text": "Use a bamboo pole to feel for the road edges and stay strictly on the center crown",
                        "safe": True,
                        "lesson": "Probing ahead with a staff detects hidden submerged irrigation canal drop-offs.",
                    },
                    {
                        "text": "Wade blindly into the murky water hoping the ditch is elsewhere",
                        "safe": False,
                        "lesson": "Submerged drainage ditches can be two meters deep, causing immediate drowning.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never wade blindly into floodwater! Probe the submerged edges with a staff.",
            )
        elif not self._road_probed:
            self.start_dialogue(
                "Aling Rosa",
                [
                    "Grab the walking stick and probe the submerged crown ahead before we step forward!",
                ],
            )
        elif not self._harvest_saved:
            self.start_dialogue(
                "Aling Rosa",
                [
                    "The causeway path is clear! Now help me hoist the seed grain onto the elevated rack!",
                ],
            )
        else:
            self.start_dialogue(
                "Aling Rosa",
                [
                    "The seed harvest is safe! Lead the way to the elevated Grain Terminal!",
                ],
            )

    def _on_decision_safe(self):
        if not self._rosa_assisted:
            self._rosa_assisted = True
            self.score_system.assist_resident("Aling Rosa")
            self.record_score("warnings_followed", 1)

        self.show_hint("Pick up the WALKING STICK and probe the submerged causeway crown!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Road Probing & Harvest Hoist
    # ------------------------------------------------------------------
    def _interact_probe(self):
        if not self._rosa_assisted:
            self.show_hint("Consult with Aling Rosa before crossing the breach zone.", 3.0)
            return

        if self._road_probed:
            self.show_hint("Safe road crown probed and marked with warning poles.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="PROBE ROAD EDGES",
                hint="Tap pole into mud to locate hidden irrigation ditch drops",
                rounds=3,
                speed=1.05,
                zone=0.24,
                steps=["Probe left ditch boundary", "Detect submerged culvert", "Mark solid center crown"],
                win_text="SAFE ROAD CROWN IDENTIFIED!",
                fail_text="SLIPPED OFF EDGE! RETRY",
                icon="stick",
            ),
            on_win=self._probe_success,
            on_fail=lambda: self.show_hint("Staff sank into deep mud off the road. Stay centered!", 3.0),
        )

    def _probe_success(self):
        self._road_probed = True
        self.set_checkpoint((180, 175))
        self.show_hint("Crown marked! Now hoist the harvest sacks at the grain rack!", 5.0)

    def _interact_harvest(self):
        if not self._road_probed:
            self.show_hint("Verify the safe crossing path before loading supplies.", 3.5)
            return

        if self._harvest_saved:
            self.show_hint("Grain sacks safely secured onto high timber racks.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="ELEVATE GRAIN RESERVES",
                hint="Mash SPACE to hoist heavy rice seed sacks onto high racks!",
                target=15,
                decay=2.2,
                time_limit=8.0,
                icon="gobag",
                win_text="HARVEST SECURED ABOVE WATER!",
                fail_text="SACK SLIPPED IN WATER! RETRY",
            ),
            on_win=self._harvest_success,
            on_fail=lambda: self.show_hint("Sack was too heavy. Lift with steady leg power!", 3.0),
        )

    def _harvest_success(self):
        self._harvest_saved = True
        self.set_checkpoint(self.HARVEST_RACK_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Grain reserves saved! Evacuate all families to the GRAIN TERMINAL!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "terminal_safe" and not self.completed:
            if not self._harvest_saved:
                self.show_hint("Probe the road and secure the grain sacks before sheltering!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch4_2")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.rain.update(dt)

        self._flood_level = min(0.85, 0.25 + (self.level_time / 130.0) * 0.60)
        self.set_meter("flood", "CANAL FLOOD", self._flood_level, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Breached canal channel
        canal_screen = self.camera.apply(pygame.Rect(self.CANAL_BREACH))
        draw_water(surface, canal_screen, self._anim_t, alpha=135, color=(35, 90, 150), foam=True, depth=True)

        # Surging road flood
        surge_screen = self.camera.apply(pygame.Rect(self.SURGE_ZONE))
        draw_water(surface, surge_screen, self._anim_t, alpha=105, color=(45, 105, 165), foam=True)

        # Submerged ditches
        for ditch in (self.DITCH_HAZARD_1, self.DITCH_HAZARD_2):
            s_ditch = self.camera.apply(pygame.Rect(ditch))
            pygame.draw.rect(surface, (25, 45, 65), s_ditch)
            draw_water(surface, s_ditch, self._anim_t, alpha=80, color=(20, 50, 90))

        if self.player.rect.colliderect(pygame.Rect(self.SURGE_ZONE)):
            draw_wading_ripples(surface, self.camera, self.player.rect, self._anim_t)

    def draw_over_world(self, surface: pygame.Surface):
        self.rain.draw(surface)
        self.vignette.draw(surface, strength=0.20 + 0.50 * self._flood_level)
