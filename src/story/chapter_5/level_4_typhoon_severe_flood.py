"""Chapter 5 - Level 4: Lahar Mudflow & Typhoon Landfall (Volcano Valley).

Location: Valley River Chasm & Flood Drainage.
Disaster: Compound Catastrophe: Typhoon Rains + Volcanic Ash = Torrential Lahar.
Objectives: Escape the roaring lahar channel, sound river basin evacuation siren with Mayor Cruz.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import COLOR_GROUND_VALLEY
from src.core.decision_system import Decision


class Chapter5Level4TyphoonSevereFlood(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_5",
            level_id="level_4_typhoon_severe_flood",
            title="Chapter 5 - Level 4: The Concrete Flood (Lahar)",
            subtitle="Valley Chasm - Typhoon Landfall over Volcanic Ash",
            disaster_type="Lahar Mudflow & Severe Typhoon Flooding",
            lesson_source="DOST-PHIVOLCS Lahar Warning Protocols & Historical Lessons from Mt. Pinatubo (1991)",
            lesson_text=(
                "When heavy typhoon rains fall on loose volcanic pyroclastic deposits,\n"
                "millions of tons of boiling mud, ash, and boulders mobilize into LAHAR.\n"
                "Lahar travels at 30-60 km/h and has the density of wet concrete, burying bridges and homes.\n"
                "Never cross a lahar river channel; evacuate perpendicularly up valley canyon ridges immediately!"
            ),
        )
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=4))
        self.hazards.append(SevereFloodingHazard())
        self.objectives = [
            "Sprint away from the deep lahar chasm before the torrential mud crests",
            "Coordinate with Mayor Cruz at the Valley Siren Station",
            "Evacuate perpendicularly up the canyon wall to the High Substation",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Lahar River Chasm", width=640, height=360, ground_color=COLOR_GROUND_VALLEY)
        bm = self.block_map

        # Deep lahar roaring channel
        bm.add_water(160, 0, 90, 360)
        bm.add_road(30, 160, 580, 40)
        # Road bridge over the chasm is the crossing before the mud crests
        bm.add_bridge(160, 160, 90, 40)
        bm.add_hazard_zone("flood", 140, 160, 130, 40, label="ROARING LAHAR")

        # Canyon wall ascent path
        bm.add_road(300, 40, 40, 260)

        # Structures
        bm.add_building("house", "RIVER GAUGE SHED", 60, 60, 85, 60)
        bm.add_building("shelter", "HIGH SUBSTATION", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="HIGH RIDGE", trigger_id="ridge_safe")

        # NPCs
        self.add_npc(
            "mayor_cruz",
            "Mayor Cruz",
            (360, 135),
            [
                "The rain is washing the whole mountain slope into the river!",
                "The acoustic flow sensors upstream are registering a ten-meter wall of boiling lahar!",
                "Sound the emergency sirens for all lowland villages along the riverbanks!",
                "Anyone in the river basin must climb the mountain sides right this second!",
            ],
            role="official",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Mayor Cruz" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Mayor Cruz")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="lahar_escape_choice",
                    prompt="A deafening roar echoes from upstream as boiling mud surges around the bridge piers. Which way do you run?",
                    options=[
                        {
                            "text": "Evacuate perpendicularly UP the steep canyon slope away from the river bed",
                            "safe": True,
                            "lesson": "Climbing perpendicular to lahar channels reaches elevation above the mud crest.",
                        },
                        {
                            "text": "Run downstream along the riverbank path trying to outpace the mudflow on foot",
                            "safe": False,
                            "lesson": "Lahar flows at speeds exceeding 50 km/h; running downstream guarantees being engulfed.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "ridge_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch5_4")
            self.complete_level()
