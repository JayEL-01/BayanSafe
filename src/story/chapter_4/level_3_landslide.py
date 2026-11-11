"""Chapter 4 - Level 3: Uncovering the Subterranean Truth (North East Plains).

Location: Plains Foothills & Excavation Trench.
Disaster: Rain-Induced Slope Failure & Infrastructure Exposure.
Objectives: Avoid landslide scar, investigate exposed conduit, confer with Dr. Elena Reyes.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import LandslideHazard
from src.config.palette import COLOR_GROUND_PLAINS
from src.core.decision_system import Decision


class Chapter4Level3Landslide(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_3_landslide",
            title="Chapter 4 - Level 3: The Exposed Arteries",
            subtitle="Plains Foothills - Conduit Discovery & Slope Failure",
            disaster_type="Slope Failure & Industrial Conduit Rupture",
            lesson_source="DENR Environmental Management Bureau (EMB) & MGB Underground Mining / Tunneling Safety",
            lesson_text=(
                "Unregulated subterranean excavation and geothermal tunneling severely destabilize surface slopes.\n"
                "When earth failures expose high-voltage industrial cables or pressurized pipelines,\n"
                "maintain a minimum 50-meter safety cordon; arc flash and gas explosion hazards are extreme.\n"
                "Scientific field teams must cross-reference seismic sensor arrays with geological fault maps."
            ),
        )
        self._build_world()
        self.hazards.append(LandslideHazard())
        self.objectives = [
            "Maneuver past the fresh landslide scar at the base of the hill",
            "Examine the exposed Aegis-Terra conduit and telemetry cables",
            "Confer with Dr. Elena Reyes at the mobile seismological van",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Plains Foothills Excavation", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Foothill trail
        bm.add_path(30, 160, 580, 36)
        # Landslide debris scar
        bm.add_hazard_zone("landslide", 170, 150, 110, 60, label="HILLSIDE SLIDE")

        # Exposed facility conduit structure (research building block)
        bm.add_building("research", "AEGIS CONDUIT", 290, 60, 85, 65, trigger_id="conduit_found")
        bm.add_building("clinic", "MOBILE SEISMO VAN", 470, 50, 110, 75)
        bm.add_safe_zone(470, 50, 110, 75, label="SEISMO POST", trigger_id="seismo_safe")

        # Story Item
        bm.add_item("log", "DATA LOG", 300, 140)

        # NPCs
        self.add_npc(
            "dr_elena_reyes",
            "Dr. Elena Reyes",
            (420, 140),
            [
                "Look closely at those sheared wires! Those aren't public utility cables!",
                "They are military-grade pulse waveguides routing gigawatts directly into Volcano Valley!",
                "Our PHIVOLCS seismographs didn't record a natural fault rupture—it was artificially triggered!",
                "Dr. Voss is operating an uncalibrated tectonic resonance generator inside the caldera!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Dr. Elena Reyes" and self.current_objective_idx <= 2:
            self.score_system.assist_resident("Dr. Elena Reyes")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()
                self.complete_objective()
                self.score_system.complete_evacuation("ch4_3")
                self.complete_level()

            self.trigger_decision(
                Decision(
                    decision_id="conduit_investigation_choice",
                    prompt="Sparks crackle from the torn conduit cables. How do you gather evidence?",
                    options=[
                        {
                            "text": "Photograph the telemetry serial numbers from a safe distance without touching wires",
                            "safe": True,
                            "lesson": "Preserving standoff distance prevents fatal electrical arc flash injuries.",
                        },
                        {
                            "text": "Grab the severed high-voltage cables to pull them out of the mud",
                            "safe": False,
                            "lesson": "Industrial high-voltage cables carry thousands of volts that cause instant electrocution.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )
