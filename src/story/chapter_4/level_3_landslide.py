"""Chapter 4 - Level 3: Uncovering the Subterranean Truth (North East Plains).

Location: Plains Foothills & Excavation Trench.
Disaster: Rain-Induced Slope Failure & Infrastructure Exposure.
Objectives: Avoid landslide scar, investigate exposed conduit, confer with Dr. Elena Reyes.

Pixel-game layer:
  * Pickups: TELEMETRY LOGGER, DIGITAL MULTIMETER, INDUSTRIAL HARDHAT.
  * Mini-games: Unstable Scree Crossing (TimingMeter), Aegis Telemetry Decoupler (RadioTuning).
  * Pressure: Mudslide slope instability meter, arcing high-voltage waveguide setbacks.
  * Atmosphere: Rain-saturated slope, falling scree, flashing electrical arcs.
"""

from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    TimingMeter,
    RadioTuning,
)
from src.maps.block_map import BlockMap
from src.hazards.landslide import LandslideHazard
from src.config.palette import (
    COLOR_GROUND_PLAINS,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class Chapter4Level3Landslide(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    FOOTHILL_TRAIL = (30, 160, 580, 36)
    SLIDE_SCAR = (170, 150, 110, 60)
    EXPOSED_CONDUIT_POS = (310, 135)
    SEISMO_POST_ZONE = (470, 50, 110, 75)
    REYES_POS = (420, 140)

    # Pickups
    LOGGER_POS = (95, 135)
    MULTIMETER_POS = (245, 135)
    HARDHAT_POS = (370, 135)

    SLOPE_SECONDS = 135.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_3_landslide",
            title="Chapter 4 - Level 3: The Exposed Arteries",
            subtitle="Plains Foothills - Conduit Discovery & Slope Failure",
            disaster_type="Slope Failure & Industrial Conduit Rupture",
            lesson_source="DENR Environmental Management Bureau (EMB) & MGB Underground Mining / Tunneling Safety",
            lesson_text=(
                "Unregulated subterranean excavation and geothermal tunneling severely destabilize surface slopes.\n"
                "When earth failures expose high-voltage industrial cables or pressurized pipelines,\n"
                "maintain a minimum 50-meter safety cordon; arc flash and gas explosion hazards are extreme.\n"
                "Scientific field teams must cross-reference seismic sensor arrays with geological fault maps."
            ),
        )

        # Progress flags
        self._reyes_assisted: bool = False
        self._scree_crossed: bool = False
        self._telemetry_decoded: bool = False
        self._slope_instability: float = 0.20

        # Effects
        self.rain = ParticleField("rain", seed=12, count=30)
        self.scree = ParticleField("smoke", seed=4, count=14)
        self.vignette = Vignette(color=(35, 30, 25), max_alpha=150)

        # Build world & hazards
        self._build_world()
        self.hazards.append(LandslideHazard())

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("slope", "SLOPE SHIFT", 0.20, good_high=False)
        self.start_countdown(self.SLOPE_SECONDS, "SLOPE RUMBLE", on_expire=self._slope_rumble)

        # Structured quest steps
        self.set_steps([
            {
                "text": "You pass the landslide scar on the trail",
                "done": lambda: self._scree_crossed,
                "hint": "Rain loosened the hillside scree. Tread carefully past the mud scar.",
                "target": (170, 168),
            },
            {
                "text": "You examine the Aegis conduit at the site",
                "done": lambda: self._telemetry_decoded,
                "hint": "Inspect the severed industrial conduit and decode the telemetry link.",
                "target": self.EXPOSED_CONDUIT_POS,
            },
            {
                "text": "Confer with Dr. Elena Reyes at the seismo van",
                "done": lambda: self._reyes_assisted,
                "hint": "Report telemetry serial findings to Dr. Elena Reyes.",
                "target": self.REYES_POS,
            },
            {
                "text": "Muster with Dr. Reyes at the Mobile Van",
                "done": lambda: self.completed,
                "hint": "Enter the Mobile Seismo Van safe zone to finalize analysis!",
                "target": (525, 85),
            },
        ])

        self.show_hint("Fresh slope failure uncovered strange industrial cables in the mud!", 5.0)

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Plains Foothills Excavation", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Foothill trail
        bm.add_path(*self.FOOTHILL_TRAIL)

        # Landslide debris scar
        bm.add_hazard_zone("landslide", *self.SLIDE_SCAR, label="HILLSIDE SLIDE")
        self.watch_zone(self.SLIDE_SCAR, self._touch_slide)

        # Exposed facility conduit structure
        bm.add_building("research", "AEGIS CONDUIT", 290, 60, 85, 65, trigger_id="conduit_found")
        bm.add_building("clinic", "MOBILE SEISMO VAN", 470, 50, 110, 75)
        bm.add_safe_zone(*self.SEISMO_POST_ZONE, label="SEISMO POST", trigger_id="seismo_safe")

        # Interactables
        self.add_interactable(
            "scree_path", "UNSTABLE SCREE",
            (165, 160, 20, 20),
            (150, 120, 80),
            on_interact=self._interact_scree,
        )

        self.add_interactable(
            "conduit_terminal", "EXPOSED CONDUIT",
            (self.EXPOSED_CONDUIT_POS[0] - 8, self.EXPOSED_CONDUIT_POS[1] - 8, 16, 16),
            (60, 160, 220),
            on_interact=self._interact_conduit,
        )

        # Pickups
        self.add_pickup("logger", "DATA LOG", self.LOGGER_POS, "flashlight")
        self.add_pickup("multimeter", "MULTIMETER", self.MULTIMETER_POS, "battery")
        self.add_pickup("hardhat", "HEAVY HARDHAT", self.HARDHAT_POS, "hardhat")

        # NPCs
        self.add_npc(
            "dr_elena_reyes",
            "Dr. Elena Reyes",
            self.REYES_POS,
            [
                "Look closely at those sheared wires! Those aren't public utility cables!",
                "They are military-grade pulse waveguides routing gigawatts directly into Volcano Valley!",
                "Our PHIVOLCS seismographs didn't record a natural fault rupture—it was artificially triggered!",
                "Dr. Voss is operating an uncalibrated tectonic resonance generator inside the caldera!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_slide(self):
        if not self._scree_crossed and not self.is_busy():
            self.hurt("Loose mudslide rubble gave way beneath your feet!", penalty=4.0, respawn=True)

    def _slope_rumble(self):
        self.hurt("Hillside scree shifted! Watch for falling mud and rocks!", penalty=6.0, respawn=True)
        self.start_countdown(50.0, "SLOPE RUMBLE", on_expire=self._slope_rumble)

    # ------------------------------------------------------------------
    # Mini-games: Scree Crossing & Telemetry Decoupler
    # ------------------------------------------------------------------
    def _interact_scree(self):
        if self._scree_crossed:
            self.show_hint("Foothill scree path stabilized with stepping stakes.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="CROSS UNSTABLE SCREE",
                hint="Step across firm rocks to avoid triggering a fresh mudslide",
                rounds=2,
                speed=1.0,
                zone=0.25,
                steps=["Test rock firmness with foot", "Hop to solid basalt ledge"],
                win_text="SCREE TRAVERSED SAFELY!",
                fail_text="LOOSE MUD GAVE WAY! RETRY",
                icon="stick",
            ),
            on_win=self._scree_success,
            on_fail=lambda: self.show_hint("Gravel slid down slope. Plant your feet with care!", 3.0),
        )

    def _scree_success(self):
        self._scree_crossed = True
        self.set_checkpoint((220, 168))
        self.show_hint("Scree crossed! Now examine the exposed AEGIS CONDUIT ahead.", 5.0)

    def _interact_conduit(self):
        if not self._scree_crossed:
            self.show_hint("Navigate past the landslide scar first.", 3.0)
            return

        if self._telemetry_decoded:
            self.show_hint("Telemetry downloaded: pulse waveguides confirm artificial fault excitation.", 3.0)
            return

        self.start_minigame(
            RadioTuning(
                title="DECODE AEGIS TELEMETRY",
                target_channel="WAVEGUIDE CARRIER (433.9 MHz)",
                speed=1.1,
                zone=0.22,
                rounds=2,
                win_text="TELEMETRY SECURED - GIGAWATT ROUTING CONFIRMED!",
                fail_text="SIGNAL CORRUPTED! RETRY",
            ),
            on_win=self._conduit_success,
            on_fail=lambda: self.show_hint("Arc flash static jammed download. Retune carrier frequency.", 3.0),
        )

    def _conduit_success(self):
        self._telemetry_decoded = True
        self.set_checkpoint(self.EXPOSED_CONDUIT_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Telemetry carrier decoded! Confer with Dr. Elena Reyes at the seismo van.", 5.0)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Dr. Elena Reyes" or self.is_busy():
            return

        if not self._reyes_assisted:
            self.start_dialogue(
                "Dr. Elena Reyes",
                [
                    "Sparks crackle from the severed waveguides! The insulation is stripped by the slide!",
                    "How should we record the serial numbers and telemetry data without taking lethal shock?",
                ],
            )
            self.ask(
                decision_id="conduit_investigation_choice",
                prompt="Sparks crackle from the torn conduit cables. How do you gather evidence?",
                options=[
                    {
                        "text": "Photograph the telemetry serial numbers from a safe distance without touching wires",
                        "safe": True,
                        "lesson": "Preserving standoff distance prevents fatal electrical arc flash injuries.",
                    },
                    {
                        "text": "Grab the severed high-voltage cables to pull them out of the mud",
                        "safe": False,
                        "lesson": "Industrial high-voltage cables carry thousands of volts that cause instant electrocution.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never touch severed industrial conduits! Maintain safe standoff distance.",
            )
        else:
            self.start_dialogue(
                "Dr. Elena Reyes",
                [
                    "Our readings leave no doubt: Dr. Voss has pushed his machine beyond safety limits!",
                    "Enter the Mobile Seismo Van to transmit the emergency data to PHIVOLCS!",
                ],
            )

    def _on_decision_safe(self):
        if not self._reyes_assisted:
            self._reyes_assisted = True
            self.score_system.assist_resident("Dr. Elena Reyes")
            self.record_score("warnings_followed", 1)

        self.show_hint("Standoff analysis recorded! Proceed to the MOBILE SEISMO VAN!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "seismo_safe" and not self.completed:
            if not self._telemetry_decoded or not self._reyes_assisted:
                self.show_hint("Investigate the conduit and confer with Dr. Reyes before concluding analysis!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch4_3")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.rain.update(dt)
        self.scree.update(dt)

        self._slope_instability = min(0.85, 0.20 + (self.level_time / 140.0) * 0.65)
        self.set_meter("slope", "SLOPE SHIFT", self._slope_instability, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Mudslide scar patch
        scar_screen = self.camera.apply(pygame.Rect(self.SLIDE_SCAR))
        pygame.draw.rect(surface, (115, 80, 50), scar_screen)
        pygame.draw.rect(surface, (85, 55, 30), scar_screen, 2)

        # Conduit glowing waveguides
        c_screen = self.camera.apply(pygame.Rect(self.EXPOSED_CONDUIT_POS[0] - 12, self.EXPOSED_CONDUIT_POS[1] - 8, 24, 16))
        pygame.draw.rect(surface, (45, 50, 60), c_screen)
        # Flickering blue electrical energy
        if int(self._anim_t * 8) % 2 == 0:
            pygame.draw.rect(surface, (100, 200, 255), (c_screen.x + 4, c_screen.y + 6, 16, 3))

    def draw_over_world(self, surface: pygame.Surface):
        self.rain.draw(surface)
        self.scree.draw(surface)
        self.vignette.draw(surface, strength=0.20 + 0.45 * self._slope_instability)
