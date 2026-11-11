"""Chapter 1 - Level 4: Tsunami Surge (Mount Dayaw Summit).

Location: Mount Dayaw Summit Trail.
Disaster: Catastrophic Tsunami Surge.
Objectives: Scale mountain switchback, assist Rico dela Cruz with radio, reach high ground sanctuary.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import TsunamiHazard
from src.config.palette import COLOR_GROUND_PLATEAU
from src.core.decision_system import Decision


class Chapter1Level4Tsunami(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_1",
            level_id="level_4_tsunami",
            title="Chapter 1 - Level 4: The Inundation",
            subtitle="Mount Dayaw Summit - Vertical Evacuation",
            disaster_type="Tsunami Surge (Extreme Danger)",
            lesson_source="DOST-PHIVOLCS & IOC-UNESCO Tsunami Ready Program Standards",
            lesson_text=(
                "A tsunami is not a single wave, but a series of waves arriving over several hours.\n"
                "The first wave is rarely the largest; later waves can be vastly more destructive.\n"
                "Never return to the lowland coast after the first wave recedes.\n"
                "Remain at high elevation until the official 'All Clear' is broadcast by PHIVOLCS/MDRRMC."
            ),
        )
        self._build_world()
        self.hazards.append(TsunamiHazard())
        self.objectives = [
            "Scale the steep switchback trail away from the lower valley",
            "Assist Rico dela Cruz with the emergency transmitter",
            "Secure the community at Mount Dayaw High Ground Sanctuary",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Mount Dayaw Summit Trail", width=640, height=360, ground_color=COLOR_GROUND_PLATEAU)
        bm = self.block_map

        # Lower valley inundated by coastal tsunami surge
        bm.add_hazard_zone("tsunami", 0, 220, 640, 140, label="TSUNAMI INUNDATION ZONE")

        # Ascending switchback trail
        bm.add_path(40, 170, 240, 30)
        bm.add_path(240, 110, 220, 30)
        bm.add_path(420, 50, 180, 30)

        # High elevation sanctuary
        bm.add_building("shelter", "DAYAW SANCTUARY", 460, 40, 120, 65)
        bm.add_safe_zone(460, 40, 120, 65, label="HIGH GROUND SANCTUARY", trigger_id="dayaw_safe")

        # NPCs
        self.add_npc(
            "rico_dela_cruz",
            "Rico dela Cruz",
            (270, 95),
            [
                "The wave hit the harbor jetty at over eighty kilometers per hour!",
                "All landlines and mobile towers along the coast just collapsed!",
                "Help me carry the battery bank for the VHF radio to the summit shelter!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 180)
        self.player.rect.topleft = (50, 180)

    def on_npc_interacted(self, npc):
        if npc.name == "Rico dela Cruz" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Rico dela Cruz")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="tsunami_after_wave_choice",
                    prompt="The first wave has washed back into the bay. Someone asks to go retrieve their vehicle:",
                    options=[
                        {
                            "text": "Forbid anyone from descending; subsequent waves can arrive with greater height",
                            "safe": True,
                            "lesson": "Tsunamis consist of multiple wave crests spaced 10 to 60 minutes apart.",
                        },
                        {
                            "text": "Allow them to run down quickly before the water comes back",
                            "safe": False,
                            "lesson": "Returning prematurely is a leading cause of fatalities during tsunami events.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "dayaw_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch1_4")
            self.complete_level()
