"""Prologue - Tutorial: The First Warning (San Isidro).

Location: San Isidro Coastal Barangay.
Objectives: Learn basic movement, gather 72-hour Go-Bag supplies, and speak with Captain Reyes.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.config.palette import COLOR_GROUND_SAN_ISIDRO
from src.core.decision_system import Decision


class PrologueTutorialLevel(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="tutorial",
            title="Prologue: The First Warning",
            subtitle="San Isidro - Disaster Preparedness Tutorial",
            disaster_type="Normal / Early Advisory",
            lesson_source="NDRRMC National Disaster Risk Reduction & Management Plan (NDRP 2024)",
            lesson_text=(
                "Preparation begins before any storm warning is raised.\n"
                "Every household must maintain a 72-Hour Emergency Go-Bag containing:\n"
                "clean drinking water (1 gal/person/day), non-perishable food, first aid,\n"
                "battery-powered transistor radio, and waterproof identification docs."
            ),
        )
        self._build_world()
        self.objectives = [
            "Collect Go-Bag supplies (Water, Food, First Aid)",
            "Talk to Aling Rosa at the Sari-Sari Store",
            "Report to Captain Reyes at the Barangay Hall",
        ]

    def _build_world(self):
        self.block_map = BlockMap("San Isidro Village", width=640, height=360, ground_color=COLOR_GROUND_SAN_ISIDRO)
        bm = self.block_map

        # Roads and paths
        bm.add_road(60, 160, 520, 30)
        bm.add_road(280, 40, 30, 260)

        # Village Buildings (code-rendered solid rectangles with labels)
        bm.add_building("commercial", "SARI-SARI", 80, 80, 70, 50)
        bm.add_building("shelter", "BRGY HALL", 380, 70, 90, 60)
        bm.add_building("house", "HOUSE 1", 180, 70, 60, 50)
        bm.add_building("house", "HOUSE 2", 120, 220, 70, 50)
        bm.add_building("house", "HOUSE 3", 360, 220, 70, 50)

        # Ocean water boundary at the south
        bm.add_water(0, 320, 640, 40)

        # Natural tree blocks
        for tx in (40, 240, 480, 540):
            bm.add_tree(tx, 40)
            bm.add_tree(tx + 20, 250)

        # Go-Bag items to gather
        bm.add_item("water", "WATER", 100, 140)
        bm.add_item("food", "FOOD", 115, 140)
        bm.add_item("firstaid", "MEDIKIT", 130, 140)
        bm.add_item("flashlight", "TORCH", 145, 140)

        # NPCs
        self.add_npc(
            "aling_rosa",
            "Aling Rosa",
            (105, 135),
            [
                "Magandang umaga! Have you checked your emergency supplies?",
                "The coastal breeze feels unusual today. The tides are shifting fast.",
                "Take these extra rations for your family Go-Bag!",
            ],
            role="resident",
        )

        self.add_npc(
            "captain_reyes",
            "Captain Reyes",
            (420, 135),
            [
                "Attention, youth leader! PAGASA radar indicates an abnormal cyclonic low.",
                "All barangay officials and youth volunteers are placed on Blue Alert.",
                "Inspect our drainage and prepare the community warning sirens!",
            ],
            role="official",
        )

        # Set player spawn
        self.player.pos = pygame.Vector2(100, 175)
        self.player.rect.topleft = (100, 175)

    def on_item_collected(self, item_id: str):
        # Check if all items gathered
        remaining = [it for it in self.block_map.items if not it.collected]
        if not remaining and self.current_objective_idx == 0:
            self.complete_objective()

    def on_npc_interacted(self, npc):
        if npc.name == "Aling Rosa" and self.current_objective_idx == 1:
            self.complete_objective()
        elif npc.name == "Captain Reyes" and self.current_objective_idx == 2:
            # Trigger preparedness decision
            def on_decide(opt):
                self.complete_level()

            self.trigger_decision(
                Decision(
                    decision_id="tutorial_early_prep",
                    prompt="Captain Reyes asks: What is our primary priority upon early advisory?",
                    options=[
                        {
                            "text": "Inspect Go-Bags, review evacuation routes & secure home roofs",
                            "safe": True,
                            "lesson": "Pre-disaster risk assessment and family preparedness save lives.",
                        },
                        {
                            "text": "Wait until heavy rainfall starts before packing anything",
                            "safe": False,
                            "lesson": "Delaying preparation until landfall traps residents in rising hazards.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )
