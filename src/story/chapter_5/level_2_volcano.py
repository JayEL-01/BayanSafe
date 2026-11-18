"""Chapter 5 - Level 2: Explosive Eruption & Ashfall (Volcano Valley).

Location: Volcano Flanks & Evacuation Corridor.
Disaster: Volcanic Eruption (PHIVOLCS Alert Level 5) & Heavy Ashfall.
Objectives: Maneuver through abrasive ashfall, provide N95 protection to Rhea, reach convoy shelter.

Pixel-game layer:
  * Pickups: WRAP GOGGLES & N95 MASK, HALOGEN SEARCHLIGHT, WATER CANTEEN.
  * Mini-games: Goggles & Respirator Fit (TimingMeter), Clear Convoy Air Intake (Mash).
  * Pressure: Accumulated ash deposit meter, pitch-black ash darkness, abrasive silica eye setbacks.
  * Atmosphere: Dark heavy ashfall plume, zero-visibility gloom, roadside waiting shed.
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
from src.hazards.landslide import VolcanicEruptionHazard
from src.config.palette import (
    COLOR_GROUND_VALLEY,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class Chapter5Level2Volcano(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    HIGHWAY_RECT = (30, 160, 580, 40)
    ASH_DRIFT_ZONE = (150, 150, 200, 60)
    RHEA_SHED_POS = (115, 140)
    BUS_RADIATOR_POS = (435, 145)
    CONVOY_ZONE = (460, 50, 120, 80)

    # Pickups
    GOGGLES_POS = (85, 135)
    LIGHT_POS = (220, 135)
    WATER_POS = (340, 135)

    ASH_PLUME_SECONDS = 115.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_2_volcano",
            title="Chapter 5 - Level 2: Ashfall Darkness",
            subtitle="Volcano Flanks - Explosive Plume & Pyroclastic Hazard",
            disaster_type="Volcanic Eruption (Alert Level 5)",
            lesson_source="DOST-PHIVOLCS & DOH Volcanic Ashfall Health & Safety Guidelines",
            lesson_text=(
                "Volcanic ash consists of microscopic jagged pulverized rock and glass shards.\n"
                "Never rub irritated eyes; flush with clean water to avoid corneal scratches.\n"
                "Protect lungs with N95 respirators or moist cotton handkerchiefs.\n"
                "Accumulated wet ash weighs over 1,000 kg per cubic meter; scrape roofs to avoid cave-ins."
            ),
        )

        # Progress flags
        self._rhea_assisted: bool = False
        self._mask_fitted: bool = False
        self._bus_cleared: bool = False
        self._ash_accumulation: float = 0.30

        # Visuals
        self.ashfall = ParticleField("smoke", seed=25, count=38)
        self.embers = ParticleField("embers", seed=19, count=14)
        self.vignette = Vignette(color=(22, 22, 24), max_alpha=185)

        # Build world & hazards
        self._build_world()
        self.hazards.append(VolcanicEruptionHazard())

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("ash", "ASH ACCUMULATION", 0.30, good_high=False)
        self.start_countdown(self.ASH_PLUME_SECONDS, "PLUME BURST", on_expire=self._plume_burst)

        # Structured quest steps
        self.set_steps([
            {
                "text": "Locate Rhea at the ash-covered waiting shed",
                "done": lambda: self._rhea_assisted,
                "hint": "Heavy ash cloud blocking the sun! Find Rhea near the roadside waiting shed.",
                "target": self.RHEA_SHED_POS,
            },
            {
                "text": "Fit Rhea with goggles and a mask at the shed",
                "done": lambda: self._mask_fitted,
                "hint": "Interact with Rhea to seal eye goggles and mask against abrasive ash.",
                "target": self.RHEA_SHED_POS,
            },
            {
                "text": "Clear ash from the convoy bus air intake",
                "done": lambda: self._bus_cleared,
                "hint": "Scrape thick ash deposits from the convoy bus radiator intake.",
                "target": self.BUS_RADIATOR_POS,
            },
            {
                "text": "Escort Rhea into the Convoy bus shelter",
                "done": lambda: self.completed,
                "hint": "Board the Evacuation Convoy bus at the shelter post!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Alert Level 5 eruption! Total daytime darkness from dense volcanic ashfall.", 5.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Volcano Flanks Ash Corridor", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Ash road
        bm.add_road(*self.HIGHWAY_RECT)
        bm.add_hazard_zone("ash", *self.ASH_DRIFT_ZONE, label="THICK ASH DEPOSIT")
        self.watch_zone(self.ASH_DRIFT_ZONE, self._touch_ash)

        # Structures
        bm.add_building("house", "WAITING SHED", 60, 60, 85, 60)
        bm.add_building("shelter", "CONVOY BUS POST", 460, 50, 120, 80)
        bm.add_safe_zone(*self.CONVOY_ZONE, label="CONVOY POST", trigger_id="convoy_safe")

        # Interactables
        self.add_interactable(
            "rhea_fit", "RHEA RESPIRATORY FIT",
            (self.RHEA_SHED_POS[0] - 8, self.RHEA_SHED_POS[1] - 8, 16, 16),
            (210, 180, 70),
            on_interact=self._interact_mask,
        )

        self.add_interactable(
            "bus_radiator", "BUS RADIATOR INTAKE",
            (self.BUS_RADIATOR_POS[0] - 8, self.BUS_RADIATOR_POS[1] - 8, 16, 16),
            (160, 170, 190),
            on_interact=self._interact_bus,
        )

        # Pickups
        self.add_pickup("goggles", "WRAP GOGGLES", self.GOGGLES_POS, "mask")
        self.add_pickup("light", "SEARCHLIGHT", self.LIGHT_POS, "flashlight")
        self.add_pickup("water", "WATER CANTEEN", self.WATER_POS, "gobag")

        # NPCs
        self.add_npc(
            "rhea",
            "Rhea",
            self.RHEA_SHED_POS,
            [
                "The sky turned completely pitch black in the middle of the afternoon!",
                "The gray sand is stinging my eyes and throat! It smells like rotten eggs!",
                "Thank you for putting this wet cloth over my nose! Let's get to the bus!",
            ],
            role="vulnerable",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_ash(self):
        if not self.is_busy():
            self.hurt("Abrasive volcanic ash blinded your vision! Flush eyes with water.", penalty=4.0, respawn=True)

    def _plume_burst(self):
        self.hurt("Pyroclastic ash burst rained hot cinders! Shelter immediately!", penalty=6.0, respawn=True)
        self.start_countdown(45.0, "ASH COLLAPSE", on_expire=self._plume_burst)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Rhea" or self.is_busy():
            return

        if not self._rhea_assisted:
            self.start_dialogue(
                "Rhea",
                [
                    "Abrasive gritty ash is falling like burning snow! My eyes are stinging terribly!",
                    "How do we protect our eyes and lungs from these sharp volcanic glass shards?",
                ],
            )
            self.ask(
                decision_id="ashfall_health_choice",
                prompt="Heavy gritty volcanic ash is falling like snow. How do you protect eyes and lungs?",
                options=[
                    {
                        "text": "Wear wrap-around goggles and an N95 mask; seal collar and cuffs",
                        "safe": True,
                        "lesson": "Proper sealing prevents abrasive silica glass shards from lacerating lung alveoli.",
                    },
                    {
                        "text": "Rub eyes vigorously and keep looking straight up into the ash cloud",
                        "safe": False,
                        "lesson": "Rubbing volcanic ash into eyes causes severe corneal lacerations and blindness.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never rub ash in eyes! Wear wrap goggles and sealed N95 masks.",
            )
        elif not self._mask_fitted:
            self.start_dialogue(
                "Rhea",
                [
                    "Help me tighten the straps on the goggles and mask so the ash cannot seep in!",
                ],
            )
        elif not self._bus_cleared:
            self.start_dialogue(
                "Rhea",
                [
                    "I can breathe clearly now! Clear the heavy ash off the convoy bus engine intake so we can depart!",
                ],
            )
        else:
            self.start_dialogue(
                "Rhea",
                [
                    "Engine intake is cleared! Board the convoy bus immediately!",
                ],
            )

    def _on_decision_safe(self):
        if not self._rhea_assisted:
            self._rhea_assisted = True
            self.score_system.assist_resident("Rhea")
            self.record_score("warnings_followed", 1)

        self.show_hint("Interact with Rhea to seal her N95 mask and wrap goggles!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Mask Fit & Convoy Air Intake Scrape
    # ------------------------------------------------------------------
    def _interact_mask(self):
        if not self._rhea_assisted:
            self.show_hint("Consult with Rhea on protective gear first.", 3.0)
            return

        if self._mask_fitted:
            self.show_hint("Rhea's goggles and N95 mask are securely sealed.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="FIT RESPIRATOR & GOGGLES",
                hint="Adjust nose bridge clip and strap tension for airtight seal",
                rounds=2,
                speed=1.0,
                zone=0.25,
                steps=["Clamp metal nose bridge clip", "Secure dual elastic headbands"],
                win_text="AIRTIGHT RESPIRATOR FIT CONFIRMED!",
                fail_text="STRAP SLIPPED! RETRY",
                icon="mask",
            ),
            on_win=self._mask_success,
            on_fail=lambda: self.show_hint("Mask gap leaked silica dust. Pinch the nose bridge firmly!", 3.0),
        )

    def _mask_success(self):
        self._mask_fitted = True
        self.set_checkpoint(self.RHEA_SHED_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Rhea protected! Now clear the heavy ash from the CONVOY BUS intake!", 5.0)

    def _interact_bus(self):
        if not self._mask_fitted:
            self.show_hint("Protect Rhea with mask and goggles before moving to the convoy.", 3.5)
            return

        if self._bus_cleared:
            self.show_hint("Convoy bus radiator cleared. Engine breathing cleanly.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="CLEAR CONVOY AIR INTAKE",
                hint="Mash SPACE to brush heavy compacted volcanic ash off the radiator!",
                target=15,
                decay=2.3,
                time_limit=8.0,
                icon="gobag",
                win_text="AIR INTAKE CLEARED - ENGINE PURRING!",
                fail_text="ASH COMPACTED! RETRY",
            ),
            on_win=self._bus_success,
            on_fail=lambda: self.show_hint("Dense ash hardened on the grill. Scrape vigorously!", 3.0),
        )

    def _bus_success(self):
        self._bus_cleared = True
        self.set_checkpoint(self.BUS_RADIATOR_POS)
        self.show_hint("Convoy intake cleared! Board the CONVOY POST shelter!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "convoy_safe" and not self.completed:
            if not self._bus_cleared:
                self.show_hint("Clear the convoy bus intake and secure Rhea before boarding!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch5_2")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.ashfall.update(dt)
        self.embers.update(dt)

        self._ash_accumulation = min(0.90, 0.30 + (self.level_time / 120.0) * 0.60)
        self.set_meter("ash", "ASH ACCUMULATION", self._ash_accumulation, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Deep gray ash deposit zone
        ash_screen = self.camera.apply(pygame.Rect(self.ASH_DRIFT_ZONE))
        pygame.draw.rect(surface, (90, 92, 98), ash_screen)
        pygame.draw.rect(surface, (120, 122, 130), ash_screen, 1)

    def draw_over_world(self, surface: pygame.Surface):
        self.ashfall.draw(surface)
        self.embers.draw(surface)
        self.vignette.draw(surface, strength=0.35 + 0.50 * self._ash_accumulation)
