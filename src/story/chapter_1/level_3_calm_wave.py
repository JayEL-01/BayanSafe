"""Chapter 1 - Level 3: The Calm Before the Wave (North West Plateau).

Location: Plateau Coastal Overlook.
Disaster: Natural Pre-Tsunami Anomaly (Sea Water Drawback).
Objectives: Observe sea drawback, warn Tatay Pio and residents, sound emergency siren with Berto.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.config.palette import COLOR_GROUND_PLATEAU
from src.core.decision_system import Decision


class Chapter1Level3CalmWave(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_3_calm_wave",
            title="Chapter 1 - Level 3: The Sea Recedes",
            subtitle="North West Plateau - The Calm Before the Wave",
            disaster_type="Tsunami Natural Warning (Rapid Drawback)",
            lesson_source="DOST-PHIVOLCS Tsunami Preparedness: Recognize the 3 Natural Signs (Shake, Drop, Roar)",
            lesson_text=(
                "If you feel a strong earthquake near the coast and notice:\n"
                "1. Rapid receding of sea water exposing the ocean floor and corals,\n"
                "2. A loud roaring sound like a jet aircraft approaching from the sea,\n"
                "DO NOT go down to the shore to pick up flopping fish or take photos!\n"
                "RUN IMMEDIATELY to high ground (at least 30 meters above sea level) inland."
            ),
        )
        self._build_world()
        self.objectives = [
            "Inspect the coastal overlook view of the bay",
            "Stop Tatay Pio from descending to the dry reef",
            "Sound the community evacuation siren at Berto's outpost",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Plateau Coastal Overlook", width=640, height=360, ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # High overlook ridge paths
        bm.add_path(40, 160, 560, 36)
        bm.add_path(420, 50, 36, 250)

        # Buildings
        bm.add_building("commercial", "VIEWPOINT SHED", 70, 70, 75, 55)
        bm.add_building("shelter", "COMMUNITY SIREN POST", 400, 60, 90, 65)

        # South sea waters showing exposed dry sea bed (cyan/blue hazard strip)
        bm.add_water(0, 310, 640, 50)
        bm.add_hazard_zone("tsunami", 0, 270, 640, 40, label="EXPOSED DRY SEA BED")

        # NPCs
        self.add_npc(
            "tatay_pio",
            "Tatay Pio",
            (110, 140),
            [
                "Look down at the bay! The sea pulled back almost half a kilometer in two minutes!",
                "Look at all those fish flopping on the dry coral reef! Some young folks want to run down with buckets!",
                "In my sixty years of fishing, I have never seen the ocean empty like this...",
            ],
            role="resident",
        )

        self.add_npc(
            "berto",
            "Berto",
            (430, 135),
            [
                "Hold the line! That is the classic precursor to a tsunami wall!",
                "We must activate the mechanical siren and order an immediate vertical evacuation!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(60, 175)
        self.player.rect.topleft = (60, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Tatay Pio" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Tatay Pio")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="tsunami_drawback_choice",
                    prompt="Residents are staring curiously at the receded ocean floor. What is your urgent command?",
                    options=[
                        {
                            "text": "Shout urgent warning: 'Tsunami incoming! Run to the mountain top immediately!'",
                            "safe": True,
                            "lesson": "Natural warning signs are immediate cues for self-evacuation before sirens.",
                        },
                        {
                            "text": "Encourage people to gather fish and take photos before the water returns",
                            "safe": False,
                            "lesson": "Curiosity near receding coasts is the #1 cause of preventable tsunami fatalities.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )
        elif npc.name == "Berto" and self.current_objective_idx >= 2:
            self.complete_level()
