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
from src.ui import text_utils as tu


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

        # Padding and layout
        PAD = 8
        INNER_GAP = 12
        COL_GAP = 10

        box_w = min(w - 16, 304)
        # We'll calculate height based on content
        col_w = (box_w - PAD * 2 - COL_GAP) // 2

        # Prepare content and measure
        half = (len(self.LEGEND_ENTRIES) + 1) // 2
        col1_items = self.LEGEND_ENTRIES[:half]
        col2_items = self.LEGEND_ENTRIES[half:]

        def measure_col(items, width):
            total_h = 0
            measured = []
            for label, color, desc in items:
                # Label is tiny
                lh = theme.get_font("tiny").get_height()
                # Description wrapped to col_w - swatch_offset
                swatch_w = 12
                desc_w = width - swatch_w
                desc_lines = tu.wrap_text(desc, "tiny", desc_w)
                item_h = max(lh, len(desc_lines) * (lh - 1)) + 4
                measured.append((label, color, desc_lines, item_h))
                total_h += item_h + 2
            return total_h, measured

        h1, m1 = measure_col(col1_items, col_w)
        h2, m2 = measure_col(col2_items, col_w)

        content_h = max(h1, h2)
        title_h = 16
        footer_h = 12
        box_h = PAD * 2 + title_h + content_h + footer_h + 4

        # Clamp height to screen
        if box_h > h - 10:
            box_h = h - 10
            # If it's still too tall, we might need to skip descriptions or scroll
            # For now, let's just use the height we have.

        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        theme.draw_panel(surface, box_rect, title="ENVIRONMENT COLOR LEGEND", accent=COLOR_UI_ACCENT)

        start_y = box_y + title_h + PAD + 2

        def draw_col(items_measured, start_x, start_y):
            curr_y = start_y
            for label, color, desc_lines, item_h in items_measured:
                # Color swatch
                swatch_rect = pygame.Rect(start_x, curr_y + 1, 8, 7)
                pygame.draw.rect(surface, color, swatch_rect)
                pygame.draw.rect(surface, (255, 255, 255), swatch_rect, 1)

                # Label (bold-ish accent)
                theme.draw_text(surface, label, (start_x + 11, curr_y), "tiny", COLOR_UI_ACCENT, shadow=False)

                # Descriptions (small cream text below or beside label)
                # If label is long, desc starts below it. Let's stack them for clarity.
                lh = theme.get_font("tiny").get_height()
                desc_y = curr_y + lh - 1
                for i, line in enumerate(desc_lines):
                    if desc_y + (i+1)*lh > box_rect.bottom - footer_h - PAD: break
                    theme.draw_text(surface, line, (start_x + 11, desc_y + i * (lh - 1)), "tiny", COLOR_UI_TEXT, shadow=False)

                curr_y += item_h + 2

        draw_col(m1, box_x + PAD, start_y)
        draw_col(m2, box_x + PAD + col_w + COL_GAP, start_y)

        # Bottom dismiss prompt
        theme.draw_text(
            surface,
            "[L] or [ESC] / [SPACE] to Close",
            (w // 2, box_rect.bottom - PAD - 2),
            size="tiny",
            color=COLOR_UI_ACCENT,
            anchor="midbottom",
            shadow=False,
        )
