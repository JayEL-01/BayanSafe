"""Ending 1: Complete Victory - A Community Restored.

Triggered when the player maintains high preparedness (>= 75%) and low unsafe actions.
"""

from typing import Dict, Any
import pygame
from src.states.base_state import BaseState
from src.ui import theme
from src.config.palette import (
    COLOR_UI_PANEL,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_SAFE,
)


class Ending1CompleteVictoryState(BaseState):
    def __init__(self, game, summary: Dict[str, Any]):
        super().__init__(game)
        self.summary = summary
        self.timer = 0.0

    def handle_event(self, event: pygame.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                from src.states.main_menu import MainMenu
                self.game.state_manager.change(MainMenu(self.game))
                return True
        return False

    def update(self, dt: float):
        self.timer += dt

    def draw(self, surface: pygame.Surface):
        w, h = surface.get_size()
        surface.fill((14, 28, 20))

        box_w = min(w - 20, 300)
        box_h = min(h - 16, 168)
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_SAFE, (box_x, box_y, box_w, box_h), 2)

        theme.draw_text(
            surface,
            "ENDING 1: COMPLETE VICTORY",
            (w // 2, box_y + 8),
            size="small",
            color=COLOR_UI_SAFE,
            anchor="center",
            shadow=True,
        )

        theme.draw_text(
            surface,
            "A COMMUNITY RESTORED THROUGH PREPAREDNESS",
            (w // 2, box_y + 22),
            size="tiny",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=False,
        )

        epilogue_lines = [
            "The Aegis-Terra machine hums to a gentle, permanent standstill.",
            "Because your community heeded every official NDRRMC advisory,",
            "packed Go-Bags early, and prioritized the vulnerable,",
            "not a single resident was lost to the storm, flood, or eruption.",
            "Bayanihan triumphed over disaster. The island rebuilds together!",
        ]
        curr_y = box_y + 36
        for line in epilogue_lines:
            theme.draw_text(
                surface,
                line,
                (w // 2, curr_y),
                size="tiny",
                color=COLOR_UI_TEXT,
                anchor="center",
                shadow=False,
            )
            curr_y += 11

        curr_y += 4
        stats_line = (
            f"Preparedness: {self.summary.get('preparedness_ratio', 100)}%  |  "
            f"Residents Saved: {self.summary.get('residents_assisted', 0)}  |  "
            f"Warnings Heeded: {self.summary.get('warnings_followed', 0)}"
        )
        theme.draw_text(
            surface,
            stats_line,
            (w // 2, curr_y),
            size="tiny",
            color=COLOR_UI_SAFE,
            anchor="center",
            shadow=True,
        )

        theme.draw_text(
            surface,
            "[SPACE] / [ENTER] Return to Main Menu",
            (w // 2, box_y + box_h - 12),
            size="tiny",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=True,
        )
