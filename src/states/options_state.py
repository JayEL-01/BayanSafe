import pygame

from src.core import prefs, settings
from src.core.strings import tr
from src.states.base_state import BaseState
from src.ui import sfx, theme
from src.ui.button import Button


class OptionsState(BaseState):
    """Language (English / Filipino) and sound on/off. Saved to prefs.json."""

    def __init__(self, game):
        super().__init__(game)
        self.backdrop = theme.CozyBackdrop()
        self.time = 0.0
        self.selected = 0
        w, h, gap = 150, 18, 7
        x = (settings.INTERNAL_WIDTH - w) // 2
        self.buttons = [Button("", (x, 56 + i * (h + gap), w, h), cb)
                        for i, cb in enumerate((self.toggle_language, self.toggle_sfx, self.back))]
        self._refresh()

    # ---------- actions ----------
    def toggle_language(self):
        prefs.put("language", "fil" if prefs.get("language") == "en" else "en")
        sfx.play("tock", 0.4)
        self._refresh()

    def toggle_sfx(self):
        prefs.put("sfx", not prefs.get("sfx"))
        sfx.play("tock", 0.4)
        self._refresh()

    def back(self):
        self.game.state_manager.pop()      # if your StateManager names this differently, change it here

    def _refresh(self):
        self.buttons[0].text = f"{tr('language')}: {tr('lang_name')}"
        self.buttons[1].text = f"{tr('sfx')}: {tr('on') if prefs.get('sfx') else tr('off')}"
        self.buttons[2].text = tr("back")
        for i, b in enumerate(self.buttons):
            b.selected = (i == self.selected)

    def _select(self, i):
        if i != self.selected:
            self.selected = i
            sfx.play("tock", 0.3)
            self._refresh()

    # ---------- state API ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._select((self.selected - 1) % len(self.buttons))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select((self.selected + 1) % len(self.buttons))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT):
                self.buttons[self.selected].activate()
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.back()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for i, b in enumerate(self.buttons):
                if b.contains(pos):
                    self._select(i)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for b in self.buttons:
                if b.contains(pos):
                    b.activate()

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        self.backdrop.draw(surface, self.time)
        theme.dim(surface, 110)
        panel = pygame.Rect(40, 14, 240, 128)
        theme.draw_panel(surface, panel, tr("options_title"), theme.HONEY)
        for b in self.buttons:
            b.draw(surface, self.time)
        theme.draw_text(surface, tr("hint_options"), (settings.INTERNAL_WIDTH // 2, 164),
                        "tiny", theme.CREAM_DIM, shadow=False, anchor="center")