"""Prologue - Level 2: Flash Flood Surge (San Isidro).

Location: San Isidro Riverbank & Lowland Bridge.
Disaster: Flash Flood / Orange Rainfall Warning.
Objectives: Reach Mila, cross bridge before inundation, navigate to high ground.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import FlashFloodHazard
from src.config.palette import COLOR_GROUND_SAN_ISIDRO
from src.core.decision_system import Decision


class PrologueLevel2FlashFlood(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="level_2_flash_flood",
            title="Prologue - Level 2: Torrential Surge",
            subtitle="San Isidro - River Breach & Flash Flood",
            disaster_type="Flash Flood (Orange Warning)",
            lesson_source="PAGASA Color-Coded Heavy Rainfall Advisory & DOH Leptospirosis Advisory",
            lesson_text=(
                "Moving floodwaters just 15 centimeters (6 inches) deep can sweep adults away.\n"
                "Never attempt to wade or cross swollen rivers or submerged bridges.\n"
                "Avoid contact with muddy floodwaters to prevent severe Leptospirosis infection.\n"
                "Always seek elevated high ground immediately upon flash flood warning."
            ),
        )
        self._build_world()
        self.hazards.append(FlashFloodHazard(rise_speed=2.5, max_height=80.0))
        self.objectives = [
            "Reach Mila near the riverside house",
            "Cross the wooden bridge to the elevated northern bank",
            "Muster at the community flood safe zone",
        ]

    def _build_world(self):
        self.block_map = BlockMap("San Isidro Riverbank", width=640, height=360, ground_color=COLOR_GROUND_SAN_ISIDRO)
        bm = self.block_map

        # River slicing vertically through the map
        bm.add_water(310, 0, 70, 360)
        # Wooden bridge crossing the river
        bm.add_bridge(310, 160, 70, 34)

        # West bank roads and buildings
        bm.add_road(30, 160, 280, 34)
        bm.add_building("house", "MILA'S HOME", 70, 90, 75, 55)
        bm.add_building("house", "STORAGE", 180, 90, 65, 50)

        # East bank roads and buildings
        bm.add_road(380, 160, 230, 34)
        bm.add_building("shelter", "RIVER SAFE HAVEN", 480, 80, 100, 60)
        bm.add_safe_zone(480, 80, 100, 60, label="HIGH GROUND", trigger_id="flood_safe")

        # Active flood danger zone at low-lying river shoulder
        bm.add_hazard_zone("flood", 250, 240, 190, 100, label="FLASH FLOOD")

        # NPCs
        self.add_npc(
            "mila",
            "Mila",
            (110, 150),
            [
                "The water rose from the creek in less than ten minutes!",
                "I have my baby wrapped in waterproof blankets, but the path is getting muddy.",
                "Please lead us across the bridge before the surge cuts us off!",
            ],
            role="vulnerable",
        )

        self.add_npc(
            "berto",
            "Berto",
            (410, 175),
            [
                "Hurry across! The upstream torrent is carrying uprooted logs!",
                "Do not step into the dark muddy backwash. Head straight up the ridge!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Mila" and self.current_objective_idx == 0:
            self.score_system.assist_resident("Mila")
            self.complete_objective()
        elif npc.name == "Berto" and self.current_objective_idx == 1:
            def on_decide(opt):
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="flood_wade_choice",
                    prompt="Water is spilling onto the bridge ramp. How should the evacuation proceed?",
                    options=[
                        {
                            "text": "Cross immediately while footing is clear, maintaining firm hold on the railing",
                            "safe": True,
                            "lesson": "Pre-planned early river crossing before crest prevents being stranded.",
                        },
                        {
                            "text": "Wade through the deeper downstream mudflat to retrieve abandoned patio furniture",
                            "safe": False,
                            "lesson": "Prioritizing material goods over human life in flash floods leads to drowning.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "flood_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("prologue_2")
            self.complete_level()
