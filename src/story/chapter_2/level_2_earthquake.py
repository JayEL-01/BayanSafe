"""Chapter 2 - Level 2: Earthquake & Rumor Control (Central Town).

Location: Central Town Municipal Hall.
Disaster: Aftershocks & Disinformation Infodemic.
Objectives: Evacuate Town Hall safely, verify disaster bulletins with Mayor Cruz, broadcast truth.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN
from src.core.decision_system import Decision


class Chapter2Level2Earthquake(BaseLevel):
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
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=5))
        self.objectives = [
            "Evacuate cracked Municipal Hall to the exterior assembly courtyard",
            "Consult Mayor Cruz at the Incident Command Post",
            "Halt the spread of unverified viral rumors inciting panic",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Central Municipal Compound", width=640, height=360, ground_color=COLOR_GROUND_CENTRAL_TOWN)
        bm = self.block_map

        # Paved roads and courtyards
        bm.add_road(30, 160, 580, 40)
        bm.add_road(300, 30, 40, 270)

        # Municipal buildings
        bm.add_building("damaged_house", "TOWN HALL (CRACKED)", 60, 60, 110, 70)
        bm.add_building("shelter", "COMMAND DESK", 360, 60, 120, 70)
        bm.add_safe_zone(360, 60, 120, 70, label="INCIDENT POST", trigger_id="command_post")

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

        self.player.pos = pygame.Vector2(70, 175)
        self.player.rect.topleft = (70, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Mayor Cruz" and self.current_objective_idx <= 1:
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()
                self.score_system.complete_evacuation("ch2_2")
                self.complete_level()

            self.trigger_decision(
                Decision(
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
                    on_resolved=on_decide,
                )
            )
