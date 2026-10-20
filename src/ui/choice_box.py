import pygame

from src.core import settings
from src.ui import theme
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
        self.active = bool(options)

    def handle_key(self, key):
        if not self.active or not self.options:
            return
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

        width = settings.INTERNAL_WIDTH - 12
        text_width = width - 20
        prompt_lines = wrap_text(self.prompt, self.font, text_width)[:3]
        option_lines = [wrap_text(option["text"], self.font, text_width - 12)[:3]
                        for option in self.options]
        row_heights = [max(13, len(lines) * 9 + 5) for lines in option_lines]
        height = 16 + max(1, len(prompt_lines)) * 9 + sum(row_heights) + 11
        # Anchor the choice card above the in-game control rail. The actual
        # authored choices fit comfortably in this space.
        height = min(height, settings.INTERNAL_HEIGHT - 44)
        box = pygame.Rect(6, settings.INTERNAL_HEIGHT - height - 20, width, height)

        old_clip = surface.get_clip()
        surface.set_clip(box.clip(old_clip))
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill((13, 20, 37, 248))
        surface.blit(panel, box.topleft)
        pygame.draw.rect(surface, (249, 200, 91), box, 1)
        pygame.draw.line(surface, (97, 119, 145), (box.x + 5, box.y + 13),
                         (box.right - 5, box.y + 13), 1)

        theme.draw_text(surface, self.speaker.upper(), (box.x + 8, box.y + 2),
                        self.font, theme.HONEY, shadow=False)
        y = box.y + 17
        for line in prompt_lines:
            theme.draw_text(surface, line, (box.x + 8, y), self.font,
                            theme.CREAM, shadow=False)
            y += 9

        y += 2
        for index, (option, lines, row_height) in enumerate(
                zip(self.options, option_lines, row_heights)):
            selected = index == self.selected
            row = pygame.Rect(box.x + 4, y, box.w - 8, row_height - 1)
            if selected:
                pygame.draw.rect(surface, (91, 72, 40), row)
                pygame.draw.rect(surface, (249, 200, 91), row, 1)
                pygame.draw.polygon(surface, theme.HONEY,
                                    [(row.x + 4, row.centery), (row.x + 8, row.centery - 3),
                                     (row.x + 8, row.centery + 3)])
            else:
                pygame.draw.rect(surface, (35, 45, 62), row)
            color = (255, 250, 225) if selected else (204, 218, 235)
            for line_index, line in enumerate(lines):
                theme.draw_text(surface, line, (row.x + 12, row.y + 1 + line_index * 9),
                                self.font, color, shadow=False)
            y += row_height

        theme.draw_text(surface, "UP / DOWN choose     ENTER select",
                        (box.centerx, box.bottom - 9), self.font,
                        (176, 194, 218), anchor="midtop", shadow=False)
        surface.set_clip(old_clip)
