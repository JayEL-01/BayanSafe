import pygame

from src.ui import sfx, theme


class Button:
    """Backward compatible: Button(text, rect, callback) still works everywhere.

    Extras (used by the main menu):
      icon         name from theme.ICONS
      press_delay  seconds the button stays pressed (1 px down + thud) before the
                   callback runs. Needs update(dt) to be called every frame.
      enabled      False = greyed out, click does nothing
      offset_x     draw offset, used for the slide-in animation
    """

    def __init__(self, text, rect, callback, font=None, icon=None, press_delay=0.0):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = font
        self.icon = icon
        self.press_delay = press_delay
        self.selected = False
        self.enabled = True
        self.offset_x = 0
        self._pending = False
        self._timer = 0.0

    def contains(self, pos):
        return self.offset_x == 0 and self.rect.collidepoint(pos)

    def activate(self):
        if self._pending:
            return
        if not self.enabled:
            sfx.play("tock", 0.25)
            return
        if self.press_delay <= 0:
            self.callback()
            return
        sfx.play("thud", 0.6)
        self._pending = True
        self._timer = self.press_delay

    def update(self, dt):
        if self._pending:
            self._timer -= dt
            if self._timer <= 0:
                self._pending = False
                self.callback()

    def draw(self, surface, t=None):
        rect = self.rect.move(self.offset_x, 1 if self._pending else 0)
        theme.draw_button(surface, rect, self.text, self.selected, font=self.font,
                          icon=self.icon, t=t, disabled=not self.enabled)