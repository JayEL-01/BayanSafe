import pygame

from src.core import audio, prefs, settings
from src.core.strings import tr
from src.states.base_state import BaseState
from src.states.character_select import CharacterSelect
from src.states.guide_state import GuideState
from src.states.high_scores import HighScores
from src.states.loading import LoadingScreen
from src.states.options_state import OptionsState
from src.states.new_game_confirm import NewGameConfirm
from src.states.mission_prep import MissionPrep
from src.ui import menu_fx, theme
from src.ui.backdrop import MenuBackdrop
from src.ui.button import Button
from src.utils.data_loader import load_json

ENTRIES = [               # (string key, icon)
    ("new_game", "house"),
    ("continue", "clip"),
    ("guide", "book"),
    ("high_scores", "radio"),
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
        self._slid = set()             # buttons that already played their slide-in sound
        self._lang = prefs.get("language")
        self._save_check = -1
        self.continue_message = ""
        self._build_buttons()
        audio.warm()

    # ---------- setup ----------
    def _build_buttons(self):
        def sounded(fn):
            def run():
                audio.play("confirm")
                fn()
            return run

        actions = {"new_game": sounded(self.new_game), "continue": sounded(self.continue_game),
                   "guide": sounded(self.guide), "high_scores": sounded(self.high_scores),
                   "options": sounded(self.options),
                   "exit": self.game.ask_quit}          # opens the "Leave BayanSafe?" box (in Game)
        width, height, gap = 110, 15, 2
        x = (settings.INTERNAL_WIDTH - width) // 2
        for i, (key, icon) in enumerate(ENTRIES):
            button = Button(tr(key), (x, 59 + i * (height + gap), width, height),
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
        if prefs.has_save():
            self.game.state_manager.push(NewGameConfirm(self.game))
        else:
            self.game.session.reset()
            self.game.state_manager.push(CharacterSelect(self.game))

    def continue_game(self):
        characters = load_json("data/characters.json")
        if self.game.session.load(characters):
            if all(stage in self.game.session.completed for stage in self.game.session.STAGE_ORDER):
                self.continue_message = "Your story is complete. Start a new journey to play again."
                return
            stage_id = self.game.session.current_stage
            self.game.state_manager.push(LoadingScreen(
                self.game, lambda: MissionPrep(self.game, stage_id), "RESUMING YOUR JOURNEY"))
        else:
            self.game.session.erase()
            self._refresh_buttons()

    def guide(self):
        self.game.state_manager.push(GuideState(self.game))

    def high_scores(self):
        self.game.state_manager.push(HighScores(self.game))

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
            audio.play("tick")

    # ---------- state API ----------
    def handle_event(self, event):
        # (while the exit box is open, Game sends the events to the box, not here)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.ask_quit()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._select((self.selected - 1) % len(self.buttons))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select((self.selected + 1) % len(self.buttons))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.selected].activate()
            elif event.key == pygame.K_t:
                self.backdrop.next_time()
            elif event.key == pygame.K_h:
                self.backdrop.next_hazard()
            elif event.key == pygame.K_F2:
                self.backdrop.toggle_debug()
            elif event.key == pygame.K_F3:
                self.backdrop.toggle_boost()

        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            self.backdrop.look_at(pos[0])
            self.backdrop.hover_at(pos)
            for i, button in enumerate(self.buttons):
                if button.contains(pos):
                    self._select(i)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            self.backdrop.poke(pos)                  # clicking the title repairs its casing
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
            if p > 0 and i not in self._slid:                # a soft whoosh as each button slides in
                self._slid.add(i)
                audio.play("whoosh", 0.4)
            button.offset_x = -int((1 - p) ** 3 * 150)       # ease-out slide from the left
            button.update(dt)

        for name, volume in self.backdrop.consume_sounds():
            audio.play(name, volume)

    def draw(self, surface):
        self.backdrop.draw(surface, self.time)
        if self.backdrop.has_title:
            self.backdrop.draw_title(surface, (160, 34))
        else:
            theme.draw_text(surface, "BAYANSAFE", (160, 28), "title", theme.HONEY, anchor="center")
        self.backdrop.draw_hint(surface)
        for button in self.buttons:
            button.draw(surface, self.time)

        menu_fx.draw_alert_chip(surface, self.time, self.backdrop.level, self.backdrop.hazard)
        menu_fx.draw_gobag(surface, self.time)
        menu_fx.draw_footer(surface, self.time)
        menu_fx.draw_banner(surface, self.backdrop.fx)
        if self.continue_message:
            theme.draw_text(surface, self.continue_message, (160, 173), "tiny",
                            theme.CREAM, anchor="center")
