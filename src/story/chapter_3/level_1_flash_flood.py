"""Chapter 3 - Level 1: Tidal Inundation (Harbor).

Location: Harbor Docks & Pierfront.
Disaster: Flash Flood & Coastal Tidal Backflow.
Objectives: Avoid slipping off wet docks, assist Tito Ramon with cargo lines, reach harbor office.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import FlashFloodHazard
from src.config.palette import COLOR_GROUND_HARBOR
from src.core.decision_system import Decision


class Chapter3Level1FlashFlood(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_1_flash_flood",
            title="Chapter 3 - Level 1: The Flooded Pier",
            subtitle="Harbor Docks - Tidal Surge & River Discharge",
            disaster_type="Harbor Flash Flood & High Tide",
            lesson_source="Philippine Ports Authority (PPA) Maritime Port Disaster Safety Standards",
            lesson_text=(
                "During combined river runoff and astronomical high tides, dock quays become submerged.\n"
                "Unsecured shipping containers and cargo drums can float and crush personnel against bulkheads.\n"
                "Always wear approved life vests near harbor quays and keep clear of drifting cargo."
            ),
        )
        self._build_world()
        self.hazards.append(FlashFloodHazard(rise_speed=2.2, max_height=75.0))
        self.objectives = [
            "Traverse the slippery wooden quay carefully",
            "Assist Tito Ramon in securing adrift cargo lines",
            "Evacuate to the elevated concrete Harbor Master Office",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Harbor Docks & Wharves", width=640, height=360, ground_color=COLOR_GROUND_HARBOR)
        bm = self.block_map

        # Harbor wharves and docks
        bm.add_road(30, 150, 580, 45)
        bm.add_water(0, 260, 640, 100)

        # Buildings
        bm.add_building("warehouse", "CARGO SHED", 60, 60, 95, 70)
        bm.add_building("warehouse", "COLD STORAGE", 180, 60, 90, 70)
        bm.add_building("shelter", "HARBOR OFFICE", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="HARBOR OFFICE", trigger_id="office_safe")

        # NPCs
        self.add_npc(
            "tito_ramon",
            "Tito Ramon",
            (110, 140),
            [
                "The river water is rushing into the bay faster than the tide can drain it!",
                "These heavy pallet crates are starting to float off the low wharf!",
                "We need to tether them down and move immediately to the elevated Harbor Office!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 165)
        self.player.rect.topleft = (50, 165)

    def on_npc_interacted(self, npc):
        if npc.name == "Tito Ramon" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Tito Ramon")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="harbor_cargo_tie_choice",
                    prompt="Heavy wooden crates are drifting toward the water edge. What is the priority?",
                    options=[
                        {
                            "text": "Secure essential lines from safe footing, then retreat immediately to higher ground",
                            "safe": True,
                            "lesson": "Never position yourself between a floating container and a solid wall.",
                        },
                        {
                            "text": "Jump into the turbulent floodwater between moving crates to grab loose ropes",
                            "safe": False,
                            "lesson": "Floating debris exerts crushing forces that cause fatal blunt trauma.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "office_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch3_1")
            self.complete_level()
