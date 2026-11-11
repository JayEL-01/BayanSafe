"""Chapter 1 - Level 1: Highland Tremor (North West Plateau).

Location: North West Highland Plateau (Mount Dayaw Foothills).
Disaster: Earthquake (PHIVOLCS PEIS Intensity VI - Very Strong).
Objectives: Execute Duck-Cover-Hold, guide Sari to clear open ground.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.config.palette import COLOR_GROUND_PLATEAU
from src.core.decision_system import Decision


class Chapter1Level1Earthquake(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_1_earthquake",
            title="Chapter 1 - Level 1: The Shaking Highland",
            subtitle="North West Plateau - Tectonic Tremor",
            disaster_type="Earthquake (PEIS Intensity VI)",
            lesson_source="DOST-PHIVOLCS Earthquake Preparedness Guide & Duck-Cover-Hold Protocol",
            lesson_text=(
                "During an earthquake, immediately DROP to hands and knees,\n"
                "COVER your head and neck under a sturdy table or desk,\n"
                "and HOLD ON until the violent shaking completely ceases.\n"
                "Once shaking stops, evacuate to an open field away from facades and power poles."
            ),
        )
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=6))
        self.objectives = [
            "Execute Duck-Cover-Hold protocol during tremors",
            "Assist Sari near the plateau schoolhouse",
            "Muster at the wide open football field away from structures",
        ]

    def _build_world(self):
        self.block_map = BlockMap("North West Plateau - Village", width=640, height=360, ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # Plateau paths and trails
        bm.add_path(50, 160, 540, 36)
        bm.add_path(260, 40, 36, 260)

        # Plateau school and masonry buildings
        bm.add_building("house", "PLATEAU SCHOOL", 70, 60, 95, 65)
        bm.add_building("damaged_house", "DAMAGED BARN", 200, 60, 80, 60)
        bm.add_building("house", "FARM HOUSE", 380, 60, 75, 55)

        # Wide open field (safe zone)
        bm.add_safe_zone(380, 200, 180, 110, label="OPEN RECREATION FIELD", trigger_id="open_field")

        # NPCs
        self.add_npc(
            "sari",
            "Sari",
            (115, 135),
            [
                "The blackboard was shaking so loudly! We were reading our textbooks when it hit!",
                "Our teacher told us to protect our heads under our desks.",
                "Can you help me get to the open grass field? I want to wait for my family there.",
            ],
            role="vulnerable",
        )

        self.player.pos = pygame.Vector2(80, 175)
        self.player.rect.topleft = (80, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Sari" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Sari")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="earthquake_cover_choice",
                    prompt="Aftershocks continue to rumble. How do you lead Sari out of the classroom?",
                    options=[
                        {
                            "text": "Cover heads with bags, proceed cautiously in single file to the open field",
                            "safe": True,
                            "lesson": "Protecting the head from falling glass, masonry, and lights is paramount.",
                        },
                        {
                            "text": "Run wildly down the hallway while looking up at dangling ceiling fans",
                            "safe": False,
                            "lesson": "Running frantically during tremors causes stampedes and falls.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "open_field" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch1_1")
            self.complete_level()
