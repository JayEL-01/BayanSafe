import pygame

from src.states.base_state import BaseState


class PlaceholderState(BaseState):
    def __init__(self, game, title):
        super().__init__(game)
        self.title = title
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 16)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_BACKSPACE
        ):
            self.game.state_manager.pop()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.game.state_manager.pop()

    def draw(self, surface):
        surface.fill((20, 30, 60))
        title = self.font.render(self.title, False, (255, 200, 60))
        info = self.small.render("Coming soon", False, (255, 255, 255))
        hint = self.small.render("ESC or click to go back", False, (150, 170, 210))
        surface.blit(title, title.get_rect(center=(160, 70)))
        surface.blit(info, info.get_rect(center=(160, 95)))
        surface.blit(hint, hint.get_rect(center=(160, 150)))