"""Chapter 2 - Level 4: Urban Flash Flood & PWD Rescue (Central Town).

Location: Central Town Lowland Residential Avenue.
Disaster: Urban Canal Overflow & Severe Street Inundation.
Objectives: Avoid submerged open manholes, assist Liza, reach elevated ramp shelter.

Pixel-game layer:
  * Rising pixel water with a WATER meter; deep water slows you down.
  * Hidden open drains: pick up the WALKING STICK and probe to reveal them.
  * Pickups: WALKING STICK and Liza's GO-BAG.
  * Mini-game: clear the debris off the wheelchair ramp (mash SPACE).
  * Pressure: "flood peak" countdown that sweeps you back.
"""

import pygame
from src.story.base_level import (
    BaseLevel,
    ParticleField,
    Mash,
    draw_water,
    draw_drain,
    draw_wading_ripples,
)
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import FlashFloodHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN


class Chapter2Level4FlashFlood(BaseLevel):
    # Layout constants (world coordinates)
    PLAYER_START = (50, 175)
    CHECKPOINT = (140, 176)
    ROAD_RECT = (30, 160, 580, 45)
    SEWER_ZONE = (180, 160, 150, 45)
    DRAINS = [(205, 176), (252, 190), (302, 172)]   # open manholes (centres)
    DEBRIS_RECT = (232, 106, 24, 16)
    DEBRIS_COLOR = (130, 96, 60)
    STICK_POS = (92, 218)
    GOBAG_POS = (152, 150)

    FLOOD_SECONDS = 150
    FLOOD_REPEAT_SECONDS = 60
    FULL_FLOOD_TIME = 150.0
    PROBE_RADIUS = 46

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_2",
            level_id="level_4_flash_flood",
            title="Chapter 2 - Level 4: The Submerged Avenue",
            subtitle="Central Town - Urban Inundation & Accessible Evacuation",
            disaster_type="Urban Flash Flood (Extreme Hazard)",
            lesson_source="DSWD & NCDA Disability-Inclusive Disaster Risk Reduction and Management (DIDRRM) Standards",
            lesson_text=(
                "Urban floods dislodge heavy manhole covers, creating invisible underwater death traps.\n"
                "Never walk through dark water without using a walking stick to probe depth and openings ahead.\n"
                "Evacuation plans must include Persons with Disabilities (PWDs), ensuring wheelchair\n"
                "ramps are cleared of debris and assistive mobility devices are kept dry."
            ),
        )
        # Progress flags (set before the world is built)
        self._liza_scored = False   # assist score is awarded only once
        self._liza_helped = False   # ramp question answered safely
        self._gobag_thanked = False
        self.ramp_cleared = False
        self.probed = set()         # indices of drains the stick has revealed
        self._flood_t = 0.0
        self.flood = 0.0            # 0..1 water depth for drawing / slowing
        self._base_speed = getattr(self.player, "speed", None)

        self.rain = ParticleField("rain", seed=6, count=70)

        self._build_world()
        self.hazards.append(FlashFloodHazard(rise_speed=3.0, max_height=85.0))
        self.objectives = [
            "You probe the flooded road near the manholes",
            "You assist Liza at her residence",
            "You clear ramp debris at the Civic Center",
        ]
        # One guide target per active step: stick/drain, Liza, then the ramp.
        self.guide_points = [
            lambda: (
                self.guide_pickup("stick")() if not self.has_item("stick")
                else next((self.DRAINS[i] for i in range(len(self.DRAINS))
                           if i not in self.probed), self.DRAINS[0])
            ),
            self.guide_npc("Liza"),
            self.guide_interactable("ramp_debris"),
        ]
        self.set_checkpoint(self.CHECKPOINT)
        self.set_meter("water", "WATER", 0.0, good_high=False)
        self.start_countdown(self.FLOOD_SECONDS, "FLOOD PEAK", on_expire=self._flood_peak)
        self.show_hint("Grab the WALKING STICK to probe for open drains, then find Liza.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Central Town Lowland Avenue",
            width=640,
            height=360,
            ground_color=COLOR_GROUND_CENTRAL_TOWN,
        )
        bm = self.block_map

        # Flooded roadway
        bm.add_road(*self.ROAD_RECT)
        bm.add_hazard_zone("flood", *self.SEWER_ZONE, label="SUBMERGED SEWER")
        self.watch_zone(self.SEWER_ZONE, self._warn_sewer)

        # Elevated accessible ramp path
        bm.add_road(180, 100, 260, 30)

        # Buildings
        bm.add_building("house", "LIZA'S RESIDENCE", 70, 70, 85, 65)
        bm.add_building("shelter", "CIVIC CENTER", 460, 60, 120, 80)
        bm.add_safe_zone(460, 60, 120, 80, label="CIVIC CENTER", trigger_id="civic_safe")

        # Debris blocking the wheelchair ramp (clear it with SPACE)
        self.add_interactable(
            "ramp_debris", "RAMP DEBRIS", self.DEBRIS_RECT, self.DEBRIS_COLOR,
            on_interact=self._clear_ramp,
        )

        # Collectibles
        self.add_pickup("stick", "WALKING STICK", self.STICK_POS, "stick")
        self.add_pickup("gobag", "LIZA'S GO-BAG", self.GOBAG_POS, "gobag")

        # NPCs
        self.add_npc(
            "liza",
            "Liza",
            (115, 140),
            [
                "The water is already creeping over my front doorway threshold!",
                "My wheelchair cannot push through deep muddy currents without help.",
                "Thank you for coming! The elevated pedestrian ramp leads safely up to the Civic Center!",
            ],
            role="vulnerable",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Flood, drains and the peak timer
    # ------------------------------------------------------------------
    def _warn_sewer(self):
        self.show_hint("Open drains under the water! Probe with a stick or take the ramp.", 3.5)

    def _water_rect(self):
        # Water rises from the south (y=360 upwards towards y=140)
        h = int(60 + 160 * self.flood)
        top = max(140, 360 - h)
        return pygame.Rect(20, top, 600, 360 - top)

    def _drain_rect(self, cx, cy):
        return pygame.Rect(cx - 8, cy - 4, 16, 8)

    def update_level(self, dt):
        self.rain.update(dt)
        if self.completed or self.is_busy():
            return

        # Water keeps rising while the player acts
        self._flood_t += dt
        self.flood = min(1.0, self._flood_t / self.FULL_FLOOD_TIME)
        self.set_meter("water", "WATER", self.flood, good_high=False)

        # Deep water slows the player down
        if self._base_speed is not None and hasattr(self.player, "speed"):
            in_water = self.player.rect.colliderect(self._water_rect())
            self.player.speed = self._base_speed * (0.65 if (in_water and self.flood > 0.35) else 1.0)

        # Probing with the stick reveals nearby drains; falling in hurts
        pcx, pcy = self.player.rect.center
        for i, (cx, cy) in enumerate(self.DRAINS):
            if self.has_item("stick") and i not in self.probed:
                if (pcx - cx) ** 2 + (pcy - cy) ** 2 <= self.PROBE_RADIUS ** 2:
                    if i not in self.probed:
                        self.probed.add(i)
                        self.show_hint("Probe! Your stick found an open drain. Go around it.", 3.0)
                        if self.current_objective_idx == 0:
                            self.complete_objective(0)
            if self.player.rect.colliderect(self._drain_rect(cx, cy)):
                self.hurt(
                    "You fell into an open drain! Always probe the water with a stick.",
                    respawn=True,
                )

    def _flood_peak(self):
        if self.completed:
            return
        self.hurt("The flood peaked! The current swept you back.", respawn=True)
        self._flood_t = max(0.0, self._flood_t - 30.0)  # water recedes a little
        self.start_countdown(self.FLOOD_REPEAT_SECONDS, "FLOOD PEAK", on_expire=self._flood_peak)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_over_world(self, surface):
        # Water covers the road (and hides any drain you have not probed)
        wr = self.camera.apply(self._water_rect())
        draw_water(surface, wr, self._anim_t, alpha=int(90 + 100 * self.flood),
                   shore=True, foam=True, depth=True)

        # Player wading ripples when wading in water
        if self.player.rect.colliderect(self._water_rect()):
            draw_wading_ripples(surface, self.camera, self.player.rect, self._anim_t)

        # Probed drains are marked on top of the water so they stay visible
        for i, (cx, cy) in enumerate(self.DRAINS):
            if i in self.probed:
                sx, sy = self.camera.apply(pygame.Rect(cx, cy, 1, 1)).topleft
                draw_drain(surface, (sx, sy), False, self._anim_t)
        self.rain.draw(surface)

    # ------------------------------------------------------------------
    # Story events
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Liza":
            return
        if not self.require_step(1, "Finish probing the road first"):
            return

        # Thank the player once for bringing the go-bag.
        if self.has_item("gobag") and not self._gobag_thanked:
            self._gobag_thanked = True
            self.start_dialogue("Liza", [
                "My go-bag! You found my medicine and documents. Thank you!",
            ] + list(npc.dialogue))

        if self._liza_helped:
            self.show_hint("Clear the RAMP DEBRIS, then take the ramp to the Civic Center!", 4.0)
            return

        # Award the assist score once, no matter how often she is talked to.
        if not self._liza_scored:
            self._liza_scored = True
            self.score_system.assist_resident("Liza")

        # The question opens after her dialogue closes; only the safe answer advances.
        self.ask(
            decision_id="pwd_evac_ramp_choice",
            prompt="Water is rising along the main street. How do you escort Liza's wheelchair?",
            options=[
                {
                    "text": "Wheel Liza up the high concrete pedestrian ramp away from submerged gutters",
                    "safe": True,
                    "lesson": "Utilizing designated elevated access ramps prevents wheelchair submersion.",
                },
                {
                    "text": "Push the wheelchair straight through knee-deep brown water in the center road",
                    "safe": False,
                    "lesson": "Submerged missing drain covers or currents can topple wheelchairs instantly.",
                },
            ],
            on_safe=self._on_ramp_choice_safe,
            retry_hint="Water hides open drains. Use the elevated ramp.",
        )

    def _on_ramp_choice_safe(self):
        self._liza_helped = True
        if self.current_objective_idx == 1:
            self.complete_objective(1)
        self.show_hint("Clear the RAMP DEBRIS so Liza's wheelchair can pass.", 5.0)

    def _clear_ramp(self, item):
        if item["done"]:
            return
        if not self.require_step(2, "Finish helping Liza first"):
            return
        self.start_minigame(
            Mash(
                "CLEAR THE RAMP", "Mash SPACE to push the debris off the wheelchair ramp!",
                target=16, decay=2.2, time_limit=8.0,
                icon="ramp", win_text="RAMP CLEAR!",
            ),
            on_win=lambda: self._ramp_cleared(item),
            on_fail=lambda: self.show_hint("Still blocked! Try again, quickly.", 3.0),
        )

    def _ramp_cleared(self, item):
        self.ramp_cleared = True
        item["done"] = True
        self.show_hint("The ramp is clear! Now escort Liza to the Civic Center.", 4.5)

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id != "civic_safe" or self.completed:
            return
        if not self.require_step(2, "Finish helping Liza first"):
            return
        if not self.ramp_cleared:
            self.show_hint("The wheelchair ramp is blocked! Clear the debris first.", 3.5)
        else:
            self.stop_countdown()
            self.clear_meter("water")
            self.score_system.complete_evacuation("ch2_4")
            self.complete_level()