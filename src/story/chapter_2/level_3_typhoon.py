"""Chapter 2 - Level 3: Urban Typhoon Blackout (Central Town).

Location: Central Town Medical Center & Commercial Avenues.
Disaster: Severe Typhoon (TCWS #3) & Complete Grid Failure.
Objectives: Navigate shattered glass streets, locate Nurse Joy, secure emergency cold chain vaccines.

Pixel-game layer:
  * Blackout: dark screen with a light circle around you (FLASHLIGHT widens it).
  * Rain, lightning flashes and roof sheets flying across the debris lane.
  * Pickups: FLASHLIGHT and the portable BATTERY (needed for the generator).
  * Mini-game: start the generator (connect, prime, pull cord).
  * Pressure: COLD CHAIN countdown for the vaccine fridge.
"""

import pygame
from src.story.base_level import (
    BaseLevel, ParticleField, Darkness, LightningFlash, FlyingDebris, TimingMeter,
)
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN


class Chapter2Level3Typhoon(BaseLevel):
    # Layout constants (world coordinates)
    PLAYER_START = (50, 175)
    DEBRIS_ZONE = (170, 150, 80, 60)       # block-map hazard marker
    DEBRIS_LANES = (150, 138, 140, 84)     # where roof sheets fly
    CHECKPOINT = (136, 172)
    GENERATOR_RECT = (500, 100, 30, 24)
    GENERATOR_COLOR = (210, 170, 50)
    FLASHLIGHT_POS = (210, 95)
    BATTERY_POS = (215, 240)

    FRIDGE_SECONDS = 90
    FRIDGE_REPEAT_SECONDS = 45
    DARK_ALPHA = 165
    LIGHT_RADIUS = 62
    LIGHT_RADIUS_FLASHLIGHT = 104

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_2",
            level_id="level_3_typhoon",
            title="Chapter 2 - Level 3: Winds Over the City",
            subtitle="Central Town - Urban Debris & Blackout",
            disaster_type="Typhoon (PAGASA TCWS #3)",
            lesson_source="DOST-PAGASA Tropical Cyclone TCWS #3 Guidelines & DOH Cold Chain Preservation Standards",
            lesson_text=(
                "Under TCWS #3 (winds 89-117 km/h), unanchored billboards and roof sheets become airborne missiles.\n"
                "Stay clear of glass curtain-wall buildings; flying debris shatters glass inward.\n"
                "During prolonged blackouts, medical facilities must activate backup generators\n"
                "to maintain the cold chain (+2°C to +8°C) for vaccines, antivenoms, and blood units."
            ),
        )
        # Progress flags (set before the world is built)
        self._joy_met = False
        self.power_on = False
        self._power_level = 0.0
        self._fridge_total = float(self.FRIDGE_SECONDS)

        self.rain = ParticleField("rain", seed=2, count=110)
        self.dark = Darkness(alpha=self.DARK_ALPHA)
        self.lightning = LightningFlash(seed=4)
        self.debris = FlyingDebris(self.DEBRIS_LANES, seed=8)

        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=3))
        self.objectives = [
            "You dodge glass fall zones along the avenue",
            "You reach Nurse Joy at the Municipal Health Center",
            "You power vaccine cold storage from the auxiliary generator",
        ]
        self.guide_points = [
            self.guide_pickup("flashlight"),
            self.guide_npc("Nurse Joy"),
            self.guide_interactable("generator"),
        ]
        self.set_checkpoint(self.CHECKPOINT)
        self.show_hint("Blackout! Find the FLASHLIGHT, then reach Nurse Joy.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Central Urban Health Center",
            width=640,
            height=360,
            ground_color=COLOR_GROUND_CENTRAL_TOWN,
        )
        bm = self.block_map

        # Wide urban boulevard
        bm.add_road(30, 160, 580, 40)
        bm.add_road(290, 30, 40, 270)

        # Buildings
        bm.add_building("clinic", "HEALTH CENTER", 360, 60, 120, 80)
        bm.add_safe_zone(360, 60, 120, 80, label="SAFE CLINIC", trigger_id="clinic_safe")
        bm.add_building("damaged_house", "HIGHRISE STORE", 60, 50, 100, 90)
        bm.add_building("commercial", "COMMERCIAL PLAZA", 60, 220, 100, 70)

        # Shattered glass debris zone
        bm.add_hazard_zone("landslide", *self.DEBRIS_ZONE, label="FLYING DEBRIS")
        self.watch_zone(self.DEBRIS_ZONE, self._warn_debris)

        # Auxiliary generator panel for the vaccine cold-storage unit
        self.add_interactable(
            "generator",
            "GENERATOR",
            self.GENERATOR_RECT,
            self.GENERATOR_COLOR,
            on_interact=self._use_generator,
        )

        # Collectibles
        self.add_pickup("flashlight", "FLASHLIGHT", self.FLASHLIGHT_POS, "flashlight")
        self.add_pickup("battery", "BATTERY", self.BATTERY_POS, "battery")

        # NPCs
        self.add_npc(
            "nurse_joy",
            "Nurse Joy",
            (410, 150),
            [
                "The power grid tripped when the substation caught gale-force winds!",
                "Our vaccine refrigerator contains hundreds of childhood immunizations and rabies shots!",
                "Help me hook up the portable solar inverter battery to maintain refrigerator temperatures!",
            ],
            role="medical",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Storm, debris and the fridge timer
    # ------------------------------------------------------------------
    def _warn_debris(self):
        self.show_hint("FLYING DEBRIS! Watch the red warning and time your crossing.", 3.5)

    def update_level(self, dt):
        self.rain.update(dt)
        self.lightning.update(dt)

        # Lights fade back in once the generator is on
        if self.power_on and self._power_level < 1.0:
            self._power_level = min(1.0, self._power_level + dt / 2.0)
        self.dark.alpha = int(self.DARK_ALPHA * (1.0 - 0.75 * self._power_level))

        if self.completed or self.is_busy():
            return

        self.debris.update(dt)
        if self.debris.hits(self.player.rect):
            self.hurt("A flying roof sheet hit you! Wait for a gap, then cross.", respawn=True)

        if self.countdown_active and self._joy_met and not self.power_on:
            self.set_meter(
                "fridge", "COLD CHAIN",
                self.countdown_time / max(1.0, self._fridge_total), good_high=True,
            )

    def _fridge_warmed(self):
        if self.completed or self.power_on:
            return
        self.hurt("The vaccine fridge is warming up! Hurry to the generator!")
        self._fridge_total = float(self.FRIDGE_REPEAT_SECONDS)
        self.start_countdown(self.FRIDGE_REPEAT_SECONDS, "FRIDGE WARMING", on_expire=self._fridge_warmed)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_over_world(self, surface):
        self.debris.draw(surface, self.camera)
        # Blackout with a light circle around the player
        centre = self.camera.apply(self.player.rect).center
        radius = self.LIGHT_RADIUS_FLASHLIGHT if self.has_item("flashlight") else self.LIGHT_RADIUS
        if self.power_on:
            radius += int(60 * self._power_level)
        self.dark.draw(surface, centre, radius)
        self.rain.draw(surface)
        self.lightning.draw(surface)

    # ------------------------------------------------------------------
    # Story events
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Nurse Joy":
            return

        if self._joy_met:
            if not self.power_on:
                self.show_hint("Use the GENERATOR panel east of the Health Center.", 4.0)
            return

        if self.current_objective_idx == 0 and not self.has_item("flashlight"):
            self.show_hint("Find the FLASHLIGHT before crossing the dark avenue.", 4.0)
            return

        # Award the assist score once, then advance only the active step.
        self._joy_met = True
        self.score_system.assist_resident("Nurse Joy")
        if self.current_objective_idx == 0:
            self.complete_objective(0)
        if self.current_objective_idx == 1:
            self.complete_objective(1)
        self._fridge_total = float(self.FRIDGE_SECONDS)
        self.start_countdown(self.FRIDGE_SECONDS, "FRIDGE WARMING", on_expire=self._fridge_warmed)
        if self.has_item("battery"):
            self.show_hint("You have the battery! Start the GENERATOR east of the clinic.", 5.0)
        else:
            self.show_hint("Find the BATTERY near the Commercial Plaza, then use the GENERATOR.", 5.0)

    def _use_generator(self, item):
        if item["done"]:
            return
        if not self.require_step(2, "Talk to Nurse Joy first"):
            return
        if not self.has_item("battery"):
            self.show_hint("You need the portable BATTERY. Look near the Commercial Plaza.", 4.0)
            return

        self.start_minigame(
            TimingMeter(
                "START GENERATOR", "",
                steps=[
                    "Connect the battery terminals",
                    "Prime the fuel line",
                    "Pull the starter cord",
                ],
                speed=0.9, zone=0.28, max_misses=3,
                icon="generator", win_text="GENERATOR ON!",
            ),
            on_win=lambda: self._generator_started(item),
            on_fail=lambda: self.show_hint("It sputtered and died. Try again!", 3.0),
        )

    def _generator_started(self, item):
        # Generator is running; now decide where the limited fuel goes.
        # Opens right away; only the safe answer advances.
        self.ask(
            decision_id="urban_blackout_power_choice",
            prompt="The generator fuel is limited. Which loads should be powered on priority?",
            options=[
                {
                    "text": "Priority power strictly for vaccine cold-chain fridge and emergency lights",
                    "safe": True,
                    "lesson": "Preserving life-saving vaccines and basic triage visibility prevents catastrophe.",
                },
                {
                    "text": "Plug in hallway entertainment screens and personal phone fast-chargers first",
                    "safe": False,
                    "lesson": "Wasting auxiliary power exhausts fuel, spoiling perishable medications.",
                },
            ],
            on_safe=lambda: self._on_power_safe(item),
            retry_hint="Fuel is limited. Protect the vaccines first.",
        )

    def _on_power_safe(self, item):
        item["done"] = True
        self.power_on = True
        self.stop_countdown()
        self.clear_meter("fridge")
        self.score_system.complete_evacuation("ch2_3")
        self.complete_objective()  # cold storage on generator -> completes the level
        if not self.completed:
            self.complete_level()