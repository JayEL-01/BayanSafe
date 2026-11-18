"""Chapter 5 - Level 4: Lahar Mudflow & Typhoon Landfall (Volcano Valley).

Location: Valley River Chasm & Flood Drainage.
Disaster: Compound Catastrophe: Typhoon Rains + Volcanic Ash = Torrential Lahar.
Objectives: Escape the roaring lahar channel, sound river basin evacuation siren with Mayor Cruz.

Pixel-game layer:
  * Pickups: ACOUSTIC SIREN KEY, EMERGENCY RADIO, CLIMBING HARNESS.
  * Mini-games: Sound River Basin Siren (TimingMeter), Canyon Wall Ridge Climb (Mash).
  * Pressure: Lahar crest surge countdown & meter, dense volcanic mud, flash river channel setbacks.
  * Realistic water/lahar rendering: churning gray-brown volcanic mudflow, foam edges, perpendicular evacuation path.
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
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import (
    COLOR_GROUND_VALLEY,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class SilentLaharHazard(SevereFloodingHazard):
    """Custom wrapper for lahar mudflow hazard logic without flat block drawing,
    allowing custom dense turbulent mud rendering."""

    def draw_effects(self, surface, camera):
        pass


class Chapter5Level4TyphoonSevereFlood(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    ROAD_LANE = (30, 160, 580, 40)
    LAHAR_CHASM = (160, 0, 90, 360)
    LAHAR_SURGE_ZONE = (140, 160, 130, 40)
    ASCENT_PATH = (300, 40, 40, 260)
    SIREN_POS = (360, 135)
    STAIRS_POS = (300, 150)
    RIDGE_SAFE_ZONE = (460, 50, 120, 80)
    MAYOR_POS = (360, 135)

    # Pickups
    SIREN_KEY_POS = (85, 135)
    RADIO_POS = (125, 215)
    HARNESS_POS = (245, 135)

    LAHAR_SECONDS = 110.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_4_typhoon_severe_flood",
            title="Chapter 5 - Level 4: The Concrete Flood (Lahar)",
            subtitle="Valley Chasm - Typhoon Landfall over Volcanic Ash",
            disaster_type="Lahar Mudflow & Severe Typhoon Flooding",
            lesson_source="DOST-PHIVOLCS Lahar Warning Protocols & Historical Lessons from Mt. Pinatubo (1991)",
            lesson_text=(
                "When heavy typhoon rains fall on loose volcanic pyroclastic deposits,\n"
                "millions of tons of boiling mud, ash, and boulders mobilize into LAHAR.\n"
                "Lahar travels at 30-60 km/h and has the density of wet concrete, burying bridges and homes.\n"
                "Never cross a lahar river channel; evacuate perpendicularly up valley canyon ridges immediately!"
            ),
        )

        # Progress flags
        self._mayor_assisted: bool = False
        self._siren_sounded: bool = False
        self._ridge_climbed: bool = False
        self._lahar_progress: float = 0.25

        # Visuals
        self.rain = ParticleField("rain", seed=31, count=40)
        self.lightning = LightningFlash()
        self.vignette = Vignette(color=(35, 30, 22), max_alpha=170)

        # Build world & hazards
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=4))
        self.hazards.append(SilentLaharHazard(shallow_rects=[self.LAHAR_SURGE_ZONE], deep_rects=[self.LAHAR_CHASM]))

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("lahar", "LAHAR CREST", 0.25, good_high=False)
        self.start_countdown(self.LAHAR_SECONDS, "LAHAR ARRIVAL", on_expire=self._lahar_arrival)

        # Structured quest steps
        self.set_steps([
            {
                "text": "Cross the river bridge to Mayor Cruz",
                "done": lambda: self._mayor_assisted,
                "hint": "Typhoon deluge mobilizing ash into boiling mud! Cross the bridge to Mayor Cruz.",
                "target": self.MAYOR_POS,
            },
            {
                "text": "Sound the sirens with Mayor Cruz at the shed",
                "done": lambda: self._siren_sounded,
                "hint": "Use the acoustic siren key at the River Gauge Station console.",
                "target": self.SIREN_POS,
            },
            {
                "text": "Climb the ridge stairs above the chasm",
                "done": lambda: self._ridge_climbed,
                "hint": "Power sprint up the canyon wall stairs to escape the rising mud line!",
                "target": self.STAIRS_POS,
            },
            {
                "text": "Reach the High Substation on the ridge",
                "done": lambda: self.completed,
                "hint": "Muster at the elevated HIGH SUBSTATION above the flood line!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Heavy typhoon rain over volcanic ash deposits! Lahar mudflow cresting upstream!", 5.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Lahar River Chasm", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Deep lahar roaring channel
        bm.add_water(*self.LAHAR_CHASM)
        bm.add_road(*self.ROAD_LANE)
        # Road bridge over the chasm
        bm.add_bridge(160, 160, 90, 40)
        bm.add_hazard_zone("flood", *self.LAHAR_SURGE_ZONE, label="ROARING LAHAR")
        self.watch_zone(self.LAHAR_SURGE_ZONE, self._touch_lahar)

        # Canyon wall ascent path
        bm.add_road(*self.ASCENT_PATH)

        # Structures
        bm.add_building("house", "RIVER GAUGE SHED", 60, 60, 85, 60)
        bm.add_building("shelter", "HIGH SUBSTATION", 460, 50, 120, 80)
        bm.add_safe_zone(*self.RIDGE_SAFE_ZONE, label="HIGH RIDGE", trigger_id="ridge_safe")

        # Interactables
        self.add_interactable(
            "siren_console", "ACOUSTIC SIREN",
            (self.SIREN_POS[0] - 8, self.SIREN_POS[1] - 8, 16, 16),
            (220, 190, 50),
            on_interact=self._interact_siren,
        )

        self.add_interactable(
            "canyon_stairs", "CANYON RIDGE ASCENT",
            (self.STAIRS_POS[0] - 8, self.STAIRS_POS[1] - 8, 16, 16),
            (170, 160, 150),
            on_interact=self._interact_stairs,
        )

        # Pickups
        self.add_pickup("siren_key", "ACOUSTIC SIREN KEY", self.SIREN_KEY_POS, "stick")
        self.add_pickup("radio", "EMERGENCY RADIO", self.RADIO_POS, "radio")
        self.add_pickup("harness", "CLIMBING HARNESS", self.HARNESS_POS, "hardhat")

        # NPCs
        self.add_npc(
            "mayor_cruz",
            "Mayor Cruz",
            self.MAYOR_POS,
            [
                "The rain is washing the whole mountain slope into the river!",
                "The acoustic flow sensors upstream are registering a ten-meter wall of boiling lahar!",
                "Sound the emergency sirens for all lowland villages along the riverbanks!",
                "Anyone in the river basin must climb the mountain sides right this second!",
            ],
            role="official",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_lahar(self):
        if not self._ridge_climbed and not self.is_busy():
            self.hurt("Dense churning lahar mud swept your legs from under you! High density mud drags you down.", penalty=6.0, respawn=True)

    def _lahar_arrival(self):
        self.hurt("The roaring lahar wall smashed into the bridge piers! Evacuate perpendicularly immediately!", penalty=8.0, respawn=True)
        self.start_countdown(45.0, "LAHAR RE-CREST", on_expire=self._lahar_arrival)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Mayor Cruz" or self.is_busy():
            return

        if not self._mayor_assisted:
            self.start_dialogue(
                "Mayor Cruz",
                [
                    "A deafening roar echoes from upstream as boiling mud surges around the bridge piers!",
                    "A ten-meter wall of liquid concrete is rushing down the canyon! Which way do we run?",
                ],
            )
            self.ask(
                decision_id="lahar_escape_choice",
                prompt="A deafening roar echoes from upstream as boiling mud surges around the bridge piers. Which way do you run?",
                options=[
                    {
                        "text": "Evacuate perpendicularly UP the steep canyon slope away from the river bed",
                        "safe": True,
                        "lesson": "Climbing perpendicular to lahar channels reaches elevation above the mud crest.",
                    },
                    {
                        "text": "Run downstream along the riverbank path trying to outpace the mudflow on foot",
                        "safe": False,
                        "lesson": "Lahar flows at speeds exceeding 50 km/h; running downstream guarantees being engulfed.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never run downstream in front of a lahar flow! Evacuate perpendicularly UP the canyon slopes.",
            )
        elif not self._siren_sounded:
            self.start_dialogue(
                "Mayor Cruz",
                [
                    "Insert the siren key into the console right here to sound the valley-wide alert horn!",
                ],
            )
        elif not self._ridge_climbed:
            self.start_dialogue(
                "Mayor Cruz",
                [
                    "Lowland villages are warned! Now scramble up the canyon stairs to the High Substation!",
                ],
            )
        else:
            self.start_dialogue(
                "Mayor Cruz",
                [
                    "We're above the mud line! The entire island's fate rests on what lies in the core bunker ahead!",
                ],
            )

    def _on_decision_safe(self):
        if not self._mayor_assisted:
            self._mayor_assisted = True
            self.score_system.assist_resident("Mayor Cruz")
            self.record_score("warnings_followed", 1)

        self.show_hint("Interact with the ACOUSTIC SIREN console to trigger the regional warning!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Siren Trigger & Ridge Ascent
    # ------------------------------------------------------------------
    def _interact_siren(self):
        if not self._mayor_assisted:
            self.show_hint("Consult with Mayor Cruz before sounding municipal sirens.", 3.0)
            return

        if self._siren_sounded:
            self.show_hint("130-decibel lahar siren blasting across all lowland valleys.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="SOUND LAHAR SIREN",
                hint="Turn the primary key switch and depressurize horn manifold",
                rounds=2,
                speed=1.05,
                zone=0.24,
                steps=["Insert master acoustic key", "Depress pneumatic horn release"],
                win_text="VALLEY-WIDE LAHAR SIREN BLASTING!",
                fail_text="SIREN JAMMED! RETRY",
                icon="stick",
            ),
            on_win=self._siren_success,
            on_fail=lambda: self.show_hint("Key slipped in the vibrating console. Turn firmly!", 3.0),
        )

    def _siren_success(self):
        self._siren_sounded = True
        self.set_checkpoint(self.SIREN_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Sirens sounding! Sprint to the CANYON RIDGE ASCENT to climb the canyon wall!", 5.0)

    def _interact_stairs(self):
        if not self._siren_sounded:
            self.show_hint("Trigger the valley emergency sirens before evacuating!", 3.5)
            return

        if self._ridge_climbed:
            self.show_hint("You already scaled the canyon wall. Proceed to the High Substation.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="CLIMB CANYON RIDGE",
                hint="Mash SPACE to scramble up the steep vertical canyon stairs!",
                target=16,
                decay=2.5,
                time_limit=8.0,
                icon="hardhat",
                win_text="HIGH CANYON RIDGE REACHED!",
                fail_text="SLIPPED ON WET MUD! RETRY",
            ),
            on_win=self._stairs_success,
            on_fail=lambda: self.show_hint("Mud washed down the steps. Keep driving with your legs!", 3.0),
        )

    def _stairs_success(self):
        self._ridge_climbed = True
        self.set_checkpoint((320, 80))
        self.player.pos = pygame.Vector2(320, 80)
        self.player.rect.topleft = (320, 80)
        self.show_hint("You cleared the lahar inundation line! Enter the HIGH SUBSTATION shelter!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "ridge_safe" and not self.completed:
            if not self._ridge_climbed:
                self.show_hint("Climb the canyon wall stairs to escape the lahar path first!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch5_4")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.rain.update(dt)
        self.lightning.update(dt)

        self._lahar_progress = min(0.92, 0.25 + (self.level_time / 115.0) * 0.67)
        self.set_meter("lahar", "LAHAR CREST", self._lahar_progress, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Deep turbulent mudflow channel (gray-brown volcanic mud)
        lahar_screen = self.camera.apply(pygame.Rect(self.LAHAR_CHASM))
        draw_water(surface, lahar_screen, self._anim_t, alpha=150, color=(75, 60, 48), foam=True, depth=True)

        # Surging bridge lahar wash
        surge_screen = self.camera.apply(pygame.Rect(self.LAHAR_SURGE_ZONE))
        draw_water(surface, surge_screen, self._anim_t, alpha=115, color=(90, 72, 55), foam=True)

        if self.player.rect.colliderect(pygame.Rect(self.LAHAR_SURGE_ZONE)):
            draw_wading_ripples(surface, self.camera, self.player.rect, self._anim_t)

    def draw_over_world(self, surface: pygame.Surface):
        self.rain.draw(surface)
        self.lightning.draw(surface)
        self.vignette.draw(surface, strength=0.25 + 0.50 * self._lahar_progress)
