"""Ending 3: Total Failure - Warnings Ignored.

Triggered on low preparedness (< 45%) or excessive unsafe actions (> 5).
Presented as three polished pages: the epilogue, the casualty and
infrastructure report and the urgent imperative.
"""

from typing import Any, Dict, List

from src.story.endings.ending_base import EndingState
from src.ui import theme


class Ending3TotalFailureState(EndingState):
    ending_id = "ending_3_total_failure"
    title = "ENDING 3  -  TOTAL FAILURE"
    subtitle = "THE TRAGIC CONSEQUENCE OF WARNINGS IGNORED"
    accent = theme.CORAL
    mood = (58, 12, 10)
    mood_alpha = 72
    particle_kind = "ash"
    emblem = "warning"

    def _build_pages(self) -> List[Dict[str, Any]]:
        prep = self.summary.get("preparedness_ratio", 20)
        unsafe = self.summary.get("unsafe_actions", 6)

        return [
            {
                "heading": "EPILOGUE",
                "sub": "WHEN WARNINGS ARE IGNORED, CALAMITY REIGNS",
                "body": [
                    "Official warnings were dismissed and evacuation orders ignored.",
                    "Kuya Ben and his neighbors were trapped by toxic smoke.",
                    "At the Harbor, salt floods submerged the radio rooms.",
                    "Tito Ramon was overtaken by the tsunami on the open pier.",
                    "Dr. Voss, in the ashes: 'When science is ignored, calamity reigns.'",
                ],
            },
            {
                "heading": "CASUALTY & INFRASTRUCTURE REPORT",
                "sub": "COMMUNITY DISASTER RESILIENCE BREAKDOWN",
                "bar": ("PREPAREDNESS SCORE", prep / 100.0, theme.CORAL),
                "stats": [
                    ("UNSAFE DECISIONS", f"{unsafe} hazardous actions", theme.CORAL),
                    ("RESCUE RADIOS", "Severed - unequipped", theme.CORAL),
                    ("LOWLAND ASSEMBLY", "Flooded by tsunami surge", theme.CREAM),
                    ("OUTCOME", "Preventable catastrophe", theme.CORAL),
                ],
            },
            {
                "heading": "IN MEMORIAM",
                "sub": "DISASTER PREPAREDNESS IS NON-NEGOTIABLE",
                "body": [
                    "Natural hazards are inevitable. Casualties are not.",
                    "NDRRMC, PAGASA and PHIVOLCS give life-saving warnings.",
                    "Listen to official advisories. Never gamble with lives.",
                    "Pack your Go-Bag. Find high ground. Move without delay.",
                    "Learn the lessons. Protect your community next time.",
                ],
            },
        ]
