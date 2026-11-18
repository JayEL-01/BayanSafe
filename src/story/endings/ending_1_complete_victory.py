"""Ending 1: Complete Victory - A Community Restored.

Triggered when the player keeps high preparedness (>= 75%) and low unsafe
actions. Presented as three polished pages: the epilogue, the preparedness
audit and the roll of honor.
"""

from typing import Any, Dict, List

from src.story.endings.ending_base import EndingState
from src.ui import theme


class Ending1CompleteVictoryState(EndingState):
    ending_id = "ending_1_complete_victory"
    title = "ENDING 1  -  COMPLETE VICTORY"
    subtitle = "A COMMUNITY RESTORED THROUGH PREPAREDNESS"
    accent = theme.SAGE
    mood = (18, 46, 30)
    mood_alpha = 54
    particle_kind = "mote"
    emblem = "medal"

    def _build_pages(self) -> List[Dict[str, Any]]:
        prep = self.summary.get("preparedness_ratio", 100)
        res = self.summary.get("residents_assisted", 8)
        warn = self.summary.get("warnings_followed", 10)
        unsafe = self.summary.get("unsafe_actions", 0)

        return [
            {
                "heading": "EPILOGUE",
                "sub": "THE MACHINE FALLS SILENT - THE ISLAND BREATHES AGAIN",
                "body": [
                    "The Aegis-Terra machine hums to a gentle, permanent standstill.",
                    "In Central Town, Kuya Ben's jeepney now delivers relief food and water.",
                    "At the Harbor, Rico dela Cruz's VHF radio guided Coast Guard cutters to dock.",
                    "Tito Ramon watched the tsunami recede safely from the cliff lookout.",
                    "Dr. Elias Voss smiles: 'True resilience is an educated community.'",
                    "Not a single life was lost. Bayanihan triumphed over disaster.",
                ],
            },
            {
                "heading": "PREPAREDNESS AUDIT",
                "sub": "OFFICIAL MUNICIPAL READINESS METRICS",
                "bar": ("PREPAREDNESS RATING", prep / 100.0, theme.SAGE),
                "stats": [
                    ("RESIDENTS ASSISTED", f"{res} citizens safe", theme.CREAM),
                    ("ADVISORIES HEEDED", f"{warn} bulletins", theme.CREAM),
                    ("SUPPLIES SECURED", "Go-Bags & radios ready", theme.CREAM),
                    ("UNSAFE ACTIONS", f"{unsafe}  [EXEMPLARY]", theme.SAGE),
                ],
            },
            {
                "heading": "ROLL OF HONOR",
                "sub": "DEDICATED TO PHILIPPINE DISASTER RESPONDERS",
                "body": [
                    "Prepared in line with official national disaster protocols:",
                    "NDRRMC - Disaster Risk Reduction & Management",
                    "DOST-PAGASA - Cyclones, Rain and Storm Surges",
                    "DOST-PHIVOLCS - Earthquakes, Tsunami and Volcanoes",
                    "BFP and NTC - Fire Response and Emergency Telecoms",
                    "Preparedness is the shield that preserves every Filipino family.",
                ],
            },
        ]
