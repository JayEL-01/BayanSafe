"""Chapter 5 - Level 1: Caldera Tremors & Rockfalls (Volcano Valley).

Location: Volcano Valley Gorge & Access Highway.
Disaster: Strong Caldera Tremors (PEIS Intensity VII) & Rockfall Cascades.
Objectives: Navigate fissure chasms, locate stranded research convoy, reach Facility Gate.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.hazards.landslide import LandslideHazard
from src.config.palette import COLOR_GROUND_VALLEY
from src.core.decision_system import Decision


class Chapter5Level1EarthquakeLandslide(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_1_earthquake_landslide",
            title="Chapter 5 - Level 1: The Splitting Caldera",
            subtitle="Volcano Valley - Caldera Ruptures & Rockfall",
            disaster_type="Volcanic Earthquake (Intensity VII) & Rockfall",
            lesson_source="DOST-PHIVOLCS Volcanic Seismicity & Caldera Fissure Safety Manual",
            lesson_text=(
                "Caldera earthquakes can rip open ground fissures several meters wide in seconds.\n"
                "Never cross active ground fissures; superheated volcanic gases and steam vent from below.\n"
                "In steep volcanic gorges, falling boulders travel at terminal velocity.\n"
                "Watch the upper canyon rims and seek shelter under solid overhangs or reinforced culverts."
            ),
        )
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=7))
        self.hazards.append(LandslideHazard())
        self.objectives = [
            "Traverse the cracked caldera gorge road",
            "Assist Engr. Paolo Santos trapped behind collapsed boulders",
            "Reach the outer security gate of Project Aegis-Terra",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Volcano Valley Gorge", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Broken canyon highway
        bm.add_road(30, 160, 580, 40)
        # Deep ground fissure hazard (dark unstable brown)
        bm.add_hazard_zone("landslide", 160, 150, 120, 60, label="CALDERA FISSURE")

        # Buildings
        bm.add_building("house", "CONSTRUCTION SHED", 60, 60, 85, 60)
        bm.add_building("research", "AEGIS GATEHOUSE", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="AEGIS GATE", trigger_id="gate_safe")

        # NPCs
        self.add_npc(
            "engr_paolo_santos",
            "Engr. Paolo Santos",
            (115, 140),
            [
                "The road ahead sheared vertically by almost two meters!",
                "Dr. Voss locked himself inside the subterranean command bunker and disabled remote access!",
                "He believes his resonance array can stabilize the magma chamber, but it's doing the opposite!",
                "It's hyper-charging the magma chamber like a shaken soda can! We have to breach the facility!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Engr. Paolo Santos" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Engr. Paolo Santos")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="fissure_crossing_choice",
                    prompt="A gaping fissure vents superheated volcanic steam across the road. How do you bypass it?",
                    options=[
                        {
                            "text": "Skirt around along the solid basalt outcrop on the high shoulder",
                            "safe": True,
                            "lesson": "Solid basalt rock supports weight safely while avoiding hot fissure gases.",
                        },
                        {
                            "text": "Try to jump directly over the smoking thermal crack where the soil looks crumbled",
                            "safe": False,
                            "lesson": "Crumbled soil around active fissures collapses under weight into superheated vents.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "gate_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch5_1")
            self.complete_level()
