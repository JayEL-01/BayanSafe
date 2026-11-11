"""Ending 2: Partial Victory - A Costly Recovery.

Triggered on moderate preparedness (45% - 74%).
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
    COLOR_UI_DANGER,
)


class Ending2PartialVictoryState(BaseState):
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
        surface.fill((28, 24, 16))

        box_w = min(w - 20, 300)
        box_h = min(h - 16, 168)
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_ACCENT, (box_x, box_y, box_w, box_h), 2)

        theme.draw_text(
            surface,
            "ENDING 2: PARTIAL VICTORY",
            (w // 2, box_y + 8),
            size="small",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=True,
        )

        theme.draw_text(
            surface,
            "A COSTLY RECOVERY AND BITTER LESSONS",
            (w // 2, box_y + 22),
            size="tiny",
            color=COLOR_UI_TEXT,
            anchor="center",
            shadow=False,
        )

        epilogue_lines = [
            "The machine was severed before the caldera suffered a total blowout.",
            "However, hesitation, delayed evacuations, and risky shortcuts",
            "took a heavy toll on the island's infrastructure and families.",
            "Bridges are down, clinics overflow, and recovery will take years.",
            "The community survived, but learned vigilance cannot be compromised.",
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
            f"Preparedness: {self.summary.get('preparedness_ratio', 50)}%  |  "
            f"Unsafe Choices: {self.summary.get('unsafe_actions', 0)}  |  "
            f"Warnings Heeded: {self.summary.get('warnings_followed', 0)}"
        )
        theme.draw_text(
            surface,
            stats_line,
            (w // 2, curr_y),
            size="tiny",
            color=COLOR_UI_ACCENT,
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
