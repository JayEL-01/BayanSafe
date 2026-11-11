"""Environment Color Legend Modal Screen.

Provides a full in-game reference explaining what every code-rendered block
and hazard color represents, accessible at any time (via 'L' key or pause menu).
"""

import pygame
from src.config.palette import (
    COLOR_BUILDING_HOUSE,
    COLOR_BUILDING_SHELTER,
    COLOR_BUILDING_HOSPITAL,
    COLOR_BUILDING_RESEARCH,
    COLOR_ROAD,
    COLOR_BRIDGE,
    COLOR_WATER,
    COLOR_HAZARD_FLOOD,
    COLOR_HAZARD_FIRE,
    COLOR_HAZARD_LANDSLIDE,
    COLOR_HAZARD_ASH,
    COLOR_HAZARD_TSUNAMI,
    COLOR_SAFE_ZONE,
    COLOR_ITEM_GOBAG,
    COLOR_ITEM_FIRSTAID,
    COLOR_ITEM_WATER,
    COLOR_ITEM_KEY,
    COLOR_UI_PANEL,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
)
from src.ui import theme


class LegendScreen:
    LEGEND_ENTRIES = [
        ("SAFE HIGH GROUND", COLOR_SAFE_ZONE, "Designated evacuation muster point"),
        ("EVACUATION SHELTER", COLOR_BUILDING_SHELTER, "Barangay emergency safe facility"),
        ("HEALTH CLINIC", COLOR_BUILDING_HOSPITAL, "Medical triage and first aid"),
        ("RESIDENTIAL HOUSE", COLOR_BUILDING_HOUSE, "Homes to clear & assist occupants"),
        ("RESEARCH FACILITY", COLOR_BUILDING_RESEARCH, "Aegis-Terra sensor terminal"),
        ("ROAD / PATH", COLOR_ROAD, "Walkable transit path"),
        ("WOODEN BRIDGE", COLOR_BRIDGE, "River crossing (flood hazard)"),
        ("RIVER / SEA", COLOR_WATER, "Deep water - impassable"),
        ("FLOODWATER ZONE", COLOR_HAZARD_FLOOD, "Active rushing flood - risk of drowning"),
        ("FIRE / THERMAL", COLOR_HAZARD_FIRE, "Flash fire & heat - stay low & clear"),
        ("LANDSLIDE DEBRIS", COLOR_HAZARD_LANDSLIDE, "Collapsed rock & mud slope"),
        ("VOLCANIC ASHFALL", COLOR_HAZARD_ASH, "Toxic ash zone - respiratory risk"),
        ("TSUNAMI SURGE", COLOR_HAZARD_TSUNAMI, "Coastal sea surge - flee to high ground"),
        ("GO-BAG / ITEMS", COLOR_ITEM_GOBAG, "Emergency survival gear to collect"),
    ]

    def __init__(self):
        self.visible = False
        self.scroll_index = 0

    def toggle(self):
        self.visible = not self.visible

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def handle_input(self, action: str) -> bool:
        if not self.visible:
            return False
        if action in ("legend", "escape", "cancel", "confirm", "interact"):
            self.hide()
            return True
        return False

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        w, h = surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 12, 16, 220))
        surface.blit(overlay, (0, 0))

        box_w = min(w - 20, 300)
        box_h = min(h - 16, 168)
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_BORDER, (box_x, box_y, box_w, box_h), 2)

        # Title
        theme.draw_text(
            surface,
            "ENVIRONMENT COLOR LEGEND",
            (w // 2, box_y + 6),
            size="small",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=True,
        )

        # Draw entries in 2 columns
        col1_x = box_x + 8
        col2_x = box_x + box_w // 2 + 4
        start_y = box_y + 22
        row_height = 10

        half = (len(self.LEGEND_ENTRIES) + 1) // 2
        for idx, (label, color, desc) in enumerate(self.LEGEND_ENTRIES):
            is_col2 = idx >= half
            rx = col2_x if is_col2 else col1_x
            row_idx = idx - half if is_col2 else idx
            ry = start_y + row_idx * row_height

            # Color swatch block
            pygame.draw.rect(surface, color, (rx, ry + 1, 8, 7))
            pygame.draw.rect(surface, (255, 255, 255), (rx, ry + 1, 8, 7), 1)

            # Text label
            theme.draw_text(
                surface,
                label,
                (rx + 11, ry),
                size="tiny",
                color=COLOR_UI_TEXT,
                anchor="topleft",
                shadow=False,
            )

        # Bottom dismiss prompt
        theme.draw_text(
            surface,
            "[L] or [ESC] / [SPACE] to Close",
            (w // 2, box_y + box_h - 10),
            size="tiny",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=False,
        )
