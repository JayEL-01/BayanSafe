"""Chapter 2 - Level 2: Earthquake & Rumor Control (Central Town).

Location: Central Town Municipal Hall.
Disaster: Aftershocks & Disinformation Infodemic.
Objectives: Evacuate Town Hall safely, verify disaster bulletins with Mayor Cruz, broadcast truth.

Pixel-game layer:
  * Pickups: HARD HAT (protects from debris) and MEGAPHONE (easier broadcast).
  * Aftershocks: warning, then hold still ("Drop, Cover and Hold On") or stumble.
  * Mini-game: tune and broadcast the verified bulletin on the radio.
  * Ground cracks and falling dust grow with every aftershock.
"""

import random

import pygame
from src.story.base_level import (
    BaseLevel, ParticleField, Vignette, TimingMeter, draw_cracks,
)
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN


class Chapter2Level2Earthquake(BaseLevel):
    # Layout constants (world coordinates)
    PLAYER_START = (70, 175)
    COURTYARD_ZONE = (270, 150, 100, 70)
    COURTYARD_COLOR = (80, 170, 120)
    RADIO_RECT = (492, 98, 24, 18)
    RADIO_COLOR = (200, 60, 60)
    HARDHAT_POS = (96, 148)
    MEGAPHONE_POS = (440, 232)

    # Ground cracks revealed one more per aftershock (world points)
    CRACKS = [
        [(180, 130), (196, 142), (190, 154), (210, 166), (205, 180)],
        [(250, 215), (266, 204), (262, 192), (282, 184), (296, 170)],
        [(120, 135), (110, 150), (126, 160), (118, 176), (134, 188)],
    ]

    # Aftershock timing (seconds)
    FIRST_QUAKE = 8.0
    QUAKE_GAP = (14.0, 20.0)
    WARN_TIME = 1.6
    QUAKE_TIME = 2.4

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_2",
            level_id="level_2_earthquake",
            title="Chapter 2 - Level 2: Tremors and Truth",
            subtitle="Central Town Hall - Aftershocks & Rumor Control",
            disaster_type="Aftershocks & Infodemic Panic",
            lesson_source="NDRRMC Disaster Information Management & Public Advisory Guidelines",
            lesson_text=(
                "During crises, unverified rumors and sensationalized social media posts\n"
                "spread faster than hazards, inciting lethal stampedes and misdirected resources.\n"
                "Rely strictly on official government agencies: NDRRMC, PAGASA, PHIVOLCS, and LGU.\n"
                "Never forward emergency alerts unless certified by verified public PIO channels."
            ),
        )
        # Progress flags (set before the world is built)
        self._courtyard_item = None
        self._rumor_resolved = False
        self._rnd = random.Random(21)

        # Aftershock state machine: calm -> warn -> quake -> calm
        self._quake_state = "calm"
        self._quake_timer = self.FIRST_QUAKE
        self._quake_anchor = (0, 0)
        self._stumbled = False
        self.quake_count = 0

        self.dust = ParticleField("dust", seed=3, count=16)
        self.quake_dust = ParticleField("dust", seed=9, count=70)
        self.warn_vignette = Vignette(color=(150, 20, 10), max_alpha=140)

        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=5))
        self.objectives = [
            "You evacuate Town Hall to the outdoor assembly yard",
            "Consult Mayor Cruz at the Incident Command Post",
            "You halt rumors at the Command Post radio",
        ]
        self.guide_points = [
            (
                self.COURTYARD_ZONE[0] + self.COURTYARD_ZONE[2] // 2,
                self.COURTYARD_ZONE[1] + self.COURTYARD_ZONE[3] // 2,
            ),
            self.guide_npc("Mayor Cruz"),
            self.guide_interactable("radio"),
        ]
        self.set_checkpoint(self.PLAYER_START)
        self.show_hint("The Town Hall is cracked! Reach the green assembly courtyard.", 6.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Central Municipal Compound",
            width=640,
            height=360,
            ground_color=COLOR_GROUND_CENTRAL_TOWN,
        )
        bm = self.block_map

        # Paved roads and courtyards
        bm.add_road(30, 160, 580, 40)
        bm.add_road(300, 30, 40, 270)

        # Municipal buildings
        bm.add_building("damaged_house", "TOWN HALL (CRACKED)", 60, 60, 110, 70)
        bm.add_building("shelter", "COMMAND DESK", 360, 60, 120, 70)
        bm.add_safe_zone(360, 60, 120, 70, label="INCIDENT POST", trigger_id="command_post")

        # Assembly courtyard: translucent zone the player must reach first
        self._courtyard_item = self.add_interactable(
            "courtyard",
            "ASSEMBLY COURTYARD",
            self.COURTYARD_ZONE,
            self.COURTYARD_COLOR,
            prompt=False,
            alpha=70,
        )
        self.watch_zone(self.COURTYARD_ZONE, self._on_courtyard_reached)

        # Radio at the command desk: used for the final broadcast
        self.add_interactable(
            "radio", "RADIO", self.RADIO_RECT, self.RADIO_COLOR,
            on_interact=self._use_radio,
        )

        # Collectibles
        self.add_pickup("hardhat", "HARD HAT", self.HARDHAT_POS, "hardhat")
        self.add_pickup("megaphone", "MEGAPHONE", self.MEGAPHONE_POS, "megaphone")

        # NPCs
        self.add_npc(
            "mayor_cruz",
            "Mayor Cruz",
            (400, 140),
            [
                "Thank you for keeping your composure during these violent aftershocks!",
                "Panic is threatening our town: people are circulating fake voice notes online",
                "claiming a secret chemical cloud has leaked, causing crowds to mob the bridges!",
                "We must counteract these lies with verified civil defense radio broadcasts immediately!",
            ],
            role="official",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Aftershocks
    # ------------------------------------------------------------------
    def update_level(self, dt):
        self.dust.update(dt)
        if self._quake_state == "quake":
            self.quake_dust.update(dt)
        if self.completed or self.is_busy():
            return

        self._quake_timer -= dt
        if self._quake_state == "calm" and self._quake_timer <= 0:
            self._quake_state = "warn"
            self._quake_timer = self.WARN_TIME
            self.show_hint("AFTERSHOCK! Drop, Cover and Hold On. Do not move!", 2.4)

        elif self._quake_state == "warn" and self._quake_timer <= 0:
            self._quake_state = "quake"
            self._quake_timer = self.QUAKE_TIME
            self._quake_anchor = self.player.rect.center
            self._stumbled = False
            self.quake_count += 1

        elif self._quake_state == "quake":
            self._jolt = 0.3  # keep the screen shaking
            ax, ay = self._quake_anchor
            px, py = self.player.rect.center
            moved = abs(px - ax) + abs(py - ay) > 2
            if moved and not self._stumbled:
                self._stumbled = True
                if self.has_item("hardhat"):
                    self.show_hint("Your HARD HAT saved you! Next time Drop, Cover, Hold On.", 3.5)
                else:
                    self.hurt("Falling debris hit you! Stay still: Drop, Cover, Hold On.")
            if self._quake_timer <= 0:
                self._quake_state = "calm"
                self._quake_timer = self._rnd.uniform(*self.QUAKE_GAP)
                if not self._stumbled:
                    self.show_hint("Well done! You held still: Drop, Cover and Hold On.", 3.5)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_under_player(self, surface):
        n = min(self.quake_count, len(self.CRACKS))
        if n:
            draw_cracks(surface, self.camera, self.CRACKS[:n])

    def draw_over_world(self, surface):
        self.dust.draw(surface)
        if self._quake_state == "quake":
            self.quake_dust.draw(surface)
        elif self._quake_state == "warn":
            blink = 0.5 + 0.5 * (1 if int(self._anim_t * 6) % 2 == 0 else 0)
            self.warn_vignette.draw(surface, blink)

    # ------------------------------------------------------------------
    # Story events
    # ------------------------------------------------------------------
    def _on_courtyard_reached(self):
        if self.current_objective_idx != 0:
            return
        self.complete_objective()
        if self._courtyard_item is not None:
            self._courtyard_item["done"] = True
        self.show_hint("Safe outside! Report to Mayor Cruz at the Command Desk.", 5.0)

    def on_npc_interacted(self, npc):
        if npc.name != "Mayor Cruz":
            return

        if self._rumor_resolved:
            self.show_hint("Use the RADIO at the Command Desk to broadcast the truth.", 4.0)
            return

        if self.current_objective_idx < 1:
            self.show_hint("Evacuate the Town Hall to the assembly courtyard first.", 4.5)
            return

        # Opens after the mayor's dialogue closes; only the safe answer advances.
        self.ask(
            decision_id="rumor_control_choice",
            prompt="A panicked crowd approaches shouting about an anonymous SMS alert. How do you respond?",
            options=[
                {
                    "text": "Direct everyone to official MDRRMC megaphone updates and radio frequencies",
                    "safe": True,
                    "lesson": "Accurate verified information quells panic and directs aid where needed.",
                },
                {
                    "text": "Forward the alarming anonymous message to every contact on your phone",
                    "safe": False,
                    "lesson": "Spreading unverified rumors overburdens emergency lines and triggers stampedes.",
                },
            ],
            on_safe=self._on_rumor_safe,
            retry_hint="Only share verified information from official channels.",
        )

    def _on_rumor_safe(self):
        self._rumor_resolved = True
        self.complete_objective()  # consult Mayor Cruz
        self.show_hint("Now broadcast the truth: use the RADIO next to the Command Desk.", 5.0)

    def _use_radio(self, item):
        if item["done"]:
            return
        if self.current_objective_idx < 2:
            self.show_hint("Talk to Mayor Cruz first. He has the verified bulletin.", 4.0)
            return

        boosted = self.has_item("megaphone")
        self.start_minigame(
            TimingMeter(
                "RADIO BROADCAST", "",
                steps=[
                    "Tune to the official MDRRMC frequency",
                    "Verify the bulletin with PHIVOLCS",
                    "Broadcast the verified update",
                ],
                speed=0.9,
                zone=0.34 if boosted else 0.22,
                max_misses=4 if boosted else 3,
                icon="radio", win_text="BROADCAST SENT!",
            ),
            on_win=lambda: self._broadcast_done(item),
            on_fail=lambda: self.show_hint(
                "Signal lost! Try again." if boosted else
                "Signal lost! A MEGAPHONE would make this easier. Try again.", 3.5),
        )

    def _broadcast_done(self, item):
        item["done"] = True
        self.score_system.complete_evacuation("ch2_2")
        self.complete_objective()  # halt the rumors -> completes the level
        if not self.completed:
            self.complete_level()