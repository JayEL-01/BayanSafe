"""Chapter 4 - Level 2: Canal Breach & Escalating Inundation (North East Plains).

Location: Plains Irrigation Canal Network.
Disaster: Flash Flood to Severe Flooding (Canal Dike Collapse).
Objectives: Navigate rising plains water, rescue stranded farming family, reach Grain Terminal.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import COLOR_GROUND_PLAINS
from src.core.decision_system import Decision


class Chapter4Level2FlashFlood(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_2_flash_flood",
            title="Chapter 4 - Level 2: The Dike Breaks",
            subtitle="North East Plains - Severe Agricultural Inundation",
            disaster_type="Canal Breach / Severe Flooding",
            lesson_source="National Irrigation Administration (NIA) & NDRRMC Dam & Dike Safety Advisory",
            lesson_text=(
                "When agricultural canals or river dikes fail, flat plains inundate with deceptive speed.\n"
                "Water depth can double in under five minutes as water spreads laterally across fields.\n"
                "Never drive or walk across flooded plains roads; obscured ditches and culverts are fatal.\n"
                "Evacuate perpendicularly away from the canal breach to natural ridge lines."
            ),
        )
        self._build_world()
        self.hazards.append(SevereFloodingHazard())
        self.objectives = [
            "Evade rushing water currents from the fractured canal dike",
            "Assist Aling Rosa near the communal threshing barn",
            "Evacuate to the reinforced multi-level Grain Terminal",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Plains Irrigation Breach", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Breached canal water spreading across road
        bm.add_water(150, 0, 60, 360)
        bm.add_road(30, 160, 580, 40)
        bm.add_hazard_zone("flood", 180, 160, 220, 40, label="CANAL SURGE")

        # Buildings
        bm.add_building("house", "THRESHING BARN", 60, 60, 90, 70)
        bm.add_building("shelter", "GRAIN TERMINAL", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="GRAIN TERMINAL", trigger_id="terminal_safe")

        # NPCs
        self.add_npc(
            "aling_rosa",
            "Aling Rosa",
            (115, 140),
            [
                "The earthen wall collapsed with a loud splash! The entire paddy is underwater!",
                "The current is washing away our harvest sacks and our boots are sinking in mud!",
                "Lead us toward the concrete Grain Terminal! Its foundation is built five meters above the plain!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Aling Rosa" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Aling Rosa")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="plains_flood_evac_choice",
                    prompt="The road ahead is covered in knee-deep water. Ditches are completely submerged. How do you proceed?",
                    options=[
                        {
                            "text": "Use a bamboo pole to feel for the road edges and stay strictly on the center crown",
                            "safe": True,
                            "lesson": "Probing ahead with a staff detects hidden submerged irrigation canal drop-offs.",
                        },
                        {
                            "text": "Wade blindly into the murky water hoping the ditch is elsewhere",
                            "safe": False,
                            "lesson": "Submerged drainage ditches can be two meters deep, causing immediate drowning.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "terminal_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch4_2")
            self.complete_level()
