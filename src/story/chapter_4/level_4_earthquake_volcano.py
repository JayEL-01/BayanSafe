"""Chapter 4 - Level 4: Volcanic Tremor Swarm & Steam Venting (North East Plains).

Location: Plains-Valley Gateway & Boundary Post.
Disaster: Volcanic Earthquake Swarm & Phreatic Steam Venting.
Objectives: Evacuate plains boundary, consult Dr. Mira Santos on SO2 gas, enforce 6-km Danger Zone.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.hazards.landslide import VolcanicEruptionHazard
from src.config.palette import COLOR_GROUND_PLAINS
from src.core.decision_system import Decision


class Chapter4Level4EarthquakeVolcano(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_4",
            level_id="level_4_earthquake_volcano",
            title="Chapter 4 - Level 4: The Earth Groans",
            subtitle="Plains Gateway - Harmonic Tremors & Phreatic Venting",
            disaster_type="Volcanic Earthquake Swarm & Alert Level 3",
            lesson_source="DOST-PHIVOLCS Volcanic Alert Level Scheme & Permanent Danger Zone (PDZ) Standards",
            lesson_text=(
                "Volcano Alert Level 3 indicates high level of volcanic unrest with magma intrusion.\n"
                "A 6-kilometer radius Permanent Danger Zone (PDZ) must be evacuated immediately.\n"
                "Volcanic sulfur dioxide (SO2) gas is toxic and heavier than air, collecting in low ravines.\n"
                "Wear N95 respirators or moist cotton masks and evacuate immediately upwind."
            ),
        )
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=6))
        self.hazards.append(VolcanicEruptionHazard())
        self.objectives = [
            "Withstand the harmonic volcanic tremor swarms along the highway",
            "Consult Dr. Mira Santos at the gas monitoring station",
            "Establish the 6-kilometer Permanent Danger Zone checkpoint",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Caldera Gateway Checkpoint", width=640, height=360, ground_color=COLOR_GROUND_PLAINS)
        bm = self.block_map

        # Gateway highway
        bm.add_road(30, 160, 580, 40)
        bm.add_road(300, 30, 40, 270)

        # Toxic steam venting crack (gray ash hazard)
        bm.add_hazard_zone("ash", 160, 150, 100, 60, label="SO2 STEAM VENT")

        # Buildings
        bm.add_building("research", "GAS SENSOR HUB", 60, 60, 90, 70)
        bm.add_building("shelter", "PDZ CHECKPOINT", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="SAFE PERIMETER", trigger_id="pdz_safe")

        # NPCs
        self.add_npc(
            "dr_mira_santos",
            "Dr. Mira Santos",
            (115, 140),
            [
                "Sulfur dioxide flux just spiked past 8,000 metric tons per day!",
                "The groundwater pH dropped to 1.8—it is burning through our monitoring probes!",
                "The caldera is swelling. An explosive magmatic eruption is imminent within hours!",
                "We must seal the 6-km Permanent Danger Zone and stop anyone from heading toward the valley!",
            ],
            role="researcher",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Dr. Mira Santos" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Dr. Mira Santos")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="volcanic_gas_choice",
                    prompt="A yellowish sulfur gas cloud is drifting across the gateway road. How do you pass?",
                    options=[
                        {
                            "text": "Put on N95 mask / moist cloth, move upwind, avoid low ravines where gas pools",
                            "safe": True,
                            "lesson": "SO2 gas irritates the respiratory tract; staying upwind prevents acute poisoning.",
                        },
                        {
                            "text": "Walk directly through the dense yellow fog breathing deeply without a mask",
                            "safe": False,
                            "lesson": "Inhaling dense volcanic sulfur dioxide triggers severe pulmonary edema and suffocation.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "pdz_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch4_4")
            self.complete_level()
