"""Prologue - Level 3: Severe Flooding & Evacuation Center (San Isidro).

Location: San Isidro Central Evacuation Center (School Grounds).
Disaster: Severe Flooding / Red Rainfall Warning / Storm Surge.
Objectives: Reach Central Evacuation Center, verify registry, support triage.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import COLOR_GROUND_SAN_ISIDRO
from src.core.decision_system import Decision


class PrologueLevel3SevereFlooding(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="level_3_severe_flooding",
            title="Prologue - Level 3: The Sanctuary",
            subtitle="San Isidro - Red Alert Inundation",
            disaster_type="Severe Flooding (Red Rainfall Warning)",
            lesson_source="NDRRMC Evacuation Camp Coordination & Camp Management (CCCM) Guidelines",
            lesson_text=(
                "Under Red Rainfall Warnings, evacuation is mandatory, not optional.\n"
                "Evacuation centers must maintain separate hygiene facilities,\n"
                "clean drinking water rations, and special protection areas for vulnerable groups.\n"
                "Boil all tap water or drink only sealed relief water during flood emergencies."
            ),
        )
        self._build_world()
        self.hazards.append(SevereFloodingHazard())
        self.objectives = [
            "Navigate flooded streets to San Isidro Central Evacuation Center",
            "Report headcount to Captain Reyes at the Incident Post",
            "Deliver first-aid supplies to Nurse Joy at the Medical Desk",
        ]

    def _build_world(self):
        self.block_map = BlockMap("San Isidro Evacuation Sanctuary", width=640, height=360, ground_color=COLOR_GROUND_SAN_ISIDRO)
        bm = self.block_map

        # Submerged lowland roads
        bm.add_road(30, 180, 580, 40)
        bm.add_hazard_zone("flood", 40, 180, 260, 40, label="DEEP WATER")

        # Evacuation Center Building Complex
        bm.add_building("shelter", "EVACUATION CENTER", 340, 50, 140, 80)
        bm.add_building("clinic", "MEDICAL CLINIC", 500, 50, 100, 70)
        bm.add_safe_zone(340, 50, 260, 110, label="SAFE SANCTUARY", trigger_id="evac_center")

        # Damaged homes submerged in floodwaters
        bm.add_building("damaged_house", "FLOODED HOME A", 70, 70, 70, 60)
        bm.add_building("damaged_house", "FLOODED HOME B", 160, 70, 70, 60)

        # NPCs
        self.add_npc(
            "captain_reyes",
            "Captain Reyes",
            (380, 140),
            [
                "You made it! San Isidro Elementary is holding safe on the high ridge.",
                "Over forty families have already registered safely at the incident desk.",
                "PAGASA reports the storm system is moving inland toward the North West Plateau!",
            ],
            role="official",
        )

        self.add_npc(
            "nurse_joy",
            "Nurse Joy",
            (530, 130),
            [
                "Thank you for bringing these medical packs!",
                "We are treating minor lacerations and giving out doxycycline for flood exposure.",
                "Always remember: boil water for at least three minutes if water lines are flooded!",
            ],
            role="medical",
        )

        self.player.pos = pygame.Vector2(60, 240)
        self.player.rect.topleft = (60, 240)

    def on_npc_interacted(self, npc):
        if npc.name == "Captain Reyes" and self.current_objective_idx == 0:
            self.complete_objective()
        elif npc.name == "Nurse Joy" and self.current_objective_idx == 1:
            def on_decide(opt):
                self.score_system.complete_evacuation("prologue_3")
                self.complete_level()

            self.trigger_decision(
                Decision(
                    decision_id="flood_water_hygiene_choice",
                    prompt="Water supply in the evacuation center is limited. A resident offers tap water from a flooded well:",
                    options=[
                        {
                            "text": "Refuse unboiled flood tap water; distribute sealed bottles and purification tablets",
                            "safe": True,
                            "lesson": "Floods contaminate groundwater with sewage and pathogens like cholera and E. coli.",
                        },
                        {
                            "text": "Drink directly from the tap because the well looks clear to the naked eye",
                            "safe": False,
                            "lesson": "Clear water can still harbor lethal waterborne bacteria and chemical toxins.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )
