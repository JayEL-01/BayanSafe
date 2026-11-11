"""Chapter 2 - Level 4: Urban Flash Flood & PWD Rescue (Central Town).

Location: Central Town Lowland Residential Avenue.
Disaster: Urban Canal Overflow & Severe Street Inundation.
Objectives: Avoid submerged open manholes, assist Liza, reach elevated ramp shelter.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import FlashFloodHazard
from src.config.palette import COLOR_GROUND_CENTRAL_TOWN
from src.core.decision_system import Decision


class Chapter2Level4FlashFlood(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_2",
            level_id="level_4_flash_flood",
            title="Chapter 2 - Level 4: The Submerged Avenue",
            subtitle="Central Town - Urban Inundation & Accessible Evacuation",
            disaster_type="Urban Flash Flood (Extreme Hazard)",
            lesson_source="DSWD & NCDA Disability-Inclusive Disaster Risk Reduction and Management (DIDRRM) Standards",
            lesson_text=(
                "Urban floods dislodge heavy manhole covers, creating invisible underwater death traps.\n"
                "Never walk through dark water without using a walking stick to probe depth and openings ahead.\n"
                "Evacuation plans must include Persons with Disabilities (PWDs), ensuring wheelchair\n"
                "ramps are cleared of debris and assistive mobility devices are kept dry."
            ),
        )
        self._build_world()
        self.hazards.append(FlashFloodHazard(rise_speed=3.0, max_height=85.0))
        self.objectives = [
            "Probe submerged streets carefully to avoid open sewer drains",
            "Assist Liza at her ground-floor residence",
            "Escort Liza across the elevated ramp to the multi-level Civic Center",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Central Town Lowland Avenue", width=640, height=360, ground_color=COLOR_GROUND_CENTRAL_TOWN)
        bm = self.block_map

        # Flooded roadway
        bm.add_road(30, 160, 580, 45)
        bm.add_hazard_zone("flood", 180, 160, 150, 45, label="SUBMERGED SEWER")

        # Elevated accessible ramp path
        bm.add_road(180, 100, 260, 30)

        # Buildings
        bm.add_building("house", "LIZA'S RESIDENCE", 70, 70, 85, 65)
        bm.add_building("shelter", "CIVIC CENTER", 460, 60, 120, 80)
        bm.add_safe_zone(460, 60, 120, 80, label="CIVIC CENTER", trigger_id="civic_safe")

        # NPCs
        self.add_npc(
            "liza",
            "Liza",
            (115, 140),
            [
                "The water is already creeping over my front doorway threshold!",
                "My wheelchair cannot push through deep muddy currents without help.",
                "Thank you for coming! The elevated pedestrian ramp leads safely up to the Civic Center!",
            ],
            role="vulnerable",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Liza" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Liza")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="pwd_evac_ramp_choice",
                    prompt="Water is rising along the main street. How do you escort Liza's wheelchair?",
                    options=[
                        {
                            "text": "Wheel Liza up the high concrete pedestrian ramp away from submerged gutters",
                            "safe": True,
                            "lesson": "Utilizing designated elevated access ramps prevents wheelchair submersion.",
                        },
                        {
                            "text": "Push the wheelchair straight through knee-deep brown water in the center road",
                            "safe": False,
                            "lesson": "Submerged missing drain covers or currents can topple wheelchairs instantly.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "civic_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch2_4")
            self.complete_level()
