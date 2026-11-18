"""In-game Pause Menu Modal for BayanSafe.

Provides seamless pause/resume, navigation to Color Legend, World Map,
and Main Menu via keyboard or mouse.
"""

from typing import Optional, Callable
import pygame
from src.ui import theme
from src.config.palette import COLOR_UI_PANEL, COLOR_UI_BORDER, COLOR_UI_TEXT, COLOR_UI_ACCENT


class PauseMenu:
    MENU_OPTIONS = [
        ("RESUME", "resume"),
        ("RESTART LEVEL", "restart"),
        ("COLOR LEGEND", "legend"),
        ("WORLD MAP", "world_map"),
        ("MAIN MENU", "main_menu"),
    ]

    def __init__(self, game):
        self.game = game
        self.visible = False
        self.selection = 0

    def show(self):
        self.visible = True
        self.selection = 0

    def hide(self):
        self.visible = False

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.selection = 0

    def handle_input(self, action: str, level=None) -> bool:
        if not self.visible:
            if action in ("escape", "pause"):
                self.show()
                return True
            return False

        if action in ("escape", "pause", "resume"):
            self.hide()
            return True

        if action in ("up", "prev"):
            self.selection = (self.selection - 1) % len(self.MENU_OPTIONS)
            return True
        elif action in ("down", "next"):
            self.selection = (self.selection + 1) % len(self.MENU_OPTIONS)
            return True
        elif action in ("confirm", "interact", "select"):
            return self._execute_option(level)

        return False

    def handle_event(self, event: pygame.Event, level=None) -> bool:
        if not self.visible:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.show()
                return True
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.hide()
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selection = (self.selection - 1) % len(self.MENU_OPTIONS)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selection = (self.selection + 1) % len(self.MENU_OPTIONS)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                return self._execute_option(level)
            elif event.key == pygame.K_l:
                self.hide()
                if level and hasattr(level, "legend_screen"):
                    level.legend_screen.show()
                return True
            elif event.key == pygame.K_m:
                return self._go_world_map()

        return True

    def _execute_option(self, level=None) -> bool:
        opt_key = self.MENU_OPTIONS[self.selection][1]
        if opt_key == "resume":
            self.hide()
            return True
        elif opt_key == "legend":
            self.hide()
            if level and hasattr(level, "legend_screen"):
                level.legend_screen.show()
            return True
        elif opt_key == "restart":
            return self._restart_level(level)
        elif opt_key == "world_map":
            return self._go_world_map()
        elif opt_key == "main_menu":
            return self._go_main_menu()
        return False

    def _restart_level(self, level=None) -> bool:
        """Rebuild the current mission from scratch without stale quest state."""
        self.hide()
        chapter_id = getattr(level, "chapter_id", None)
        level_id = getattr(level, "level_id", None)
        if not chapter_id or not level_id:
            return False
        from src.story.chapter_registry import load_level
        try:
            load_level(self.game, chapter_id, level_id, resume=False)
        except Exception as exc:  # keep the menu responsive if a rebuild fails
            print(f"[BayanSafe] Could not restart level: {exc}")
            self.show()
            return False
        return True

    def _go_world_map(self) -> bool:
        self.hide()
        from src.states.world_map import WorldMap
        self.game.state_manager.change(WorldMap(self.game))
        return True

    def _go_main_menu(self) -> bool:
        self.hide()
        from src.states.main_menu import MainMenu
        self.game.state_manager.change(MainMenu(self.game))
        return True

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        w, h = surface.get_size()
        theme.fade(surface, 215)

        # Dynamic sizing: measure the widest option label
        font = theme.get_font("tiny")
        max_label_w = 0
        for label, _ in self.MENU_OPTIONS:
            lw, _ = font.size(label)
            max_label_w = max(max_label_w, lw)

        btn_w = max(130, max_label_w + 24)   # text + padding
        btn_h = 16
        gap = 4

        # Title height
        title_h = 20
        footer_h = 12

        panel_w = btn_w + 16
        panel_h = title_h + len(self.MENU_OPTIONS) * (btn_h + gap) + footer_h + 16
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        theme.draw_panel(surface, panel_rect, accent=theme.HONEY, alpha=240)

        theme.draw_text(
            surface,
            "PAUSED",
            (w // 2, panel_y + 6),
            size="small",
            color=COLOR_UI_ACCENT,
            anchor="center",
            shadow=True,
        )

        start_y = panel_y + 24
        for idx, (label, _) in enumerate(self.MENU_OPTIONS):
            by = start_y + idx * (btn_h + gap)
            bx = (w - btn_w) // 2
            is_sel = idx == self.selection
            b_rect = pygame.Rect(bx, by, btn_w, btn_h)

            theme.draw_option_row(surface, b_rect, selected=is_sel, accent=theme.HONEY)

            text_col = theme.HONEY if is_sel else theme.CREAM
            prefix = "> " if is_sel else "  "
            theme.draw_text(
                surface,
                f"{prefix}{label}",
                (bx + 8, by + 3),
                size="tiny",
                color=text_col,
                anchor="topleft",
                shadow=False,
            )

        theme.draw_text(
            surface,
            "ESC: Resume  ·  ENTER: Select",
            (w // 2, panel_y + panel_h - 10),
            size="tiny",
            color=theme.CREAM_DIM,
            anchor="center",
            shadow=False,
        )
