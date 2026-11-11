"""Chapter 2 - Level 1: Flash Fire (Central Town).

Location: Central Town Commercial District.
Disaster: Flash Fire Outbreak & Dense Toxic Smoke.
Objectives: Stay low, avoid fire zones, locate Kuya Ben, reach clear street plaza.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import FlashFireHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN
from src.core.decision_system import Decision


class Chapter2Level1Fire(BaseLevel):
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
        self._build_world()
        self.hazards.append(FlashFireHazard())
        self.objectives = [
            "Navigate the smoke-filled commercial alleyways",
            "Assist Kuya Ben whose jeepney was trapped near the pharmacy",
            "Evacuate to the wide concrete Town Plaza assembly zone",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Central Town Commercial District", width=640, height=360, ground_color=COLOR_GROUND_CENTRAL_TOWN)
        bm = self.block_map

        # Paved urban street grid
        bm.add_road(30, 160, 580, 40)
        bm.add_road(280, 30, 40, 270)

        # Commercial shop blocks
        bm.add_building("commercial", "PHARMACY", 60, 60, 85, 60)
        bm.add_building("commercial", "BAKERY", 170, 60, 80, 60)
        bm.add_building("commercial", "GROCERY", 350, 60, 90, 60)
        bm.add_building("commercial", "HARDWARE", 60, 220, 85, 60)

        # Active fire hazard zones (red/orange blocks)
        bm.add_hazard_zone("fire", 160, 150, 90, 60, label="FLASH FIRE")

        # Wide open town plaza safe zone
        bm.add_safe_zone(470, 150, 130, 110, label="TOWN PLAZA", trigger_id="plaza_safe")

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

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Kuya Ben" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Kuya Ben")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
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
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "plaza_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch2_1")
            self.complete_level()
