"""Chapter 3 - Level 4: Pier Fire & Incoming Tsunami (Harbor).

Location: Harbor Fuel Pier & Seaward Cliffs.
Disaster: Compound Disaster - Flash Fire & Approaching Tsunami.
Objectives: Bypass burning fuel line, shut off emergency isolation valve, scale cliff stairs.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import FlashFireHazard, TsunamiHazard
from src.config.palette import COLOR_GROUND_HARBOR
from src.core.decision_system import Decision


class Chapter3Level4FireTsunami(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_4_fire_tsunami",
            title="Chapter 3 - Level 4: Fire and Water",
            subtitle="Harbor Fuel Pier - Compound Cascading Disaster",
            disaster_type="Dual Hazard: Flash Fire & Tsunami",
            lesson_source="NDRRMC Multi-Hazard Protocol & BFP Hazardous Materials (HazMat) Emergency Response",
            lesson_text=(
                "In compound disaster events (e.g. industrial fire combined with imminent tsunami),\n"
                "life safety and rapid vertical evacuation supersede fire containment attempts.\n"
                "If fire cannot be extinguished within seconds, shut off emergency fuel isolation valves\n"
                "and immediately sprint to elevated terrain beyond the inundation line."
            ),
        )
        self._build_world()
        self.hazards.append(FlashFireHazard())
        self.hazards.append(TsunamiHazard())
        self.objectives = [
            "Maneuver around burning fuel slick barriers on the pier",
            "Assist Tito Ramon in turning the master emergency fuel shutoff valve",
            "Flee up the rocky cliff stairs to the High Harbor Lookout",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Harbor Burning Pier", width=640, height=360, ground_color=COLOR_GROUND_HARBOR)
        bm = self.block_map

        # Pier concrete road
        bm.add_road(30, 160, 580, 40)
        bm.add_water(0, 240, 640, 120)

        # Buildings
        bm.add_building("warehouse", "FUEL BUNKER", 60, 60, 90, 70)
        bm.add_building("shelter", "CLIFF LOOKOUT", 460, 40, 120, 80)
        bm.add_safe_zone(460, 40, 120, 80, label="HIGH CLIFF", trigger_id="cliff_safe")

        # Active fire hazard
        bm.add_hazard_zone("fire", 160, 150, 100, 60, label="BURNING FUEL")

        # NPCs
        self.add_npc(
            "tito_ramon",
            "Tito Ramon",
            (115, 140),
            [
                "The ruptured fuel pipe caught fire! Flames are spreading toward the barge!",
                "Hear that terrifying low rumble from the horizon? The tsunami wave is bearing down on us!",
                "Turn the yellow emergency cut-off wheel, then run for the cliff stairs!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Tito Ramon" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Tito Ramon")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="compound_hazard_choice",
                    prompt="Flames are licking the pipe while the ocean is roaring toward the pier. What is your action?",
                    options=[
                        {
                            "text": "Turn the quick-shutoff valve and run immediately up the cliff path",
                            "safe": True,
                            "lesson": "Isolating fuel cut-offs stops escalation, allowing instant vertical evacuation.",
                        },
                        {
                            "text": "Grab a small bucket of water and stay on the pier trying to fight the oil fire",
                            "safe": False,
                            "lesson": "Throwing water on burning oil causes explosive fire splatters and traps you in the tsunami.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "cliff_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch3_4")
            self.complete_level()
