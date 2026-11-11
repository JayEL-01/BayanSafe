"""Chapter 3 - Level 2: Harbor Gale & Snapback Hazard (Harbor).

Location: Harbor Breakwater & Fishing Jetty.
Disaster: Maritime Typhoon Gale (TCWS #3 & Gale Warning).
Objectives: Avoid wave spray over breakwater, help Tatay Pio secure bancas, avoid snapback zones.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_HARBOR
from src.core.decision_system import Decision


class Chapter3Level2Typhoon(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_2_typhoon",
            title="Chapter 3 - Level 2: The Crashing Seawall",
            subtitle="Harbor Jetty - Gale Warning & Mooring Safety",
            disaster_type="Typhoon & Gale Warning (PCG No-Sail)",
            lesson_source="Philippine Coast Guard (PCG) Sea Travel Advisory & Mooring Snapback Guidelines",
            lesson_text=(
                "Under PCG No-Sail protocols, all sea travel for vessels of any tonnage is strictly suspended.\n"
                "When mooring ships during severe gales, stay far away from taut synthetic ropes;\n"
                "a snapping mooring cable recoils with supersonic speed and lethal kinetic force.\n"
                "Anchor boats in sheltered coves and seek onshore shelter immediately."
            ),
        )
        self._build_world()
        self.hazards.append(TyphoonHazard(tcws_level=3))
        self.objectives = [
            "Advance along the protected side of the concrete breakwater",
            "Assist Tatay Pio in tying down the community fishing bancas",
            "Retreat to the reinforced Coast Guard Station bunker",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Harbor Seawall & Breakwater", width=640, height=360, ground_color=COLOR_GROUND_HARBOR)
        bm = self.block_map

        # Breakwater concrete walkway
        bm.add_road(30, 160, 580, 40)
        bm.add_water(0, 240, 640, 120)

        # Buildings
        bm.add_building("warehouse", "BOAT SHED", 60, 60, 90, 70)
        bm.add_building("shelter", "COAST GUARD POST", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="PCG STATION", trigger_id="pcg_safe")

        # Wave splash hazard strip
        bm.add_hazard_zone("flood", 180, 200, 180, 40, label="WAVE SPLASH")

        # NPCs
        self.add_npc(
            "tatay_pio",
            "Tatay Pio",
            (115, 140),
            [
                "The Coast Guard hoisted the red flag! No boats are allowed out to sea!",
                "The swell is lifting the bancas so violently that the nylon ropes are humming!",
                "Step back from the line tension! Do not stand in the snapback zone!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Tatay Pio" and self.current_objective_idx <= 1:
            self.score_system.assist_resident("Tatay Pio")
            def on_decide(opt):
                self.complete_objective()
                self.complete_objective()

            self.trigger_decision(
                Decision(
                    decision_id="harbor_snapback_choice",
                    prompt="A nylon mooring cable is stretched near maximum breaking tension. Where do you stand?",
                    options=[
                        {
                            "text": "Stand outside the rope's arc of recoil behind a reinforced concrete pillar",
                            "safe": True,
                            "lesson": "Positioning behind solid barriers protects personnel from catastrophic rope snap.",
                        },
                        {
                            "text": "Straddle the taut line while pulling down with your whole body weight",
                            "safe": False,
                            "lesson": "Parting lines snap back with force capable of amputating limbs or causing death.",
                        },
                    ],
                    on_resolved=on_decide,
                )
            )

    def on_trigger_activated(self, trigger_id: str):
        if trigger_id == "pcg_safe" and self.current_objective_idx >= 2:
            self.score_system.complete_evacuation("ch3_2")
            self.complete_level()
