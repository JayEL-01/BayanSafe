import pygame

from src.core import settings
from src.states.base_state import BaseState


class TestState(BaseState):
    def __init__(self, game, name):
        super().__init__(game)
        self.name = name
        self.color = (30, 60, 120) if name == "A" else (120, 40, 40)
        self.font = pygame.font.Font(None, 20)
        self.box_x = 0.0  # moving square, proves dt works

    def enter(self):
        print(f"Entered state {self.name}")

    def exit(self):
        print(f"Exited state {self.name}")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                next_name = "B" if self.name == "A" else "A"
                self.game.state_manager.change(TestState(self.game, next_name))
            elif event.key == pygame.K_ESCAPE:
                self.game.quit()

    def update(self, dt):
        self.box_x += 60 * dt  # 60 pixels per second
        if self.box_x > settings.INTERNAL_WIDTH:
            self.box_x = -16

    def draw(self, surface):
        surface.fill(self.color)
        pygame.draw.rect(surface, (255, 220, 80), (int(self.box_x), 100, 16, 16))
        text = self.font.render(f"STATE {self.name}  -  SPACE to switch", False, (255, 255, 255))
        surface.blit(text, (10, 10))