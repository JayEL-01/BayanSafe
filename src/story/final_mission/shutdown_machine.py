"""Final Mission: Shut Down the Machine.

Location: Project Aegis-Terra Subterranean Core Control Room.
Antagonist: Dr. Elias Voss.
Objectives: Confront Dr. Elias Voss, execute scram protocols, deactivate artificial seismic core.
"""

import pygame
from src.story.base_level import BaseLevel
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.config.palette import COLOR_GROUND_FACILITY
from src.core.decision_system import Decision


class FinalMissionShutdownMachine(BaseLevel):
    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="final_mission",
            level_id="shutdown_machine",
            title="Final Mission: The Aegis Core",
            subtitle="Central Facility Bunker - Confrontation with Dr. Elias Voss",
            disaster_type="Catastrophic Resonance Overload",
            lesson_source="Philippine Institute of Volcanology and Seismology (PHIVOLCS) Geological Hazard Assessment",
            lesson_text=(
                "Nature cannot be conquered through reckless technological hubris.\n"
                "True community safety is built on resilience, early warnings,\n"
                "transparent public communication, and collective preparedness.\n"
                "A united community that heeds verified science will endure any disaster."
            ),
        )
        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=7))
        self.objectives = [
            "Confront Dr. Elias Voss at the Aegis-Terra Master Console",
            "Depressurize the geothermal injector manifold",
            "Decouple the electromagnetic resonance coils to scram the core",
        ]

    def _build_world(self):
        self.block_map = BlockMap("Aegis-Terra Subterranean Control Core", width=640, height=360, ground_color=COLOR_GROUND_FACILITY)
        bm = self.block_map

        # High-tech facility flooring & server aisles
        bm.add_road(40, 160, 560, 40)
        bm.add_road(300, 40, 40, 260)

        # Core reactor chamber & server mainframes
        bm.add_building("research", "TERMINAL A", 60, 60, 95, 75)
        bm.add_building("research", "TERMINAL B", 180, 60, 95, 75)
        bm.add_building("research", "AEGIS CORE", 340, 50, 140, 90)
        bm.add_building("research", "BACKUP SCRAM", 500, 50, 90, 75)
        bm.add_safe_zone(340, 50, 140, 90, label="SCRAM CONSOLE", trigger_id="scram_zone")

        # Keycard item
        bm.add_item("key", "MASTER KEY", 100, 140)

        # Antagonist NPC: Dr. Elias Voss
        self.add_npc(
            "dr_elias_voss",
            "Dr. Elias Voss",
            (380, 140),
            [
                "You don't understand what you're interfering with!",
                "Nature is violent, chaotic, and blind! I was building a machine to control the earth's heartbeat!",
                "I wanted to bleed off the tectonic pressure in controlled pulses!",
                "The calculations were perfect... but the geothermal resonance harmonic ran away from me!",
                "If we don't initiate the manual scram sequence right now, the entire faultline will tear open!",
            ],
            role="antagonist",
        )

        self.player.pos = pygame.Vector2(60, 175)
        self.player.rect.topleft = (60, 175)

    def on_npc_interacted(self, npc):
        if npc.name == "Dr. Elias Voss" and self.current_objective_idx == 0:
            self.complete_objective()
            # Step 1: Depressurization decision
            def on_decide_1(opt):
                self.complete_objective()
                self._trigger_step_2()

            self.trigger_decision(
                Decision(
                    decision_id="scram_step_1",
                    prompt="Manifold pressure is critical. How do you vent the thermal injectors?",
                    options=[
                        {
                            "text": "Open bypass pressure-relief valves into the auxiliary basalt buffer chamber",
                            "safe": True,
                            "lesson": "Controlled pressure equalization prevents catastrophic explosive shockwaves.",
                        },
                        {
                            "text": "Slam the emergency shutoff valve shut while pressure is rising at peak rate",
                            "safe": False,
                            "lesson": "Abrupt valve closures against superheated steam cause explosive water hammer ruptures.",
                        },
                    ],
                    on_resolved=on_decide_1,
                )
            )

    def _trigger_step_2(self):
        def on_decide_2(opt):
            self.complete_level()

        self.trigger_decision(
            Decision(
                decision_id="scram_step_2",
                prompt="The resonance harmonic is vibrating the bedrock. How do you disconnect the coils?",
                options=[
                    {
                        "text": "Insert master scram keycard and execute graduated phase-frequency dampening",
                        "safe": True,
                        "lesson": "Gradual phase dampening stabilizes the subterranean faultline without triggering shockwaves.",
                    },
                    {
                        "text": "Smash the main circuit breaker with a metal crowbar to cut all power instantly",
                        "safe": False,
                        "lesson": "Inductive back-EMF discharge under heavy load causes massive arc explosions.",
                    },
                ],
                on_resolved=on_decide_2,
            )
        )

    def proceed_to_next(self):
        """Transition directly to the canonical ending based on ScoreSystem."""
        from src.story.chapter_registry import launch_ending
        launch_ending(self.game, self.score_system)
