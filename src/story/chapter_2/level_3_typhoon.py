"""Chapter 2 - Level 3: Urban Typhoon Blackout (Central Town).

Location: Central Town Medical Center & Commercial Avenues.
Disaster: Severe Typhoon (TCWS #3) & Complete Grid Failure.
Objectives: Navigate shattered glass streets, locate Nurse Joy, secure emergency cold chain vaccines.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN
from src.core.decision_system import Decision


class Chapter2Level3Typhoon(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_2",
            level_id="level_3_typhoon",
            title="Chapter 2 - Level 3: Winds Over the City",
            subtitle="Central Town - Urban Debris & Blackout",
            disaster_type="Typhoon (PAGASA TCWS #3)",
            lesson_source="DOST-PAGASA Tropical Cyclone TCWS #3 Guidelines & DOH Cold Chain Preservation Standards",
            lesson_text=(
                "Under TCWS #3 (winds 89-117 km/h), unanchored billboards and roof sheets become airborne missiles.\n"
                "Stay clear of glass curtain-wall buildings; flying debris shatters glass inward.\n"
                "During prolonged blackouts, medical facilities must activate backup generators\n"
                "to maintain the cold chain (+2°C to +8°C) for vaccines, antivenoms, and blood units."
            ),
        )
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=3))
        self.objectives = [
            "Avoid high-rise shattered glass fall zones along the avenue",
            "Reach Nurse Joy at the Municipal Health Center",
            "Switch the emergency vaccine cold-storage unit to auxiliary generator power",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Central Urban Health Center", width=640, height=360, ground_color=COLOR_GROUND_CENTRAL_TOWN)
        bm = self.block_map

        # Wide urban boulevard
        bm.add_road(30, 160, 580, 40)
        bm.add_road(290, 30, 40, 270)

        # Buildings
        bm.add_building("clinic", "HEALTH CENTER", 360, 60, 120, 80)
        bm.add_safe_zone(360, 60, 120, 80, label="SAFE CLINIC", trigger_id="clinic_safe")
        bm.add_building("damaged_house", "HIGHRISE STORE", 60, 50, 100, 90)
        bm.add_building("commercial", "COMMERCIAL PLAZA", 60, 220, 100, 70)

        # Shattered glass debris zone
        bm.add_hazard_zone("landslide", 170, 150, 80, 60, label="FLYING DEBRIS")

        # NPCs
        self.add_npc(
            "nurse_joy",
            "Nurse Joy",
            (410, 150),
            [
                "The power grid tripped when the substation caught gale-force winds!",
                "Our vaccine refrigerator contains hundreds of childhood immunizations and rabies shots!",
                "Help me hook up the portable solar inverter battery to maintain refrigerator temperatures!",
            ],
            role="medical",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Nurse Joy" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Nurse Joy")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()
                self.score_system.complete_evacuation("ch2_3")
                self.complete_level()

            self.trigger_decision(
                Decision(
                    decision_id="urban_blackout_power_choice",
                    prompt="The generator fuel is limited. Which loads should be powered on priority?",
                    options=[
                        {
                            "text": "Priority power strictly for vaccine cold-chain fridge and emergency lights",
                            "safe": True,
                            "lesson": "Preserving life-saving vaccines and basic triage visibility prevents catastrophe.",
                        },
                        {
                            "text": "Plug in hallway entertainment screens and personal phone fast-chargers first",
                            "safe": False,
                            "lesson": "Wasting auxiliary power exhausts fuel, spoiling perishable medications.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )
