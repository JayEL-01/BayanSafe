"""Chapter 4 - Level 4: Volcanic Tremor Swarm & Steam Venting (North East Plains).

Location: Plains-Valley Gateway & Boundary Post.
Disaster: Volcanic Earthquake Swarm & Phreatic Steam Venting.
Objectives: Evacuate plains boundary, consult Dr. Mira Santos on SO2 gas, enforce 6-km Danger Zone.

Pixel-game layer:
  * Pickups: N95 RESPIRATOR, SO2 DETECTOR, WARNING FLARE.
  * Mini-games: Gas Sensor Calibration (TimingMeter), PDZ Gate Lockout (Mash).
  * Pressure: Volcanic tremor screen shakes, SO2 gas toxicity meter, ash steam vent setbacks.
  * Atmosphere: Drifting yellow sulfur clouds, cracked highway, distant caldera rumblings.
"""

from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    TimingMeter,
    Mash,
)
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.hazards.landslide import VolcanicEruptionHazard
from src.config.palette import (
    COLOR_GROUND_PLAINS,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class Chapter4Level4EarthquakeVolcano(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    HIGHWAY_RECT = (30, 160, 580, 40)
    VENT_ZONE = (160, 150, 100, 60)
    SENSOR_HUB_POS = (115, 135)
    GATE_BOOM_POS = (360, 150)
    PDZ_ZONE = (460, 50, 120, 80)
    SANTOS_POS = (115, 140)

    # Pickups
    MASK_POS = (85, 135)
    DETECTOR_POS = (220, 135)
    FLARE_POS = (315, 135)

    SWARM_SECONDS = 120.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_4_earthquake_volcano",
            title="Chapter 4 - Level 4: The Earth Groans",
            subtitle="Plains Gateway - Harmonic Tremors & Phreatic Venting",
            disaster_type="Volcanic Earthquake Swarm & Alert Level 3",
            lesson_source="DOST-PHIVOLCS Volcanic Alert Level Scheme & Permanent Danger Zone (PDZ) Standards",
            lesson_text=(
                "Volcano Alert Level 3 indicates high level of volcanic unrest with magma intrusion.\n"
                "A 6-kilometer radius Permanent Danger Zone (PDZ) must be evacuated immediately.\n"
                "Volcanic sulfur dioxide (SO2) gas is toxic and heavier than air, collecting in low ravines.\n"
                "Wear N95 respirators or moist cotton masks and evacuate immediately upwind."
            ),
        )

        # Progress flags
        self._santos_assisted: bool = False
        self._sensor_calibrated: bool = False
        self._gate_locked: bool = False
        self._gas_toxicity: float = 0.25

        # Visuals
        self.steam = ParticleField("smoke", seed=17, count=22)
        self.vignette = Vignette(color=(50, 45, 15), max_alpha=160)

        # Build world & hazards
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=6))
        self.hazards.append(VolcanicEruptionHazard())

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("so2", "SO2 TOXICITY", 0.25, good_high=False)
        self.start_countdown(self.SWARM_SECONDS, "TREMOR CLIMAX", on_expire=self._tremor_climax)

        # Structured quest steps
        self.set_steps([
            {
                "text": "Consult Dr. Mira Santos at the Gas Sensor Hub",
                "done": lambda: self._santos_assisted,
                "hint": "The highway is vibrating! Confer with Dr. Santos at the Gas Sensor Hub.",
                "target": self.SANTOS_POS,
            },
            {
                "text": "Calibrate the SO2 array at the sensor hub",
                "done": lambda: self._sensor_calibrated,
                "hint": "Interact with the sensor hub to calibrate sulfur telemetry.",
                "target": self.SENSOR_HUB_POS,
            },
            {
                "text": "Lock the PDZ barrier at the highway",
                "done": lambda: self._gate_locked,
                "hint": "Lock out the highway boom barrier to seal off the 6-km Danger Zone.",
                "target": self.GATE_BOOM_POS,
            },
            {
                "text": "Evacuate to the PDZ Command Outpost",
                "done": lambda: self.completed,
                "hint": "Retreat to the reinforced PDZ Checkpoint shelter!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Volcanic harmonic tremors shaking the plains gateway! Toxic gas venting ahead.", 5.0)

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Caldera Gateway Checkpoint", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Gateway highway
        bm.add_road(*self.HIGHWAY_RECT)
        bm.add_road(300, 30, 40, 270)

        # Toxic steam venting crack
        bm.add_hazard_zone("ash", *self.VENT_ZONE, label="SO2 STEAM VENT")
        self.watch_zone(self.VENT_ZONE, self._touch_vent)

        # Buildings
        bm.add_building("research", "GAS SENSOR HUB", 60, 60, 90, 70)
        bm.add_building("shelter", "PDZ CHECKPOINT", 460, 50, 120, 80)
        bm.add_safe_zone(*self.PDZ_ZONE, label="SAFE PERIMETER", trigger_id="pdz_safe")

        # Interactables
        self.add_interactable(
            "sensor_array", "GAS SENSOR ARRAY",
            (self.SENSOR_HUB_POS[0] - 8, self.SENSOR_HUB_POS[1] - 8, 16, 16),
            (220, 200, 50),
            on_interact=self._interact_sensor,
        )

        self.add_interactable(
            "pdz_gate", "HIGHWAY BOOM BARRIER",
            (self.GATE_BOOM_POS[0] - 8, self.GATE_BOOM_POS[1] - 8, 16, 16),
            (210, 60, 50),
            on_interact=self._interact_gate,
        )

        # Pickups
        self.add_pickup("mask", "N95 RESPIRATOR", self.MASK_POS, "mask")
        self.add_pickup("detector", "SO2 GAS DETECTOR", self.DETECTOR_POS, "generator")
        self.add_pickup("flare", "EMERGENCY FLARE", self.FLARE_POS, "fuelcan")

        # NPCs
        self.add_npc(
            "dr_mira_santos",
            "Dr. Mira Santos",
            self.SANTOS_POS,
            [
                "Sulfur dioxide flux just spiked past 8,000 metric tons per day!",
                "The groundwater pH dropped to 1.8—it is burning through our monitoring probes!",
                "The caldera is swelling. An explosive magmatic eruption is imminent within hours!",
                "We must seal the 6-km Permanent Danger Zone and stop anyone from heading toward the valley!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_vent(self):
        if not self.is_busy():
            self.hurt("Inhaled acidic volcanic steam! Toxic sulfur gas choked your throat.", penalty=5.0, respawn=True)

    def _tremor_climax(self):
        self.hurt("A violent harmonic tremor shook the roadway! Regain footing immediately!", penalty=6.0, respawn=True)
        self.start_countdown(45.0, "TREMOR SHAKE", on_expire=self._tremor_climax)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Dr. Mira Santos" or self.is_busy():
            return

        if not self._santos_assisted:
            self.start_dialogue(
                "Dr. Mira Santos",
                [
                    "A dense yellowish sulfur gas cloud is drifting across the highway from ground fractures!",
                    "How do we safely proceed across the boundary to seal the Permanent Danger Zone?",
                ],
            )
            self.ask(
                decision_id="volcanic_gas_choice",
                prompt="A yellowish sulfur gas cloud is drifting across the gateway road. How do you pass?",
                options=[
                    {
                        "text": "Put on N95 mask / moist cloth, move upwind, avoid low ravines where gas pools",
                        "safe": True,
                        "lesson": "SO2 gas irritates the respiratory tract; staying upwind prevents acute poisoning.",
                    },
                    {
                        "text": "Walk directly through the dense yellow fog breathing deeply without a mask",
                        "safe": False,
                        "lesson": "Inhaling dense volcanic sulfur dioxide triggers severe pulmonary edema and suffocation.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Always wear protective masks and stay upwind of heavy volcanic gas plumes!",
            )
        elif not self._sensor_calibrated:
            self.start_dialogue(
                "Dr. Mira Santos",
                [
                    "Calibrate the Gas Sensor Hub array so PHIVOLCS can track the magma intrusion!",
                ],
            )
        elif not self._gate_locked:
            self.start_dialogue(
                "Dr. Mira Santos",
                [
                    "Telemetry active! Now padlock the highway boom barrier to establish the 6-km PDZ!",
                ],
            )
        else:
            self.start_dialogue(
                "Dr. Mira Santos",
                [
                    "PDZ perimeter secured! Evacuate to the command outpost beyond the safety line!",
                ],
            )

    def _on_decision_safe(self):
        if not self._santos_assisted:
            self._santos_assisted = True
            self.score_system.assist_resident("Dr. Mira Santos")
            self.record_score("warnings_followed", 1)

        self.show_hint("Interact with the GAS SENSOR ARRAY to calibrate SO2 readings!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Sensor Calibration & PDZ Gate Lockout
    # ------------------------------------------------------------------
    def _interact_sensor(self):
        if not self._santos_assisted:
            self.show_hint("Confer with Dr. Mira Santos on gas toxicity levels first.", 3.0)
            return

        if self._sensor_calibrated:
            self.show_hint("Gas sensors calibrated: 8,400 tonnes/day SO2 confirmed (Alert Level 3).", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="CALIBRATE SO2 SENSORS",
                hint="Tune infrared gas spectrometer to sulfur absorption peaks",
                rounds=2,
                speed=1.1,
                zone=0.23,
                steps=["Zero reference nitrogen baseline", "Lock onto SO2 optical absorption band"],
                win_text="SPECTROMETER CALIBRATED - DATA SYNCED!",
                fail_text="BASELINE DRIFT! RETRY",
                icon="generator",
            ),
            on_win=self._sensor_success,
            on_fail=lambda: self.show_hint("Optical sensor saturated. Re-zero baseline and calibrate.", 3.0),
        )

    def _sensor_success(self):
        self._sensor_calibrated = True
        self.set_checkpoint(self.SENSOR_HUB_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Sensors reporting! Now run east to lock down the HIGHWAY BOOM BARRIER!", 5.0)

    def _interact_gate(self):
        if not self._sensor_calibrated:
            self.show_hint("Calibrate and broadcast the hazard readings before sealing the road.", 3.5)
            return

        if self._gate_locked:
            self.show_hint("6-kilometer PDZ boom barrier locked shut. Perimeter established.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="LOCK PDZ BOOM BARRIER",
                hint="Mash SPACE to drop and padlock the heavy steel boom barrier!",
                target=16,
                decay=2.4,
                time_limit=8.0,
                icon="stick",
                win_text="PDZ SEALED - NO ADMITTANCE!",
                fail_text="BARRIER COUNTERWEIGHT SLIPPED! RETRY",
            ),
            on_win=self._gate_success,
            on_fail=lambda: self.show_hint("Heavy steel barrier jammed. Pull lever and drop firmly!", 3.0),
        )

    def _gate_success(self):
        self._gate_locked = True
        self.set_checkpoint(self.GATE_BOOM_POS)
        self.show_hint("Highway sealed! Evacuate to the SAFE PERIMETER at the PDZ Checkpoint!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "pdz_safe" and not self.completed:
            if not self._gate_locked:
                self.show_hint("Seal the PDZ highway gate before retreating to safety!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch4_4")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.steam.update(dt)

        self._gas_toxicity = min(0.85, 0.25 + (self.level_time / 130.0) * 0.60)
        self.set_meter("so2", "SO2 TOXICITY", self._gas_toxicity, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Steaming yellow/gray sulfur vent
        vent_screen = self.camera.apply(pygame.Rect(self.VENT_ZONE))
        pygame.draw.rect(surface, (75, 70, 50), vent_screen)
        pygame.draw.rect(surface, (180, 165, 50), vent_screen, 1)

    def draw_over_world(self, surface: pygame.Surface):
        self.steam.draw(surface)
        self.vignette.draw(surface, strength=0.25 + 0.45 * self._gas_toxicity)
