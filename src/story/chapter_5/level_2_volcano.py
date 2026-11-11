"""Chapter 5 - Level 2: Explosive Eruption & Ashfall (Volcano Valley).

Location: Volcano Flanks & Evacuation Corridor.
Disaster: Volcanic Eruption (PHIVOLCS Alert Level 5) & Heavy Ashfall.
Objectives: Maneuver through abrasive ashfall, provide N95 protection to Rhea, reach convoy shelter.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import VolcanicEruptionHazard
from src.config.palette import COLOR_GROUND_VALLEY
from src.core.decision_system import Decision


class Chapter5Level2Volcano(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_2_volcano",
            title="Chapter 5 - Level 2: Ashfall Darkness",
            subtitle="Volcano Flanks - Explosive Plume & Pyroclastic Hazard",
            disaster_type="Volcanic Eruption (Alert Level 5)",
            lesson_source="DOST-PHIVOLCS & DOH Volcanic Ashfall Health & Safety Guidelines",
            lesson_text=(
                "Volcanic ash consists of microscopic jagged pulverized rock and glass shards.\n"
                "Never rub irritated eyes; flush with clean water to avoid corneal scratches.\n"
                "Protect lungs with N95 respirators or moist cotton handkerchiefs.\n"
                "Accumulated wet ash weighs over 1,000 kg per cubic meter; scrape roofs to avoid cave-ins."
            ),
        )
        self._build_world()
        self.hazards.append(VolcanicEruptionHazard())
        self.objectives = [
            "Navigate the ash-covered roadway under zero-visibility conditions",
            "Assist Rhea at the roadside waiting shed and provide respiratory cover",
            "Escort Rhea to the pressurized Evacuation Convoy bus",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Volcano Flanks Ash Corridor", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Roadway under thick gray ash
        bm.add_road(30, 160, 580, 40)
        bm.add_hazard_zone("ash", 150, 150, 200, 60, label="THICK ASH DEPOSIT")

        # Structures
        bm.add_building("house", "WAITING SHED", 60, 60, 85, 60)
        bm.add_building("shelter", "CONVOY BUS POST", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="CONVOY POST", trigger_id="convoy_safe")

        # NPCs
        self.add_npc(
            "rhea",
            "Rhea",
            (115, 140),
            [
                "The sky turned completely pitch black in the middle of the afternoon!",
                "The gray sand is stinging my eyes and throat! It smells like rotten eggs!",
                "Thank you for putting this wet cloth over my nose! Let's get to the bus!",
            ],
            role="vulnerable",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Rhea" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Rhea")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="ashfall_health_choice",
                    prompt="Heavy gritty volcanic ash is falling like snow. How do you protect eyes and lungs?",
                    options=[
                        {
                            "text": "Wear wrap-around goggles and an N95 mask; seal collar and cuffs",
                            "safe": True,
                            "lesson": "Proper sealing prevents abrasive silica glass shards from lacerating lung alveoli.",
                        },
                        {
                            "text": "Rub eyes vigorously and keep looking straight up into the ash cloud",
                            "safe": False,
                            "lesson": "Rubbing volcanic ash into eyes causes severe corneal lacerations and blindness.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "convoy_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch5_2")
            self.complete_level()
