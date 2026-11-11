"""Ending 3: Total Failure - Warnings Ignored.

Triggered on low preparedness (< 45%) or excessive unsafe actions (> 5).
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


class Ending3TotalFailureState(BaseState):
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
        surface.fill((28, 12, 12))

        box_w = min(w - 20, 300)
        box_h = min(h - 16, 168)
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_DANGER, (box_x, box_y, box_w, box_h), 2)

        theme.draw_text(
            surface,
            "ENDING 3: TOTAL FAILURE",
            (w // 2, box_y + 8),
            size="small",
            color=COLOR_UI_DANGER,
            anchor="center",
            shadow=True,
        )

        theme.draw_text(
            surface,
            "THE TRAGIC CONSEQUENCE OF WARNINGS IGNORED",
            (w // 2, box_y + 22),
            size="tiny",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=False,
        )

        epilogue_lines = [
            "Official warnings were dismissed. Evacuation orders went unheeded.",
            "Misinformation and panic paralyzed decision-makers until the surge arrived.",
            "Lahar and floodwaters swept through undefended lowland corridors.",
            "The island's communities lie buried beneath mud, ash, and saltwater.",
            "A grim monument to the lethal reality: In disaster, delay is fatal.",
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
            f"Preparedness: {self.summary.get('preparedness_ratio', 0)}%  |  "
            f"Unsafe Actions: {self.summary.get('unsafe_actions', 0)}  |  "
            f"Result: Catastrophic Loss"
        )
        theme.draw_text(
            surface,
            stats_line,
            (w // 2, curr_y),
            size="tiny",
            color=COLOR_UI_DANGER,
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
