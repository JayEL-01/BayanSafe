"""Chapter 5 - Level 3: Wildfire & Lava Bombardment (Volcano Valley).

Location: Aegis-Terra Perimeter Campus.
Disaster: Ballistic Bombardment & Wildfire Inferno.
Objectives: Avoid falling incandescent bombs, clear mineral soil firebreak, breach bunker airlock.

Pixel-game layer:
  * Pickups: FOAM EXTINGUISHER, TRENCHING TOOL, ASBESTOS WRAP.
  * Mini-games: Dig Mineral Firebreak (Mash), Airlock Blast Seal Override (TimingMeter).
  * Pressure: Wildfire spread meter, ballistic lava bomb crater hazards, fuel tank threat.
  * Atmosphere: Raging code-drawn brushfire, flying embers, smoke plume, bunker airlock.
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
)
from src.maps.block_map import BlockMap
from src.hazards.landslide import FlashFireHazard
from src.config.palette import (
    COLOR_GROUND_VALLEY,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class Chapter5Level3FlashFire(BaseLevel):
    # World layout constants
    PLAYER_START = (50, 175)
    COMPOUND_ROAD = (30, 160, 580, 40)
    BRUSHFIRE_ZONE = (160, 150, 120, 60)
    FIREBREAK_LINE_POS = (240, 168)
    AIRLOCK_PANEL_POS = (440, 145)
    AIRLOCK_SAFE_ZONE = (460, 50, 120, 80)
    PAOLO_POS = (115, 140)

    # Pickups
    EXTINGUISHER_POS = (85, 135)
    SHOVEL_POS = (210, 135)
    BLANKET_POS = (360, 135)

    FIRE_SECONDS = 120.0

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_3_flash_fire",
            title="Chapter 5 - Level 3: Rain of Fire",
            subtitle="Facility Perimeter - Ballistic Bombs & Wildfire",
            disaster_type="Ballistic Lava Bombs & Wildfire",
            lesson_source="DENR Forest Management Bureau (FMB) Wildfire Suppression & PHIVOLCS Ballistic Hazards",
            lesson_text=(
                "Volcanic ballistic bombs can exceed automobile size and crash miles from the crater.\n"
                "Wildfires ignited by volcanic debris require proactive firebreaks;\n"
                "scraping vegetation down to bare mineral earth starves the flame of fuel.\n"
                "Seek immediate reinforced concrete or subterranean shelter during active ballistic ejecta."
            ),
        )

        # Progress flags
        self._paolo_assisted: bool = False
        self._firebreak_dug: bool = False
        self._airlock_unsealed: bool = False
        self._fire_spread: float = 0.25

        # Visuals
        self.embers = ParticleField("embers", seed=28, count=32)
        self.smoke = ParticleField("smoke", seed=14, count=24)
        self.vignette = Vignette(color=(50, 20, 10), max_alpha=165)

        # Build world & hazards
        self._build_world()
        self.hazards.append(FlashFireHazard())

        # Checkpoints & meters
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("fire", "WILDFIRE SPREAD", 0.25, good_high=False)
        self.start_countdown(self.FIRE_SECONDS, "FUEL TANK THREAT", on_expire=self._fire_threat)

        # Structured quest steps
        self.set_steps([
            {
                "text": "Meet Engr. Paolo Santos at the generator shed",
                "done": lambda: self._paolo_assisted,
                "hint": "Lava bombs exploding outside! Find Engr. Paolo Santos near the perimeter generator.",
                "target": self.PAOLO_POS,
            },
            {
                "text": "Dig a firebreak at the perimeter fuel tanks",
                "done": lambda: self._firebreak_dug,
                "hint": "Interact with the firebreak line to scrape fuel away from the diesel tanks.",
                "target": self.FIREBREAK_LINE_POS,
            },
            {
                "text": "Disengage the airlock seals at the facility",
                "done": lambda: self._airlock_unsealed,
                "hint": "Override the pneumatic airlock locks to open access to the bunker.",
                "target": self.AIRLOCK_PANEL_POS,
            },
            {
                "text": "Breach the Aegis-Terra Facility Airlock",
                "done": lambda: self.completed,
                "hint": "Take shelter inside the subterranean BUNKER AIRLOCK!",
                "target": (520, 90),
            },
        ])

        self.show_hint("Volcanic ballistic bombs crashing down! Wildfire threatens perimeter fuel tanks.", 5.0)

    # ------------------------------------------------------------------
    # World Layout
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap("Aegis-Terra Facility Campus", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Paved compound road
        bm.add_road(*self.COMPOUND_ROAD)

        # Raging brushfire hazard blocks
        bm.add_hazard_zone("fire", *self.BRUSHFIRE_ZONE, label="BURNING BRUSH")
        self.watch_zone(self.BRUSHFIRE_ZONE, self._touch_fire)

        # Structures
        bm.add_building("warehouse", "PERIMETER GENERATOR", 60, 60, 90, 70)
        bm.add_building("research", "FACILITY AIRLOCK", 460, 50, 120, 80)
        bm.add_safe_zone(*self.AIRLOCK_SAFE_ZONE, label="BUNKER AIRLOCK", trigger_id="airlock_safe")

        # Interactables
        self.add_interactable(
            "firebreak", "FIREBREAK LINE",
            (self.FIREBREAK_LINE_POS[0] - 8, self.FIREBREAK_LINE_POS[1] - 8, 16, 16),
            (140, 100, 50),
            on_interact=self._interact_firebreak,
        )

        self.add_interactable(
            "airlock_override", "AIRLOCK OVERRIDE",
            (self.AIRLOCK_PANEL_POS[0] - 8, self.AIRLOCK_PANEL_POS[1] - 8, 16, 16),
            (210, 60, 50),
            on_interact=self._interact_airlock,
        )

        # Pickups
        self.add_pickup("extinguisher", "FIRE EXTINGUISHER", self.EXTINGUISHER_POS, "extinguisher")
        self.add_pickup("shovel", "TRENCHING TOOL", self.SHOVEL_POS, "stick")
        self.add_pickup("blanket", "ASBESTOS WRAP", self.BLANKET_POS, "drybag")

        # NPCs
        self.add_npc(
            "engr_paolo_santos",
            "Engr. Paolo Santos",
            self.PAOLO_POS,
            [
                "Lava bombs are smashing through the trees like artillery shells!",
                "The grass is dry and the flames are racing straight toward the diesel fuel tanks!",
                "Help me dig a five-meter firebreak down to the raw gravel soil before the fire leaps the fence!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Hazards & Setbacks
    # ------------------------------------------------------------------
    def _touch_fire(self):
        if not self._firebreak_dug and not self.is_busy():
            self.hurt("Ouch! Incandescent brushfire embers singed your clothing!", penalty=5.0, respawn=True)

    def _fire_threat(self):
        self.hurt("Flames flared near the perimeter diesel manifold! Contain it quickly!", penalty=6.0, respawn=True)
        self.start_countdown(45.0, "FLAME SPREAD", on_expire=self._fire_threat)

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
                    "Flames ignited by incandescent lava bombs are racing across dry pine needles toward the tanks!",
                    "How do we halt the wildfire spread before the entire generator complex explodes?",
                ],
            )
            self.ask(
                decision_id="wildfire_firebreak_choice",
                prompt="Flames are racing across dry pine needles toward the compound. How do you stop them?",
                options=[
                    {
                        "text": "Scrape all vegetation and organic matter down to bare mineral dirt and rock",
                        "safe": True,
                        "lesson": "Fire cannot cross a fuel-free gap of bare mineral soil.",
                    },
                    {
                        "text": "Pile dry branches and brush in front of the flames thinking it will smother them",
                        "safe": False,
                        "lesson": "Adding dry fuel causes intense fire flares and rapid flame spread.",
                    },
                ],
                on_safe=self._on_decision_safe,
                retry_hint="Starve wildfires of fuel by scraping down to bare mineral rock and dirt!",
            )
        elif not self._firebreak_dug:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "Take the trenching shovel to the FIREBREAK LINE and clear a clean mineral trench!",
                ],
            )
        elif not self._airlock_unsealed:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "The firebreak is holding! Now disengage the blast locks on the FACILITY AIRLOCK!",
                ],
            )
        else:
            self.start_dialogue(
                "Engr. Paolo Santos",
                [
                    "Airlock seals uncoupled! Hurry inside before the next ballistic salvo lands!",
                ],
            )

    def _on_decision_safe(self):
        if not self._paolo_assisted:
            self._paolo_assisted = True
            self.score_system.assist_resident("Engr. Paolo Santos")
            self.record_score("warnings_followed", 1)

        self.show_hint("Head to the FIREBREAK LINE with the trenching shovel to scrape mineral dirt!", 5.0)

    # ------------------------------------------------------------------
    # Mini-games: Firebreak Dig & Airlock Decoupler
    # ------------------------------------------------------------------
    def _interact_firebreak(self):
        if not self._paolo_assisted:
            self.show_hint("Consult with Engr. Paolo Santos on firebreak placement first.", 3.0)
            return

        if self._firebreak_dug:
            self.show_hint("Bare mineral trench cleared. Firebreak successfully halted advancing flames.", 2.5)
            return

        self.start_minigame(
            Mash(
                title="DIG MINERAL FIREBREAK",
                hint="Mash SPACE to scrape pine duff and roots down to bare mineral gravel!",
                target=17,
                decay=2.4,
                time_limit=8.0,
                icon="stick",
                win_text="MINERAL FIREBREAK CLEARED - TANKS SAFE!",
                fail_text="DUFF RE-IGNITED! RETRY",
            ),
            on_win=self._firebreak_success,
            on_fail=lambda: self.show_hint("Organic duff remained in the trench. Scrape down to clean stone!", 3.0),
        )

    def _firebreak_success(self):
        self._firebreak_dug = True
        self.set_checkpoint(self.FIREBREAK_LINE_POS)
        self.record_score("supplies_secured", 1)
        self.show_hint("Firebreak complete! Now override the pneumatic AIRLOCK OVERRIDE panel!", 5.0)

    def _interact_airlock(self):
        if not self._firebreak_dug:
            self.show_hint("Contain the wildfire before attempting to breach the facility.", 3.5)
            return

        if self._airlock_unsealed:
            self.show_hint("Airlock blast doors decoupled. Safe to enter bunker.", 2.5)
            return

        self.start_minigame(
            TimingMeter(
                title="DECOUPLE AIRLOCK BLAST SEALS",
                hint="Depressurize pneumatic dogs to release hardened blast doors",
                rounds=3,
                speed=1.1,
                zone=0.23,
                steps=["Vent primary hydraulic line", "Disengage mechanical locking dog", "Equalize bunker airlock chamber"],
                win_text="BLAST DOORS UNLATCHED - AIRLOCK OPEN!",
                fail_text="HYDRAULIC PRESSURE SPIKE! RETRY",
                icon="generator",
            ),
            on_win=self._airlock_success,
            on_fail=lambda: self.show_hint("Blast seal pressure re-engaged. Time each valve release cleanly!", 3.0),
        )

    def _airlock_success(self):
        self._airlock_unsealed = True
        self.set_checkpoint(self.AIRLOCK_PANEL_POS)
        self.show_hint("Airlock unlatched! Take shelter inside the subterranean BUNKER AIRLOCK!", 5.0)

    # ------------------------------------------------------------------
    # Evacuation Trigger
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "airlock_safe" and not self.completed:
            if not self._airlock_unsealed:
                self.show_hint("Disengage the facility airlock seals before entering shelter!", 3.5)
                return

            self.stop_countdown()
            self.score_system.complete_evacuation("ch5_3")
            self.complete_level()

    # ------------------------------------------------------------------
    # Frame Updates & Visuals
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.embers.update(dt)
        self.smoke.update(dt)

        self._fire_spread = min(0.90, 0.25 + (self.level_time / 125.0) * 0.65)
        self.set_meter("fire", "WILDFIRE SPREAD", self._fire_spread, good_high=False)

    def draw_under_player(self, surface: pygame.Surface):
        # Raging brushfire
        fire_screen = self.camera.apply(pygame.Rect(self.BRUSHFIRE_ZONE))
        if not self._firebreak_dug:
            draw_flames(surface, fire_screen, self._anim_t)
        else:
            # Charred black ground
            pygame.draw.rect(surface, (30, 24, 22), fire_screen)
            pygame.draw.rect(surface, (120, 80, 50), fire_screen, 1)

    def draw_over_world(self, surface: pygame.Surface):
        self.embers.draw(surface)
        self.smoke.draw(surface)
        self.vignette.draw(surface, strength=0.25 + 0.45 * self._fire_spread)
