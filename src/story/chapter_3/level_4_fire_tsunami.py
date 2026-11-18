"""Chapter 3 - Level 4: Pier Fire & Incoming Tsunami (Harbor).

Location: Harbor Fuel Pier & Seaward Cliffs.
Disaster: Compound Disaster - Flash Fire & Approaching Tsunami.
Objectives: Bypass burning fuel line, shut off emergency isolation valve, scale cliff stairs.

Pixel-game layer:
  * Pickups: HEAT HOOD, FOAM EXTINGUISHER, VALVE KEY.
  * Mini-games: Fuel Line Isolation (TimingMeter), Cliff Stairs Sprint (Mash).
  * Pressure: Tsunami wave arrival countdown & surge meter, flash fire spread, burning oil setbacks.
  * Dual visual hazards: code-drawn raging oil flames + embers, approaching tsunami surge water with foam crest.
"""

from typing import Optional
import pygame

from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Vignette,
    TimingMeter,
    Mash,
    draw_flames,
    draw_water,
    draw_wading_ripples,
)
from src.maps.block_map import BlockMap
from src.hazards.landslide import FlashFireHazard, TsunamiHazard
from src.config.palette import (
    COLOR_GROUND_HARBOR,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class SilentCompoundHazards(FlashFireHazard):
    """Custom wrapper allowing BaseLevel to draw high-fidelity code-rendered
    flames, floating embers, and cascading tsunami surge without duplicate flat boxes."""

    def draw_effects(self, surface, camera):
        pass


class Chapter3Level4FireTsunami(BaseLevel):
    # World layout coordinates
    PLAYER_START = (50, 175)
    PIER_ROAD = (30, 160, 580, 40)
    SEAWARD_OCEAN = (0, 240, 640, 120)
    FIRE_ZONE = (160, 150, 100, 60)
    VALVE_POS = (280, 145)
    TITO_POS = (115, 140)
    CLIFF_STAIRS = (420, 70, 40, 100)
    CLIFF_SAFE_ZONE = (460, 40, 120, 80)

    # Pickups
    HOOD_POS = (85, 135)
    EXTINGUISHER_POS = (135, 215)
    KEY_POS = (240, 135)

    TSUNAMI_TIME = 100.0   # seconds until tsunami reaches pier

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_4_fire_tsunami",
            title="Chapter 3 - Level 4: Fire and Water",
            subtitle="Harbor Fuel Pier - Compound Cascading Disaster",
            disaster_type="Dual Hazard: Flash Fire & Tsunami",
            lesson_source="NDRRMC Multi-Hazard Protocol & BFP Hazardous Materials (HazMat) Emergency Response",
            lesson_text=(
                "In compound disaster events (e.g. industrial fire combined with imminent tsunami),\n"
                "life safety and rapid vertical evacuation supersede fire containment attempts.\n"
                "If fire cannot be extinguished within seconds, shut off emergency fuel isolation valves\n"
                "and immediately sprint to elevated terrain beyond the inundation line."
            ),
        )

        # Progress flags
        self._tito_assisted: bool = False
        self._valve_shut: bool = False
        self._stairs_climbed: bool = False
        self._fire_quenched: bool = False
        self._tsunami_progress: float = 0.15

        # Atmospheric particle effects
        self.embers = ParticleField("embers", seed=23, count=24)
        self.smoke = ParticleField("smoke", seed=7, count=16)
        self.vignette = Vignette(color=(50, 22, 12), max_alpha=160)

        # Build world
        self._build_world()
        self.hazards.append(SilentCompoundHazards())
        self.hazards.append(TsunamiHazard())

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("tsunami", "TSUNAMI SURGE", 0.15, good_high=False)
        self.start_countdown(self.TSUNAMI_TIME, "TSUNAMI INCOMING", on_expire=self._tsunami_hit)

        # Structured linear quest steps with bobbing gold arrow
        self.set_steps([
            {
                "text": "Speak to Tito Ramon near the ruptured fuel line",
                "done": lambda: self._tito_assisted,
                "hint": "Flames are leaping across the pier road! Find Tito Ramon near the bunker.",
                "target": self.TITO_POS,
            },
            {
                "text": "Shut off the master fuel cut-off valve to starve the fire",
                "done": lambda: self._valve_shut,
                "hint": "Grab the valve key and interact with the yellow shutoff wheel.",
                "target": self.VALVE_POS,
            },
            {
                "text": "Sprint past the burning barrier to the rocky cliff stairs",
                "done": lambda: self._stairs_climbed,
                "hint": "The ocean is drawing back! Run east toward the cliff stairs!",
                "target": (430, 150),
            },
            {
                "text": "Flee to the high cliff lookout assembly zone",
                "done": lambda: self.completed,
                "hint": "Climb up to the High Harbor Lookout to clear the inundation zone!",
                "target": (520, 80),
            },
        ])

        self.show_hint("Ruptured fuel lines burning while a tsunami bears down! Hurry!", 5.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Harbor Burning Pier", width=640, height=360, ground_color=COLOR_GROUND_HARBOR)
        bm = self.block_map

        # Concrete pier road & ocean basin
        bm.add_road(*self.PIER_ROAD)
        bm.add_water(*self.SEAWARD_OCEAN)

        # Cliff staircase path
        bm.add_road(420, 40, 50, 130)

        # Buildings
        bm.add_building("warehouse", "FUEL BUNKER", 60, 50, 95, 80)
        bm.add_building("shelter", "CLIFF LOOKOUT", 460, 40, 120, 85)
        bm.add_safe_zone(*self.CLIFF_SAFE_ZONE, label="HIGH CLIFF", trigger_id="cliff_safe")

        # Active burning oil hazard zone
        bm.add_hazard_zone("fire", *self.FIRE_ZONE, label="BURNING FUEL")
        self.watch_zone(self.FIRE_ZONE, self._touch_fire)

        # Emergency fuel valve wheel
        self.add_interactable(
            "valve", "FUEL CUT-OFF VALVE",
            (self.VALVE_POS[0] - 8, self.VALVE_POS[1] - 8, 16, 16),
            (240, 200, 50),
            on_interact=self._interact_valve,
        )

        # Cliff stairs interactable trigger
        self.add_interactable(
            "stairs", "CLIFF STAIRS",
            (420, 150, 30, 25),
            (160, 170, 185),
            on_interact=self._interact_stairs,
        )

        # Pickups
        self.add_pickup("hood", "HEAT HOOD", self.HOOD_POS, "hardhat")
        self.add_pickup("extinguisher", "FOAM EXTINGUISHER", self.EXTINGUISHER_POS, "extinguisher")
        self.add_pickup("key", "VALVE KEY", self.KEY_POS, "stick")

        # NPCs
        self.add_npc(
            "tito_ramon",
            "Tito Ramon",
            self.TITO_POS,
            [
                "The ruptured fuel pipe caught fire! Flames are spreading toward the barge!",
                "Hear that terrifying low rumble from the horizon? The tsunami wave is bearing down on us!",
                "Turn the yellow emergency cut-off wheel, then run for the cliff stairs!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazard Callbacks & Setbacks
    # ------------------------------------------------------------------
    def _touch_fire(self):
        if not self._fire_quenched and not self.is_busy():
            self.hurt("Ouch! Burning fuel slick! Do not walk through raw oil flames.", penalty=5.0, respawn=True)

    def _tsunami_hit(self):
        self.hurt("The tsunami wave washed over the low pier! Vertical evacuation is mandatory!", penalty=8.0, respawn=True)
        self.start_countdown(45.0, "TSUNAMI RE-SURGE", on_expire=self._tsunami_hit)

    # ------------------------------------------------------------------
    # NPC & Decision Handling
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Tito Ramon" or self.is_busy():
            return

        if not self._valve_shut:
            self.start_dialogue(
                "Tito Ramon",
                [
                    "Look at the horizon! The ocean water is receding rapidly—a massive tsunami is seconds away!",
                    "Meanwhile oil is spraying all over the pier! How do we handle both threats?",
                ],
            )
            self.ask(
                decision_id="compound_hazard_choice",
                prompt="Flames are licking the pipe while the ocean is roaring toward the pier. What is your action?",
                options=[
                    {
                        "text": "Turn the quick-shutoff valve and run immediately up the cliff path",
                        "safe": True,
                        "lesson": "Isolating fuel cut-offs stops escalation, allowing instant vertical evacuation.",
                    },
                    {
                        "text": "Grab a small bucket of water and stay on the pier trying to fight the oil fire",
                        "safe": False,
                        "lesson": "Throwing water on burning oil causes explosive fire splatters and traps you in the tsunami.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Never fight oil fires with water or delay evacuation when a tsunami approaches!",
            )
        elif not self._stairs_climbed:
            self.start_dialogue(
                "Tito Ramon",
                [
                    "The fuel feed is cut! Sprint to the cliff stairs at the east end of the pier!",
                    "Don't look back—every second counts before the crest slams ashore!",
                ],
            )
        else:
            self.start_dialogue(
                "Tito Ramon",
                [
                    "We made it above the high-water line! Stay at the High Lookout until the all-clear!",
                ],
            )

    def _on_decision_safe(self):
        if not self._tito_assisted:
            self._tito_assisted = True
            self.score_system.assist_resident("Tito Ramon")
            self.record_score("warnings_followed", 1)

        self.show_hint("Head past the bunker to the yellow VALVE wheel to cut fuel lines!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Valve Isolation & Stairs Sprint
    # ------------------------------------------------------------------
    def _interact_valve(self):
        if self._valve_shut:
            self.show_hint("Emergency fuel valve locked in OFF position. Pipelines isolated.", 3.0)
            return

        if not self._tito_assisted:
            self.show_hint("Talk to Tito Ramon to confirm shutdown sequence first.", 3.5)
            return

        self.start_minigame(
            TimingMeter(
                title="ISOLATE EMERGENCY FUEL LINE",
                hint="Turn cutoff wheel firmly to lock safety dog",
                rounds=3,
                speed=1.05,
                zone=0.24,
                steps=["Rotate yellow shutoff wheel", "Engage mechanical locking pin", "Depressurize manifold"],
                win_text="FUEL ISOLATED - FLAMES SUBSIDING!",
                fail_text="VALVE STUCK! RETRY",
                icon="stick",
            ),
            on_win=self._valve_success,
            on_fail=lambda: self.show_hint("Wheel jammed. Re-grip and turn with steady torque.", 3.0),
        )

    def _valve_success(self):
        self._valve_shut = True
        self._fire_quenched = True
        self.set_checkpoint(self.VALVE_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Fuel line sealed! Now sprint east to the CLIFF STAIRS before the wave hits!", 5.0)

    def _interact_stairs(self):
        if not self._valve_shut:
            self.show_hint("Isolate the fuel lines first so the entire depot does not detonate!", 3.5)
            return

        if self._stairs_climbed:
            self.show_hint("You already scaled the stairs! Reach the High Cliff assembly area.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="CLIFF STAIRS SPRINT",
                hint="Mash SPACE to power up the steep rocky stairs!",
                target=15,
                decay=2.4,
                time_limit=8.0,
                icon="hardhat",
                win_text="STAIRS SCALED - HIGH GROUND!",
                fail_text="SLIPPED ON WET STEPS! RETRY",
            ),
            on_win=self._stairs_success,
            on_fail=lambda: self.show_hint("You stumbled on the slick rock. Recover and sprint!", 2.5),
        )

    def _stairs_success(self):
        self._stairs_climbed = True
        self.set_checkpoint((430, 80))
        # Move player onto the high cliff path
        self.player.pos = pygame.Vector2(430, 80)
        self.player.rect.topleft = (430, 80)
        self.show_hint("You made it up the cliff! Proceed into the HIGH CLIFF shelter zone!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "cliff_safe" and not self.completed:
            if not self._stairs_climbed:
                self.show_hint("Scale the cliff stairs before entering the shelter area!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch3_4")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visual Rendering
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.embers.update(dt)
        self.smoke.update(dt)

        # Simulate approaching tsunami wave water rise
        time_elapsed = max(0.0, self.TSUNAMI_TIME - self.countdown_time) if self.countdown_active else self.level_time
        self._tsunami_progress = min(0.95, 0.15 + (time_elapsed / self.TSUNAMI_TIME) * 0.80)
        self.set_meter("tsunami", "TSUNAMI SURGE", self._tsunami_progress, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # 1. Harbor ocean water with depth & surging wave edge
        ocean_rect = pygame.Rect(self.SEAWARD_OCEAN)
        # Water encroaches northward as tsunami progress rises
        encroach_y = int(self._tsunami_progress * 40)
        surging_ocean = pygame.Rect(ocean_rect.x, ocean_rect.y - encroach_y, ocean_rect.w, ocean_rect.h + encroach_y)
        draw_water(surface, self.camera.apply(surging_ocean), self._anim_t, alpha=135, color=(25, 80, 145), foam=True, depth=True)

        # 2. Pier road water puddles if wave encroaches
        if encroach_y > 10:
            puddle_rect = pygame.Rect(30, 180, 580, 20)
            draw_water(surface, self.camera.apply(puddle_rect), self._anim_t, alpha=70, color=(40, 100, 170), foam=False)
            if self.player.rect.colliderect(puddle_rect):
                draw_wading_ripples(surface, self.camera, self.player.rect, self._anim_t)

        # 3. Code-drawn burning fuel slick if not quenched
        if not self._fire_quenched:
            fire_screen = self.camera.apply(pygame.Rect(self.FIRE_ZONE))
            # Black oil slick base
            slick_rect = fire_screen.inflate(4, 2)
            pygame.draw.rect(surface, (28, 24, 20), slick_rect)
            # Animated pixel flames
            draw_flames(surface, fire_screen, self._anim_t)

    def draw_over_world(self, surface: pygame.Surface):
        # Embers and smoke rising from burning fuel
        if not self._fire_quenched:
            self.embers.draw(surface)
            self.smoke.draw(surface)

        # Dual-threat emergency vignette
        self.vignette.draw(surface, strength=0.25 + 0.60 * self._tsunami_progress)
