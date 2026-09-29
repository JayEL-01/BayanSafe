import pygame

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
        box = pygame.Rect(8, settings.INTERNAL_HEIGHT - 52, settings.INTERNAL_WIDTH - 16, 46)
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill((15, 25, 55, 235))
        surface.blit(panel, box.topleft)
        pygame.draw.rect(surface, (255, 200, 60), box, 1)

        name = self.font.render(self.speaker.upper(), False, (255, 200, 60))
        surface.blit(name, (box.x + 6, box.y + 4))

        shown = self.lines[self.index][:int(self.chars)]
        for i, line in enumerate(wrap_text(shown, self.font, box.w - 12)[:3]):
            surface.blit(self.font.render(line, False, (255, 255, 255)), (box.x + 6, box.y + 15 + i * 10))

        hint = self.font.render("E / ENTER", False, (150, 170, 210))
        surface.blit(hint, (box.right - hint.get_width() - 5, box.bottom - 11))