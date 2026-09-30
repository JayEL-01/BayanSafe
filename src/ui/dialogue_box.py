import pygame
from src.ui import theme
from src.core import settings
from src.utils.helpers import wrap_text


class DialogueBox:
    def __init__(self, font):
        self.font = font
        self.lines = []
        self.index = 0
        self.speaker = ""
        self.active = False
        self.chars = 0.0
        self.on_finish = None

    def open(self, speaker, lines, on_finish=None):
        self.speaker, self.lines = speaker, lines
        self.index, self.chars = 0, 0.0
        self.active = True
        self.on_finish = on_finish

    def advance(self):
        """Press interact: finish typing, or go to the next line."""
        if not self.active:
            return
        if self.chars < len(self.lines[self.index]):
            self.chars = len(self.lines[self.index])
            return
        self.index += 1
        self.chars = 0.0
        if self.index >= len(self.lines):
            self.active = False
            if self.on_finish:
                self.on_finish()

    def update(self, dt):
        if self.active:
            self.chars += 40 * dt

    def draw(self, surface):
        if not self.active:
            return
        box = pygame.Rect(8, settings.INTERNAL_HEIGHT - 62, settings.INTERNAL_WIDTH - 16, 56)
        theme.draw_panel(surface, box, title=self.speaker.upper(), accent=theme.HONEY)

        shown = self.lines[self.index][:int(self.chars)]
        for i, line in enumerate(wrap_text(shown, self.font, box.w - 14)[:3]):
            theme.draw_text(surface, line, (box.x + 7, box.y + 19 + i * 11),
                            self.font, theme.CREAM, shadow=False)

        if self.chars >= len(self.lines[self.index]) and (pygame.time.get_ticks() // 400) % 2 == 0:
            x, y = box.right - 12, box.bottom - 9
            pygame.draw.polygon(surface, theme.HONEY, [(x, y), (x + 6, y), (x + 3, y + 4)])