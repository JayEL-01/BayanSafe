import pygame

from src.core import prefs, settings
from src.core.strings import tr
from src.states.base_state import BaseState
from src.states.character_select import CharacterSelect
from src.states.guide_state import GuideState
from src.states.options_state import OptionsState
from src.states.placeholder_state import PlaceholderState
from src.ui import menu_fx, sfx, theme
from src.ui.backdrop import MenuBackdrop
from src.ui.button import Button

ENTRIES = [               # (string key, icon)
    ("new_game", "house"),
    ("continue", "clip"),
    ("guide", "book"),
    ("options", "gear"),
    ("exit", "door"),
]
SLIDE_DELAY = 0.2         # seconds before the first button slides in
SLIDE_STAGGER = 0.08      # seconds between buttons
SLIDE_TIME = 0.35


class MainMenu(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.backdrop = MenuBackdrop()
        self.time = 0.0
        self.buttons = []
        self.selected = 0
        self._lang = prefs.get("language")
        self._save_check = -1
        self._build_buttons()
        sfx.warm()

    # ---------- setup ----------
    def _build_buttons(self):
        actions = {"new_game": self.new_game, "continue": self.continue_game,
                   "guide": self.guide, "options": self.options, "exit": self.game.quit}
        width, height, gap = 110, 16, 3
        x = (settings.INTERNAL_WIDTH - width) // 2
        for i, (key, icon) in enumerate(ENTRIES):
            button = Button(tr(key), (x, 68 + i * (height + gap), width, height),
                            actions[key], icon=icon, press_delay=0.12)
            button.offset_x = -150                   # starts off-screen, slides in
            self.buttons.append(button)
        self._refresh_buttons()
        self._update_selection()

    def _refresh_buttons(self):
        """Re-reads language and save state (called when either may have changed)."""
        self._lang = prefs.get("language")
        for (key, _), button in zip(ENTRIES, self.buttons):
            button.text = tr(key)
            if key == "continue":
                button.enabled = prefs.has_save()

    # ---------- actions ----------
    def new_game(self):
        self.game.session.reset()
        self.game.state_manager.push(CharacterSelect(self.game))

    def continue_game(self):
        # replace with your real load logic when the save system exists
        self.game.state_manager.push(PlaceholderState(self.game, "LOAD GAME"))

    def guide(self):
        self.game.state_manager.push(GuideState(self.game))

    def options(self):
        self.game.state_manager.push(OptionsState(self.game))

    # ---------- selection ----------
    def _update_selection(self):
        for i, button in enumerate(self.buttons):
            button.selected = (i == self.selected)

    def _select(self, index):
        if index != self.selected:
            self.selected = index
            self._update_selection()
            sfx.play("tock", 0.35)

    # ---------- state API ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._select((self.selected - 1) % len(self.buttons))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select((self.selected + 1) % len(self.buttons))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected].activate()
            elif event.key == pygame.K_t:
                self.backdrop.next_time()
            elif event.key == pygame.K_F2:
                self.backdrop.toggle_debug()
            elif event.key == pygame.K_F3:
                self.backdrop.toggle_boost()
            elif event.key == pygame.K_h:
                self.backdrop.next_hazard()

        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            self.backdrop.look_at(pos[0])
            for i, button in enumerate(self.buttons):
                if button.contains(pos):
                    self._select(i)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for button in self.buttons:
                if button.contains(pos):
                    button.activate()

    def update(self, dt):
        self.time += dt          # without this line nothing on the menu animates

        # re-check language / save file about once a second (cheap)
        if prefs.get("language") != self._lang or int(self.time) != self._save_check:
            self._save_check = int(self.time)
            self._refresh_buttons()

        for i, button in enumerate(self.buttons):
            p = max(0.0, min(1.0, (self.time - SLIDE_DELAY - i * SLIDE_STAGGER) / SLIDE_TIME))
            button.offset_x = -int((1 - p) ** 3 * 150)       # ease-out slide from the left
            button.update(dt)

        for name, volume in self.backdrop.consume_sounds():
            sfx.play(name, volume)

    def draw(self, surface):
        self.backdrop.draw(surface, self.time)
        if self.backdrop.has_title:
            self.backdrop.draw_title(surface, (160, 34))
        else:
            theme.draw_text(surface, "BAYANSAFE", (160, 28), "title",
                            theme.HONEY, anchor="center")
        for button in self.buttons:
            button.draw(surface, self.time)

        menu_fx.draw_alert_chip(surface, self.time, self.backdrop.level, self.backdrop.hazard)
        menu_fx.draw_gobag(surface, self.time)
        menu_fx.draw_footer(surface, self.time)