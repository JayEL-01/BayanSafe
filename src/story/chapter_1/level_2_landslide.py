"""Chapter 1 - Level 2: Landslide Threat (North West Plateau).

Location: Highland Ridgeline & Terraces.
Disaster: Rain-Induced Landslide & Slope Collapse.
Objectives: Avoid fissure zones, reach Mang Lito, escort across bedrock ridge.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import LandslideHazard
from src.config.palette import COLOR_GROUND_PLATEAU
from src.core.decision_system import Decision


class Chapter1Level2Landslide(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_2_landslide",
            title="Chapter 1 - Level 2: The Sliding Ridge",
            subtitle="North West Plateau - Mountain Slope Failure",
            disaster_type="Rain-Induced Landslide Hazard",
            lesson_source="DENR-MGB Geohazard Assessment & Slope Stability Guidelines",
            lesson_text=(
                "Key warning signs of an impending landslide include:\n"
                "new tension cracks in the ground, leaning utility poles or trees,\n"
                "fences pulling apart, and sudden muddying of clear spring waters.\n"
                "Never cross a freshly collapsed mudslide; secondary slides follow rapidly."
            ),
        )
        self._build_world()
        self.hazards.append(LandslideHazard())
        self.objectives = [
            "Inspect slope tension cracks along the lower trail",
            "Find Mang Lito cut off near the terraced field",
            "Escort him to the firm bedrock ridge safe zone",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Plateau Mountain Slope", width=640, height=360, ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # Main ridge trails
        bm.add_path(40, 160, 560, 32)
        # Blocked lower trail with massive landslide debris
        bm.add_hazard_zone("landslide", 220, 150, 120, 50, label="ROCKFALL DEBRIS")

        # Alternate high bedrock trail
        bm.add_path(180, 70, 240, 26)

        # Farm huts
        bm.add_building("house", "MANG LITO'S BARN", 80, 80, 75, 55)
        bm.add_building("damaged_house", "COLLAPSED SHED", 360, 220, 80, 60)

        # Bedrock safe zone
        bm.add_safe_zone(460, 60, 120, 80, label="BEDROCK RIDGE", trigger_id="bedrock_safe")

        # NPCs
        self.add_npc(
            "mang_lito",
            "Mang Lito",
            (110, 140),
            [
                "The soil was groaning before sunrise! Half my banana terrace slid down into the gorge!",
                "The main dirt road is buried under three meters of mud and heavy boulders.",
                "Is the upper bedrock trail still solid? Let's take that path to safety!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(60, 175)
        self.player.rect.topleft = (60, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Mang Lito" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Mang Lito")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="landslide_route_choice",
                    prompt="The lower path is covered with active sliding mud. What is the safest route?",
                    options=[
                        {
                            "text": "Turn back and climb the upper rocky bedrock ridge path",
                            "safe": True,
                            "lesson": "Bedrock foundations resist rainfall saturation far better than steep clay slopes.",
                        },
                        {
                            "text": "Try climbing over the wet mudflow debris while rocks are still tumbling",
                            "safe": False,
                            "lesson": "Active mudflows possess intense suction and can trigger fatal secondary collapses.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "bedrock_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch1_2")
            self.complete_level()
