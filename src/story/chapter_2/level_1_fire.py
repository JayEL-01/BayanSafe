"""Chapter 2 - Level 1: Flash Fire (Central Town).

Location: Central Town Commercial District.
Disaster: Flash Fire Outbreak & Dense Toxic Smoke.
Objectives: Stay low, avoid fire zones, locate Kuya Ben, reach clear street plaza.

Pixel-game layer:
  * Pickups: DAMP CLOTH (slows smoke damage) and FIRE EXTINGUISHER.
  * Mini-game: put the fire out with the P.A.S.S. technique (timing meter).
  * Pressure: SMOKE meter, a "fire spreads" countdown, burn setbacks.
"""

import pygame
from src.story.base_level import (
    BaseLevel, ParticleField, Vignette, TimingMeter, draw_flames, draw_charred,
)
from src.maps.block_map import BlockMap
from src.hazards.landslide import FlashFireHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN


class Chapter2Level1Fire(BaseLevel):
    # Layout constants (world coordinates)
    PLAYER_START = (50, 175)
    FIRE_ZONE = (160, 150, 90, 60)
    PLAZA_ZONE = (470, 150, 130, 110)
    SMOKE_ZONE = (30, 100, 250, 170)
    CLOTH_POS = (68, 152)
    EXTINGUISHER_POS = (156, 234)

    FIRE_SECONDS = 150      # first "fire spreads" countdown
    FIRE_REPEAT_SECONDS = 75
    SMOKE_RATE = 0.06       # exposure per second without a cloth
    SMOKE_RATE_CLOTH = 0.015
    SMOKE_RECOVER = 0.10

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_2",
            level_id="level_1_fire",
            title="Chapter 2 - Level 1: Inferno in the Streets",
            subtitle="Central Town - Commercial Grid Firestorm",
            disaster_type="Flash Fire (Code Red)",
            lesson_source="Bureau of Fire Protection (BFP) Standard Fire Safety & Smoke Inhalation Protocol",
            lesson_text=(
                "In a structural or urban fire, smoke inhalation is deadlier than direct flames.\n"
                "Stay low and crawl under smoke where oxygen remains coolest and cleanest.\n"
                "Cover mouth and nose with a damp cloth or face mask.\n"
                "Feel door panels with the back of your hand before opening to detect heat."
            ),
        )
        # Progress flags (set before the world is built)
        self._ben_scored = False   # assist score is awarded only once
        self._ben_helped = False   # smoke-crawl question answered safely
        self.fire_out = False
        self.exposure = 0.0
        self._cough_warned = False
        self._smoke_rect = pygame.Rect(self.SMOKE_ZONE)

        self.smoke = ParticleField("smoke", seed=11, count=16)
        self.embers = ParticleField("embers", seed=5, count=26)
        self.vignette = Vignette(color=(70, 40, 20), max_alpha=170)

        self._build_world()
        self.hazards.append(FlashFireHazard())
        self.objectives = [
            "You navigate the smoky commercial alleyways",
            "You assist Kuya Ben at the pharmacy jeepney",
            "You evacuate to the Town Plaza assembly zone",
        ]
        self.guide_points = [
            self.guide_pickup("cloth"),
            self.guide_npc("Kuya Ben"),
            lambda: (self.PLAZA_ZONE[0] + self.PLAZA_ZONE[2] // 2,
                     self.PLAZA_ZONE[1] + self.PLAZA_ZONE[3] // 2),
        ]
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("smoke", "SMOKE", 0.0, good_high=False)
        self.start_countdown(self.FIRE_SECONDS, "FIRE SPREADS", on_expire=self._fire_spread)
        self.show_hint("Smoke everywhere! Grab the DAMP CLOTH to cover your nose.", 6.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Central Town Commercial District",
            width=640,
            height=360,
            ground_color=COLOR_GROUND_CENTRAL_TOWN,
        )
        bm = self.block_map

        # Paved urban street grid
        bm.add_road(30, 160, 580, 40)
        bm.add_road(280, 30, 40, 270)

        # Commercial shop blocks
        bm.add_building("commercial", "PHARMACY", 60, 60, 85, 60)
        bm.add_building("commercial", "BAKERY", 170, 60, 80, 60)
        bm.add_building("commercial", "GROCERY", 350, 60, 90, 60)
        bm.add_building("commercial", "HARDWARE", 60, 220, 85, 60)

        # Active fire hazard zone (red/orange block)
        bm.add_hazard_zone("fire", *self.FIRE_ZONE, label="FLASH FIRE")
        self.watch_zone(self.FIRE_ZONE, self._touch_fire)

        # Wide open town plaza safe zone
        bm.add_safe_zone(*self.PLAZA_ZONE, label="TOWN PLAZA", trigger_id="plaza_safe")

        # Fire-fighting spot: SPACE next to the flames with the extinguisher.
        # (empty label so it does not duplicate the "FLASH FIRE" tag)
        self.add_interactable(
            "fire", "", self.FIRE_ZONE, (0, 0, 0),
            on_interact=self._use_extinguisher, alpha=1,
        )

        # Collectibles
        self.add_pickup("cloth", "DAMP CLOTH", self.CLOTH_POS, "mask")
        self.add_pickup("extinguisher", "EXTINGUISHER", self.EXTINGUISHER_POS, "extinguisher")

        # NPCs
        self.add_npc(
            "kuya_ben",
            "Kuya Ben",
            (105, 135),
            [
                "The transformer blew up and sparks showered all over the fabric awnings!",
                "The smoke is so black and thick you can't see five feet ahead!",
                "Keep your head close to the sidewalk pavement! Let's get to the open plaza!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Fire, smoke and timers
    # ------------------------------------------------------------------
    def _touch_fire(self):
        if not self.fire_out:
            self.hurt("Ouch! You touched the flames. Go around or put them out.", respawn=True)

    def _fire_spread(self):
        if self.completed:
            return
        self.hurt("The fire spread! You were pushed back to the street corner.", respawn=True)
        self.start_countdown(self.FIRE_REPEAT_SECONDS, "FIRE SPREADS", on_expire=self._fire_spread)

    def _use_extinguisher(self, item):
        if self.fire_out:
            return
        if not self.has_item("extinguisher"):
            self.show_hint("You need a fire extinguisher. Try near the hardware store.", 4.0)
            return
        self.start_minigame(
            TimingMeter(
                "FIRE EXTINGUISHER", "",
                steps=[
                    "PULL the safety pin",
                    "AIM at the base of the fire",
                    "SQUEEZE the handle",
                    "SWEEP side to side",
                ],
                speed=0.85, zone=0.26, max_misses=3,
                icon="extinguisher", win_text="FIRE OUT!",
            ),
            on_win=lambda: self._fire_put_out(item),
            on_fail=lambda: self.show_hint("The fire flared up! Remember P.A.S.S. and try again.", 3.5),
        )

    def _fire_put_out(self, item):
        self.fire_out = True
        item["done"] = True
        self.stop_countdown()
        self.show_hint("Fire out! The road is clear. (P.A.S.S.: Pull, Aim, Squeeze, Sweep)", 5.0)

    def update_level(self, dt):
        self.smoke.update(dt)
        self.embers.update(dt)
        if self.completed or self.is_busy():
            return

        in_smoke = self.player.rect.colliderect(self._smoke_rect)
        has_cloth = self.has_item("cloth")
        rate = self.SMOKE_RATE_CLOTH if has_cloth else self.SMOKE_RATE
        change = rate if in_smoke else -self.SMOKE_RECOVER
        self.exposure = max(0.0, min(1.0, self.exposure + change * dt))
        self.set_meter("smoke", "SMOKE", self.exposure, good_high=False)

        if not has_cloth and not self._cough_warned and self.exposure > 0.5:
            self._cough_warned = True
            self.show_hint("You are coughing! Find the DAMP CLOTH and cover your nose.", 4.0)

        if self.exposure >= 1.0:
            self.exposure = 0.0
            self.hurt("You breathed in too much smoke! Cover your nose and mouth.", respawn=True)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_under_player(self, surface):
        r = self.camera.apply(pygame.Rect(self.FIRE_ZONE))
        if self.fire_out:
            draw_charred(surface, r, self._anim_t)
        else:
            draw_flames(surface, r, self._anim_t)

    def draw_over_world(self, surface):
        if not self.fire_out:
            self.embers.draw(surface)
        self.smoke.draw(surface)
        if self.exposure > 0.25:
            self.vignette.draw(surface, (self.exposure - 0.25) / 0.75)

    # ------------------------------------------------------------------
    # Story events
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Kuya Ben":
            return

        if self._ben_helped:
            self.show_hint("Head east to the Town Plaza!", 3.5)
            return

        # Award the assist score once, no matter how often he is talked to.
        if not self._ben_scored:
            self._ben_scored = True
            self.score_system.assist_resident("Kuya Ben")

        # The question opens after his dialogue closes; a wrong answer
        # shows its lesson and asks again, only the safe answer advances.
        self.ask(
            decision_id="fire_smoke_crawl_choice",
            prompt="Dense black smoke is billowing through the narrow intersection. How do you advance?",
            options=[
                {
                    "text": "Drop to hands and knees, cover nose with damp cloth, crawl beneath smoke",
                    "safe": True,
                    "lesson": "Superheated toxic gases rise toward ceilings, leaving breathable air near ground.",
                },
                {
                    "text": "Stand upright and sprint through the heavy smoke cloud with eyes open",
                    "safe": False,
                    "lesson": "Inhaling superheated toxic soot causes instant airway burns and asphyxiation.",
                },
            ],
            on_safe=self._on_smoke_choice_safe,
            retry_hint="Smoke rises. Stay low, cover your nose and mouth.",
        )

    def _on_smoke_choice_safe(self):
        self._ben_helped = True
        if self.current_objective_idx == 0:
            self.complete_objective(0)
        if self.current_objective_idx == 1:
            self.complete_objective(1)
        self.show_hint("Well done! Now evacuate to the Town Plaza on the east side.", 5.0)

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id != "plaza_safe" or self.completed:
            return
        if self.current_objective_idx >= 2:
            self.stop_countdown()
            self.clear_meter("smoke")
            self.score_system.complete_evacuation("ch2_1")
            self.complete_level()
        else:
            self.show_hint("Kuya Ben still needs your help before you evacuate!", 3.5)