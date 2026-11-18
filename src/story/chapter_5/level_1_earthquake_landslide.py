"""Chapter 5 - Level 1: Caldera Tremors & Rockfalls (Volcano Valley).

Location: Volcano Valley Gorge & Access Highway.
Disaster: Strong Caldera Tremors (PEIS Intensity VII) & Rockfall Cascades.
Objectives: Navigate fissure chasms, locate stranded research convoy, reach Facility Gate.

Pixel-game layer:
  * Pickups: HEAVY PRYBAR, GEOLOGICAL COMPASS, REINFORCED BOOTS.
  * Mini-games: Lever Fallen Boulders (Mash), Basalt Fissure Crossing (TimingMeter).
  * Pressure: Caldera tremor shocks, falling rock cascades, superheated thermal fissure setbacks.
  * Atmosphere: Dark volcanic rock, glowing sulfur ground cracks, rumbling screen tremors.
"""

from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    TimingMeter,
    Mash,
    draw_cracks,
)
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.hazards.landslide import LandslideHazard
from src.config.palette import (
    COLOR_GROUND_VALLEY,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class Chapter5Level1EarthquakeLandslide(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    HIGHWAY_RECT = (30, 160, 580, 40)
    FISSURE_ZONE = (160, 150, 120, 60)
    BOULDER_POS = (190, 170)
    FISSURE_LEDGE_POS = (245, 170)
    GATE_ZONE = (460, 50, 120, 80)
    PAOLO_POS = (115, 140)

    # Pickups
    PRYBAR_POS = (80, 135)
    COMPASS_POS = (220, 135)
    BOOTS_POS = (360, 135)

    TREMOR_SECONDS = 110.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_1_earthquake_landslide",
            title="Chapter 5 - Level 1: The Splitting Caldera",
            subtitle="Volcano Valley - Caldera Ruptures & Rockfall",
            disaster_type="Volcanic Earthquake (Intensity VII) & Rockfall",
            lesson_source="DOST-PHIVOLCS Volcanic Seismicity & Caldera Fissure Safety Manual",
            lesson_text=(
                "Caldera earthquakes can rip open ground fissures several meters wide in seconds.\n"
                "Never cross active ground fissures; superheated volcanic gases and steam vent from below.\n"
                "In steep volcanic gorges, falling boulders travel at terminal velocity.\n"
                "Watch the upper canyon rims and seek shelter under solid overhangs or reinforced culverts."
            ),
        )

        # Progress flags
        self._paolo_assisted: bool = False
        self._boulder_cleared: bool = False
        self._fissure_crossed: bool = False
        self._seismic_rumble: float = 0.30

        # Visuals
        self.dust = ParticleField("smoke", seed=21, count=18)
        self.debris = ParticleField("embers", seed=13, count=16)
        self.vignette = Vignette(color=(40, 25, 20), max_alpha=160)

        # Build world & hazards
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=7))
        self.hazards.append(LandslideHazard())

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("seismic", "CALDERA SEISMIC", 0.30, good_high=False)
        self.start_countdown(self.TREMOR_SECONDS, "QUAKE CLIMAX", on_expire=self._quake_climax)

        # Structured quest steps
        self.set_steps([
            {
                "text": "Meet Engr. Paolo Santos at the gorge shed",
                "done": lambda: self._paolo_assisted,
                "hint": "Canyon road is breaking apart! Find Engr. Paolo Santos near the construction shed.",
                "target": self.PAOLO_POS,
            },
            {
                "text": "Clear basalt boulders from the gorge road",
                "done": lambda: self._boulder_cleared,
                "hint": "Grab the prybar and clear the fallen basalt obstruction.",
                "target": self.BOULDER_POS,
            },
            {
                "text": "Cross the basalt shoulder past the fissure",
                "done": lambda: self._fissure_crossed,
                "hint": "Cross along the solid basalt high shoulder avoiding superheated cracks.",
                "target": self.FISSURE_LEDGE_POS,
            },
            {
                "text": "Reach the Aegis-Terra gatehouse on the ridge",
                "done": lambda: self.completed,
                "hint": "Sprint to the fortified Aegis-Terra Gatehouse shelter!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Violent Intensity VII caldera tremors! Watch for falling rocks and ground fissures.", 5.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Volcano Valley Gorge", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Broken canyon highway
        bm.add_road(*self.HIGHWAY_RECT)

        # Deep ground fissure hazard
        bm.add_hazard_zone("landslide", *self.FISSURE_ZONE, label="CALDERA FISSURE")
        self.watch_zone(self.FISSURE_ZONE, self._touch_fissure)

        # Structures
        bm.add_building("house", "CONSTRUCTION SHED", 60, 60, 85, 60)
        bm.add_building("research", "AEGIS GATEHOUSE", 460, 50, 120, 80)
        bm.add_safe_zone(*self.GATE_ZONE, label="AEGIS GATE", trigger_id="gate_safe")

        # Interactables
        self.add_interactable(
            "boulder_rubble", "FALLEN BOULDER",
            (self.BOULDER_POS[0] - 8, self.BOULDER_POS[1] - 8, 16, 16),
            (110, 85, 60),
            on_interact=self._interact_boulder,
        )

        self.add_interactable(
            "fissure_ledge", "BASALT LEDGE",
            (self.FISSURE_LEDGE_POS[0] - 8, self.FISSURE_LEDGE_POS[1] - 8, 16, 16),
            (80, 75, 70),
            on_interact=self._interact_fissure,
        )

        # Pickups
        self.add_pickup("prybar", "HEAVY PRYBAR", self.PRYBAR_POS, "stick")
        self.add_pickup("compass", "GEOLOGICAL COMPASS", self.COMPASS_POS, "battery")
        self.add_pickup("boots", "REINFORCED BOOTS", self.BOOTS_POS, "hardhat")

        # NPCs
        self.add_npc(
            "engr_paolo_santos",
            "Engr. Paolo Santos",
            self.PAOLO_POS,
            [
                "The road ahead sheared vertically by almost two meters!",
                "Dr. Voss locked himself inside the subterranean command bunker and disabled remote access!",
                "He believes his resonance array can stabilize the magma chamber, but it's doing the opposite!",
                "It's hyper-charging the magma chamber like a shaken soda can! We have to breach the facility!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_fissure(self):
        if not self._fissure_crossed and not self.is_busy():
            self.hurt("Superheated thermal gases blasted from the cracked fissure!", penalty=5.0, respawn=True)

    def _quake_climax(self):
        self.hurt("Violent tectonic shockwave shook boulders loose from the canyon wall!", penalty=6.0, respawn=True)
        self.start_countdown(45.0, "QUAKE SHOCK", on_expire=self._quake_climax)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Engr. Paolo Santos" or self.is_busy():
            return

        if not self._paolo_assisted:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "A steaming fissure split the canyon road right down to thermal magma ducts!",
                    "Hot gases are venting. How do we bypass the chasm safely?",
                ],
            )
            self.ask(
                decision_id="fissure_crossing_choice",
                prompt="A gaping fissure vents superheated volcanic steam across the road. How do you bypass it?",
                options=[
                    {
                        "text": "Skirt around along the solid basalt outcrop on the high shoulder",
                        "safe": True,
                        "lesson": "Solid basalt rock supports weight safely while avoiding hot fissure gases.",
                    },
                    {
                        "text": "Try to jump directly over the smoking thermal crack where the soil looks crumbled",
                        "safe": False,
                        "lesson": "Crumbled soil around active fissures collapses under weight into superheated vents.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never jump over crumbling thermal cracks! Stick to solid basalt high shoulders.",
            )
        elif not self._boulder_cleared:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "Use the heavy steel prybar to heave that fallen boulder off the access path!",
                ],
            )
        elif not self._fissure_crossed:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "Path is open! Now traverse the narrow basalt high shoulder around the smoking vent!",
                ],
            )
        else:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "We're past the fissure! Hurry to the Aegis Gatehouse to override the perimeter locks!",
                ],
            )

    def _on_decision_safe(self):
        if not self._paolo_assisted:
            self._paolo_assisted = True
            self.score_system.assist_resident("Engr. Paolo Santos")
            self.record_score("warnings_followed", 1)

        self.show_hint("Pick up the PRYBAR and heave the fallen boulder off the road!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Boulder Lever & Ledge Crossing
    # ------------------------------------------------------------------
    def _interact_boulder(self):
        if not self._paolo_assisted:
            self.show_hint("Consult with Engr. Paolo Santos on safe routes first.", 3.0)
            return

        if self._boulder_cleared:
            self.show_hint("Boulder rolled down the gorge. Road is unobstructed.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="PRY FALLEN BOULDER",
                hint="Mash SPACE to lever the heavy basalt boulder into the gorge!",
                target=16,
                decay=2.4,
                time_limit=8.0,
                icon="stick",
                win_text="BOULDER TOPPLED INTO GORGE!",
                fail_text="PRYBAR SLIPPED! RETRY",
            ),
            on_win=self._boulder_success,
            on_fail=lambda: self.show_hint("Prybar slipped off the rock face. Wedge it deep and push!", 3.0),
        )

    def _boulder_success(self):
        self._boulder_cleared = True
        self.set_checkpoint(self.BOULDER_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Boulder cleared! Now traverse the BASALT LEDGE around the fissure!", 5.0)

    def _interact_fissure(self):
        if not self._boulder_cleared:
            self.show_hint("Clear the roadway boulder before attempting the narrow ledge.", 3.5)
            return

        if self._fissure_crossed:
            self.show_hint("Solid basalt ledge negotiated. Fissure safely bypassed.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="CROSS BASALT SHOULDER",
                hint="Balance along the solid basalt outcrop away from hot gases",
                rounds=3,
                speed=1.1,
                zone=0.23,
                steps=["Test basalt footholds", "Skirt superheated steam jet", "Reach firm eastern shoulder"],
                win_text="FISSURE BYPASSED SAFELY!",
                fail_text="STEAM BLAST FORCED YOU BACK! RETRY",
                icon="stick",
            ),
            on_win=self._fissure_success,
            on_fail=lambda: self.show_hint("Thermal gas blast blocked your footstep. Time your steps cleanly!", 3.0),
        )

    def _fissure_success(self):
        self._fissure_crossed = True
        self.set_checkpoint(self.FISSURE_LEDGE_POS)
        self.show_hint("Fissure crossed! Sprint to the AEGIS GATEHOUSE shelter!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "gate_safe" and not self.completed:
            if not self._fissure_crossed:
                self.show_hint("Bypass the fissure hazard before reaching the gatehouse!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch5_1")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.dust.update(dt)
        self.debris.update(dt)

        self._seismic_rumble = min(0.90, 0.30 + (self.level_time / 120.0) * 0.60)
        self.set_meter("seismic", "CALDERA SEISMIC", self._seismic_rumble, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Smoking fissure
        fissure_screen = self.camera.apply(pygame.Rect(self.FISSURE_ZONE))
        pygame.draw.rect(surface, (45, 30, 25), fissure_screen)
        pygame.draw.rect(surface, (210, 80, 40), fissure_screen, 1)

    def draw_over_world(self, surface: pygame.Surface):
        self.dust.draw(surface)
        self.debris.draw(surface)
        self.vignette.draw(surface, strength=0.25 + 0.45 * self._seismic_rumble)
