"""Chapter 4 - Level 1: Plains Gale & Farm Defense (North East Plains).

Location: Agricultural Rice Fields & Farm Dikes.
Disaster: Typhoon Wind & Inundating Rain (TCWS #2).
Objectives: Check livestock corral, assist Jun in sandbagging river dike, reach farm hall.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_PLAINS
from src.core.decision_system import Decision


class Chapter4Level1Typhoon(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_1_typhoon",
            title="Chapter 4 - Level 1: Winds Over the Fields",
            subtitle="North East Plains - Agricultural Flood Defense",
            disaster_type="Typhoon (PAGASA TCWS #2)",
            lesson_source="Department of Agriculture (DA) Disaster Risk Reduction & Management in Agriculture Guidelines",
            lesson_text=(
                "Agricultural communities must execute early harvest of mature crops upon storm advisory.\n"
                "Unhitch and move farm work animals (carabaos, cattle) to higher earthen knolls;\n"
                "never tether livestock in low-lying pastures where rising floodwaters cause drowning.\n"
                "Reinforce earthen irrigation bunds with interlocked burlap sandbags."
            ),
        )
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=2))
        self.objectives = [
            "Inspect the open pasture trail",
            "Assist Jun in securing the riverbank irrigation dike",
            "Muster at the elevated Agricultural Cooperative Silo",
        ]

    def _build_world(self):
        self.block_map = BlockMap("North East Agricultural Plains", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Dirt farm roads and dikes
        bm.add_path(30, 160, 580, 36)
        bm.add_road(300, 30, 36, 270)

        # Buildings
        bm.add_building("house", "FARMHOUSE", 60, 60, 85, 60)
        bm.add_building("warehouse", "CORRAL", 180, 60, 80, 60)
        bm.add_building("shelter", "GRAIN SILO", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="GRAIN SILO", trigger_id="silo_safe")

        # NPCs
        self.add_npc(
            "jun",
            "Jun",
            (115, 140),
            [
                "The rain over the plains hasn't stopped for eight hours!",
                "Our carabaos were tethered near the river creek! I just cut them free to higher ground!",
                "Help me pack sandbags along the irrigation gate before the whole rice field submerges!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Jun" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Jun")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="plains_animal_rescue_choice",
                    prompt="Where should farm livestock be relocated before the river crests?",
                    options=[
                        {
                            "text": "Move cattle to designated elevated communal mounds and untether them",
                            "safe": True,
                            "lesson": "Tethered animals drown when water levels rise; elevated mounds preserve herds.",
                        },
                        {
                            "text": "Lock all cattle inside a padlocked low-ground wooden pen near the creek",
                            "safe": False,
                            "lesson": "Confining animals in flood paths leads to 100% livestock mortality.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "silo_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch4_1")
            self.complete_level()
