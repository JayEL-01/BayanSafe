"""Prologue - Level 1: Typhoon Approaching (San Isidro).

Location: San Isidro Coastal Barangay.
Disaster: Tropical Cyclone Wind Signal (PAGASA TCWS #2 Escalating).
Objectives: Secure structures, clear canal debris, assist Lola Teresa.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_SAN_ISIDRO
from src.core.decision_system import Decision


class PrologueLevel1Typhoon(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="prologue",
            level_id="level_1_typhoon",
            title="Prologue - Level 1: The Gale Rising",
            subtitle="San Isidro - Tropical Cyclone Advisory",
            disaster_type="Typhoon (PAGASA TCWS #2)",
            lesson_source="DOST-PAGASA Tropical Cyclone Wind Signal (TCWS) System & NDRRMC Guidelines",
            lesson_text=(
                "Under TCWS #2 (winds 62-88 km/h expected in 24 hours):\n"
                "Secure tin roofs, trim hanging tree branches, and clear drainage canals.\n"
                "Prioritize the pre-emptive evacuation of vulnerable community members\n"
                "(elderly, persons with disabilities, infants, and pregnant mothers)."
            ),
        )
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=2))
        self.objectives = [
            "Assist Lola Teresa at her home with her medicine",
            "Help Kuya Ben clear debris from the main street",
            "Reach the elevated high-ground zone before winds intensify",
        ]

    def _build_world(self):
        self.block_map = BlockMap("San Isidro Coastline", width=640, height=360, ground_color=COLOR_GROUND_SAN_ISIDRO)
        bm = self.block_map

        # Coastal road & cross streets
        bm.add_road(40, 160, 560, 30)
        bm.add_road(300, 30, 30, 270)
        # Connecting road ramp leading up to High Ground
        bm.add_road(480, 130, 60, 30)

        # Buildings
        bm.add_building("house", "LOLA TERESA", 90, 80, 80, 55)
        bm.add_building("house", "HOUSE B", 200, 80, 70, 50)
        bm.add_building("damaged_house", "DAMAGED SHED", 360, 80, 60, 50)

        # South sea waters
        bm.add_water(0, 320, 640, 40)

        # Safe assembly zone (unobstructed, walkable high ground)
        bm.add_safe_zone(460, 50, 140, 80, label="HIGH GROUND", trigger_id="safe_reach")

        # NPCs
        self.add_npc(
            "lola_teresa",
            "Lola Teresa",
            (130, 140),
            [
                "The winds are rattling the window shutters so violently, apo!",
                "I have my maintenance medicines packed in my small waterproof pouch.",
                "Thank you for helping an old grandmother prepare for the storm.",
            ],
            role="vulnerable",
        )

        self.add_npc(
            "kuya_ben",
            "Kuya Ben",
            (320, 165),
            [
                "The wind is blowing banana leaves and loose zinc sheets across the street!",
                "If we don't keep these drainage canals clear, water will back up instantly.",
                "Stay clear of dangling power cables and push on to higher ground!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(60, 175)
        self.player.rect.topleft = (60, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Lola Teresa" and self.current_objective_idx == 0:
            self.score_system.assist_resident("Lola Teresa")
            self.complete_objective()
        elif npc.name == "Kuya Ben" and self.current_objective_idx == 1:
            def on_decide(opt):
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="typhoon_debris_choice",
                    prompt="Downed power lines and tree branches block the path ahead:",
                    options=[
                        {
                            "text": "Report wire to authorities, stay 10m away, take clear elevated path",
                            "safe": True,
                            "lesson": "Never touch fallen power lines or step in water puddles near downed wires.",
                        },
                        {
                            "text": "Attempt to push the dangling electrical wire aside with bare hands",
                            "safe": False,
                            "lesson": "High electrocution risk; downed wires can remain live and energize ground.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "safe_reach" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("prologue_1")
            self.complete_level()
