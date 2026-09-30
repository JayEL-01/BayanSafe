import pygame

from src.core import settings
from src.utils.helpers import wrap_text


class ChoiceBox:
    def __init__(self, font):
        self.font = font
        self.active = False
        self.speaker = ""
        self.prompt = ""
        self.options = []
        self.selected = 0
        self.on_choose = None

    def open(self, speaker, prompt, options, on_choose):
        self.speaker, self.prompt = speaker, prompt
        self.options, self.on_choose = options, on_choose
        self.selected = 0
        self.active = True

    def handle_key(self, key):
        if key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.options)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.options)
        elif key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
            option = self.options[self.selected]
            self.active = False
            self.on_choose(option)

    def draw(self, surface):
        if not self.active:
            return
        height = 38 + len(self.options) * 12
        box = pygame.Rect(8, settings.INTERNAL_HEIGHT - height - 6,
                          settings.INTERNAL_WIDTH - 16, height)
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill((15, 25, 55, 240))
        surface.blit(panel, box.topleft)
        pygame.draw.rect(surface, (255, 200, 60), box, 1)

        name = self.font.render(self.speaker.upper(), False, (255, 200, 60))
        surface.blit(name, (box.x + 6, box.y + 4))
        for i, line in enumerate(wrap_text(self.prompt, self.font, box.w - 12)[:2]):
            surface.blit(self.font.render(line, False, (255, 255, 255)),
                         (box.x + 6, box.y + 15 + i * 10))

        y = box.y + 38
        for i, option in enumerate(self.options):
            chosen = i == self.selected
            color = (255, 220, 80) if chosen else (200, 210, 235)
            prefix = "> " if chosen else "  "
            surface.blit(self.font.render(prefix + option["text"], False, color),
                         (box.x + 8, y + i * 12))