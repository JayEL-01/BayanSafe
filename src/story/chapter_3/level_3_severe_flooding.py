"""Chapter 3 - Level 3: Inundated Warehouses & Emergency Radio (Harbor).

Location: Harbor Warehouse District.
Disaster: Severe Flooding & Saltwater Inundation.
Objectives: Navigate flooded alleys, salvage marine radio with Rico dela Cruz, reach lighthouse.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.flash_flood import SevereFloodingHazard
from src.config.palette import COLOR_GROUND_HARBOR
from src.core.decision_system import Decision


class Chapter3Level3SevereFlooding(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_3_severe_flooding",
            title="Chapter 3 - Level 3: The Flooded Depots",
            subtitle="Harbor Warehouses - Marine Radio Salvage",
            disaster_type="Severe Coastal Flooding & Salt Surge",
            lesson_source="National Telecommunications Commission (NTC) & NDRRMC Emergency Telecoms Cluster Guidelines",
            lesson_text=(
                "Saltwater flooding rapidly corrodes electronic contacts and short-circuits power supplies.\n"
                "Emergency responders must maintain battery-powered high-frequency (HF) and VHF radios\n"
                "sealed in waterproof dry bags, keeping international distress frequency (VHF Ch 16) open.\n"
                "Never operate electrical switchgear while standing in submerged salt floodwater."
            ),
        )
        self._build_world()
        self.hazards.append(SevereFloodingHazard())
        self.objectives = [
            "Cross the flooded warehouse yard avoiding submerged forklifts",
            "Assist Rico dela Cruz in retrieving the backup marine radio transceiver",
            "Carry the radio to the elevated concrete Lighthouse Tower",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Harbor Warehouse District", width=640, height=360, ground_color=COLOR_GROUND_HARBOR)
        bm = self.block_map

        # Flooded roadway
        bm.add_road(30, 160, 580, 40)
        bm.add_hazard_zone("flood", 120, 160, 240, 40, label="SALTWATER FLOOD")

        # Warehouse structures
        bm.add_building("warehouse", "DEPOT 1", 60, 60, 95, 75)
        bm.add_building("warehouse", "DEPOT 2", 180, 60, 95, 75)
        bm.add_building("shelter", "LIGHTHOUSE", 460, 50, 110, 85)
        bm.add_safe_zone(460, 50, 110, 85, label="LIGHTHOUSE TOWER", trigger_id="lighthouse_safe")

        # Item to collect
        bm.add_item("radio", "VHF RADIO", 210, 140)

        # NPCs
        self.add_npc(
            "rico_dela_cruz",
            "Rico dela Cruz",
            (230, 140),
            [
                "The sea water is rising over the loading ramp! If it reaches the radio shelf, we lose contact!",
                "Our VHF marine transceiver is the only link left to the mainland Coast Guard!",
                "Help me pack it into the dry bag and move up to the lighthouse beacon platform!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Rico dela Cruz" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Rico dela Cruz")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="radio_salvage_choice",
                    prompt="The radio is plugged into a flooded wall outlet. How do you safely disconnect it?",
                    options=[
                        {
                            "text": "Shut off the master circuit breaker from the dry panel before touching the plug",
                            "safe": True,
                            "lesson": "Isolating electricity upstream prevents electrocution in conductive saltwater.",
                        },
                        {
                            "text": "Yank the live cord directly out of the water with wet hands",
                            "safe": False,
                            "lesson": "Saltwater is highly conductive; pulling live cables in water is fatal.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "lighthouse_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch3_3")
            self.complete_level()
