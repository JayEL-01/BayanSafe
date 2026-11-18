"""Ending 2: Partial Victory - A Costly Recovery.

Triggered on moderate preparedness (45% - 74%). Presented as three polished
pages: the epilogue, the post-disaster damage audit and the preparedness
lessons.
"""

from typing import Any, Dict, List

from src.story.endings.ending_base import EndingState
from src.ui import theme


class Ending2PartialVictoryState(EndingState):
    ending_id = "ending_2_partial_victory"
    title = "ENDING 2  -  PARTIAL VICTORY"
    subtitle = "A COSTLY RECOVERY AND BITTER LESSONS"
    accent = theme.HONEY
    mood = (72, 46, 10)
    mood_alpha = 46
    particle_kind = "ember"
    emblem = "shield"

    def _build_pages(self) -> List[Dict[str, Any]]:
        prep = self.summary.get("preparedness_ratio", 55)
        res = self.summary.get("residents_assisted", 4)
        unsafe = self.summary.get("unsafe_actions", 2)

        return [
            {
                "heading": "EPILOGUE",
                "sub": "THE MACHINE FALLS SILENT - BUT AT A GRIEVOUS COST",
                "body": [
                    "The Aegis-Terra machine was severed just before the caldera blew.",
                    "Kuya Ben inhaled smoke; neighbors carried him to the clinic.",
                    "Harbor Depot 2 flooded before the radio relays were secured.",
                    "Tito Ramon reached the cliff, but oil slicks burned the pier.",
                    "Dr. Voss: 'Lives were spared - yet hesitation cost us dearly.'",
                ],
            },
            {
                "heading": "POST-DISASTER DAMAGE AUDIT",
                "sub": "AREAS NEEDING IMMEDIATE PREPAREDNESS INTERVENTION",
                "bar": ("PREPAREDNESS SCORE", prep / 100.0, theme.HONEY),
                "stats": [
                    ("EVACUEES SUPPORTED", f"{res} residents safe", theme.CREAM),
                    ("HAZARD BREACHES", f"{unsafe} risky shortcuts", theme.CORAL),
                    ("INFRASTRUCTURE", "Flooded lowlands & shorts", theme.CREAM),
                    ("KEY FINDING", "Early warnings save lives", theme.HONEY),
                ],
            },
            {
                "heading": "PREPAREDNESS LESSONS",
                "sub": "CRITICAL LESSONS FROM OFFICIAL DISASTER PROTOCOLS",
                "body": [
                    "Never postpone vertical evacuation when coastal water recedes.",
                    "Pack waterproof Go-Bags with battery radios before landfall.",
                    "In floods and fire, cut the power before entering water.",
                    "Trust only official NDRRMC and PAGASA bulletins.",
                    "Bayanihan means preparing together before calamity strikes.",
                ],
            },
        ]
