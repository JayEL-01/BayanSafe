"""Chapter 5 - Level 3: Wildfire & Lava Bombardment (Volcano Valley).

Location: Aegis-Terra Perimeter Campus.
Disaster: Ballistic Bombardment & Wildfire Inferno.
Objectives: Avoid falling incandescent bombs, clear mineral soil firebreak, breach bunker airlock.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.landslide import FlashFireHazard
from src.config.palette import COLOR_GROUND_VALLEY
from src.core.decision_system import Decision


class Chapter5Level3FlashFire(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_3_flash_fire",
            title="Chapter 5 - Level 3: Rain of Fire",
            subtitle="Facility Perimeter - Ballistic Bombs & Wildfire",
            disaster_type="Ballistic Lava Bombs & Wildfire",
            lesson_source="DENR Forest Management Bureau (FMB) Wildfire Suppression & PHIVOLCS Ballistic Hazards",
            lesson_text=(
                "Volcanic ballistic bombs can exceed automobile size and crash miles from the crater.\n"
                "Wildfires ignited by volcanic debris require proactive firebreaks;\n"
                "scraping vegetation down to bare mineral earth starves the flame of fuel.\n"
                "Seek immediate reinforced concrete or subterranean shelter during active ballistic ejecta."
            ),
        )
        self._build_world()
        self.hazards.append(FlashFireHazard())
        self.objectives = [
            "Weave through burning timber zones outside the facility perimeter",
            "Assist Engr. Paolo Santos in cutting the mineral soil firebreak line",
            "Reach the blast-hardened Aegis-Terra Facility Airlock",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Aegis-Terra Facility Campus", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Paved compound road
        bm.add_road(30, 160, 580, 40)
        # Raging brushfire hazard blocks
        bm.add_hazard_zone("fire", 160, 150, 120, 60, label="BURNING BRUSH")

        # Structures
        bm.add_building("warehouse", "PERIMETER GENERATOR", 60, 60, 90, 70)
        bm.add_building("research", "FACILITY AIRLOCK", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="BUNKER AIRLOCK", trigger_id="airlock_safe")

        # NPCs
        self.add_npc(
            "engr_paolo_santos",
            "Engr. Paolo Santos",
            (115, 140),
            [
                "Lava bombs are smashing through the trees like artillery shells!",
                "The grass is dry and the flames are racing straight toward the diesel fuel tanks!",
                "Help me dig a five-meter firebreak down to the raw gravel soil before the fire leaps the fence!",
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
                    decision_id="wildfire_firebreak_choice",
                    prompt="Flames are racing across dry pine needles toward the compound. How do you stop them?",
                    options=[
                        {
                            "text": "Scrape all vegetation and organic matter down to bare mineral dirt and rock",
                            "safe": True,
                            "lesson": "Fire cannot cross a fuel-free gap of bare mineral soil.",
                        },
                        {
                            "text": "Pile dry branches and brush in front of the flames thinking it will smother them",
                            "safe": False,
                            "lesson": "Adding dry fuel causes intense fire flares and rapid flame spread.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "airlock_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch5_3")
            self.complete_level()
