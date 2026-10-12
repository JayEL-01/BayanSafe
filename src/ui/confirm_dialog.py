import pygame

from src.core import audio, prefs
from src.ui import theme
from src.utils.helpers import wrap_text

# English + Filipino built in, so it follows the Options language without touching strings.py
EXIT_TEXTS = {
    "en": ("Leave BayanSafe?", "Are you sure you want to quit the game?", "STAY", "QUIT"),
    "fil": ("Aalis ka na?", "Sigurado ka bang gusto mong umalis sa laro?", "MANATILI", "UMALIS"),
}


def exit_texts():
    return EXIT_TEXTS.get(prefs.get("language"), EXIT_TEXTS["en"])


class ConfirmDialog:
    """A wooden 'are you sure?' box with two buttons. Drawn by the screen that owns it.

        self.dialog = ConfirmDialog(*exit_texts(), on_yes=self.game.quit)
        # in handle_event:  if self.dialog.active: self.dialog.handle_event(event, self.game); return
        # in update:        self.dialog.update(dt)
        # in draw (last):   if self.dialog.active: theme.dim(surface, 150); self.dialog.draw(surface)

    Tip: while it is open, skip drawing the other text on that screen, because text is
    drawn after the canvas and would show on top of the dialog.
    LEFT/RIGHT (or A/D, UP/DOWN) move, OK/ENTER/SPACE choose, ESC = the 'no' button.
    The 'no' button (left) is selected first, so a stray press does not quit.
    """

    RECT = pygame.Rect(60, 48, 200, 84)

    def __init__(self, title, message, no_text, yes_text, on_yes, on_no=None):
        self.title, self.message = title, message
        self.no_text, self.yes_text = no_text, yes_text
        self.on_yes, self.on_no = on_yes, on_no
        self.active = False
        self.selected = 0            # 0 = no (left), 1 = yes (right)
        self.t = 0.0
        self.font = theme.get_font("tiny")
        self.lines = wrap_text(message, self.font, 170)[:2]
        self.buttons = [pygame.Rect(80, 108, 76, 16), pygame.Rect(164, 108, 76, 16)]

    # ---------- open / close ----------
    def open(self):
        self.active = True
        self.selected = 0
        self.t = 0.0
        audio.play("whoosh", 0.3)

    def close(self):
        self.active = False

    def _choose(self, yes):
        self.close()
        audio.play("back" if yes else "confirm")
        callback = self.on_yes if yes else self.on_no
        if callback:
            callback()

    def _move(self, index):
        if index != self.selected:
            self.selected = index
            audio.play("tick")

    # ---------- state-like API ----------
    def handle_event(self, event, game):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self._move(0)
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self._move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._choose(self.selected == 1)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self._choose(False)
        elif event.type == pygame.MOUSEMOTION:
            pos = game.to_canvas_pos(event.pos)
            for i, rect in enumerate(self.buttons):
                if rect.collidepoint(pos):
                    self._move(i)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = game.to_canvas_pos(event.pos)
            for i, rect in enumerate(self.buttons):
                if rect.collidepoint(pos):
                    self._choose(i == 1)

    def update(self, dt):
        if self.active:
            self.t += dt

    def draw(self, surface):
        if not self.active:
            return
        drop = -int((1 - min(1.0, self.t / 0.2)) ** 2 * 50)      # the sign drops in from above
        r = self.RECT.move(0, drop)

        # wooden sign
        pygame.draw.rect(surface, theme.SHADOW, r.move(2, 3))
        pygame.draw.rect(surface, theme.WOOD_DARK, r)
        for gy in range(r.y + 5, r.bottom - 3, 6):
            pygame.draw.line(surface, theme.mix(theme.WOOD_DARK, theme.SHADOW, 0.25),
                             (r.x + 6, gy), (r.right - 7, gy))
        pygame.draw.rect(surface, theme.WOOD_LIGHT, r, 1)
        pygame.draw.line(surface, theme.mix(theme.WOOD_DARK, theme.CREAM, 0.25),
                         (r.x + 2, r.y + 1), (r.right - 3, r.y + 1))
        for nx, ny in ((r.x + 4, r.y + 4), (r.right - 5, r.y + 4),
                       (r.x + 4, r.bottom - 5), (r.right - 5, r.bottom - 5)):
            pygame.draw.rect(surface, theme.CREAM_DIM, (nx, ny, 2, 2))          # nails

        theme.draw_text(surface, self.title, (r.centerx, r.y + 6), "button", theme.HONEY, anchor="midtop")
        for n, line in enumerate(self.lines):
            theme.draw_text(surface, line, (r.centerx, r.y + 24 + n * 9), self.font,
                            theme.CREAM, anchor="midtop")

        for i, (rect, text) in enumerate(zip(self.buttons, (self.no_text, self.yes_text))):
            theme.draw_button(surface, rect.move(0, drop), text, selected=(i == self.selected))