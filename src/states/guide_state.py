import pygame

from src.core import settings
from src.core.strings import guide, tr
from src.states.base_state import BaseState
from src.ui import sfx, theme
from src.ui.button import Button

ACCENTS = [theme.SKY, theme.CORAL, theme.SAGE, (240, 150, 80), (220, 80, 60)]
W = settings.INTERNAL_WIDTH


def _wrap(font, text, width):
    lines, current = [], ""
    for word in text.split():
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class GuideState(BaseState):
    """Three-page hazard guide: typhoon, earthquake, flood. LEFT/RIGHT to flip pages."""

    def __init__(self, game):
        super().__init__(game)
        self.backdrop = theme.CozyBackdrop()
        self.time = 0.0
        self.page = 0
        self.back_button = Button("", (W // 2 - 35, 146, 70, 16), self.back)
        self.back_button.selected = True
        self.left = pygame.Rect(30, 82, 12, 16)
        self.right = pygame.Rect(W - 42, 82, 12, 16)

    def back(self):
        self.game.state_manager.pop()      # if your StateManager names this differently, change it here

    def _flip(self, step):
        count = len(guide())
        self.page = (self.page + step) % count
        sfx.play("tock", 0.3)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._flip(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._flip(1)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN):
                self.back()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            if self.left.collidepoint(pos):
                self._flip(-1)
            elif self.right.collidepoint(pos):
                self._flip(1)
            elif self.back_button.contains(pos):
                self.back_button.activate()

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        pages = guide()
        data = pages[self.page % len(pages)]
        accent = ACCENTS[self.page % len(ACCENTS)]

        self.backdrop.draw(surface, self.time)
        theme.dim(surface, 110)
        panel = pygame.Rect(24, 10, W - 48, 160)
        theme.draw_panel(surface, panel, tr("guide_title"), accent)

        theme.draw_text(surface, data["title"], (W // 2, 31), "heading", accent, anchor="center")

        font = theme.get_font("body")
        y = 46
        for line in data["lines"]:
            for i, text in enumerate(_wrap(font, line, 220)):
                if i == 0:
                    pygame.draw.rect(surface, theme.HONEY, (50, y + 3, 2, 2))
                theme.draw_text(surface, text, (56, y), "body", theme.CREAM, shadow=False)
                y += 10
            y += 4

        # page arrows and dots
        cy = self.left.centery
        pygame.draw.polygon(surface, accent, [(self.left.right, cy - 5), (self.left.right, cy + 5), (self.left.x + 2, cy)])
        pygame.draw.polygon(surface, accent, [(self.right.x, cy - 5), (self.right.x, cy + 5), (self.right.right - 2, cy)])
        for i in range(len(pages)):
            color = accent if i == self.page else theme.PLUM_LIGHT
            pygame.draw.rect(surface, color, (W // 2 - len(pages) * 4 + i * 8, 133, 4, 4))

        self.back_button.text = tr("back")
        self.back_button.draw(surface, self.time)
        theme.draw_text(surface, tr("hint_guide"), (W // 2, 174), "tiny",
                        theme.CREAM_DIM, shadow=False, anchor="center")