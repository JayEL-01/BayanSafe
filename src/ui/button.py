import pygame

from src.ui import theme


class Button:
    def __init__(self, text, rect, callback, font=None, icon=None):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = font
        self.icon = icon
        self.selected = False

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def activate(self):
        self.callback()

    def draw(self, surface, t=None):
        theme.draw_button(surface, self.rect, self.text, self.selected,
                          font=self.font, icon=self.icon, t=t)