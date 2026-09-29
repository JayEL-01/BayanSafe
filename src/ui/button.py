import pygame


class Button:
    """A clickable button. Reusable on every screen."""

    def __init__(self, text, rect, callback, font):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback  # function to run when activated
        self.font = font
        self.selected = False

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def activate(self):
        self.callback()

    def draw(self, surface):
        if self.selected:
            fill, border, text_color = (255, 200, 60), (255, 255, 255), (30, 30, 30)
        else:
            fill, border, text_color = (40, 60, 110), (120, 150, 210), (255, 255, 255)

        pygame.draw.rect(surface, fill, self.rect)
        pygame.draw.rect(surface, border, self.rect, 1)

        label = self.font.render(self.text, False, text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))