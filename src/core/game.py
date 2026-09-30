import pygame
from src.ui import theme
from src.core import settings
from src.core.state_manager import StateManager
from src.core.session import GameSession

class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(settings.TITLE)

        # Small canvas: all game drawing happens here.
        self.canvas = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        )

        self.clock = pygame.time.Clock()
        self.state_manager = StateManager()
        self.running = True
        self.session = GameSession()
    
    def quit(self):
        self.running = False

    def to_canvas_pos(self, pos):
        """Convert a window mouse position to canvas position."""
        return (pos[0] // settings.SCALE, pos[1] // settings.SCALE)
     
    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000  # seconds

            state = self.state_manager.current()
            if state is None:
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                else:
                    state.handle_event(event)

            state.update(dt)   # <-- this line was missing

            theme.TEXT_QUEUE.clear()
            self.canvas.fill((0, 0, 0))
            state.draw(self.canvas)

            # Scale the small canvas up to the window (pixel art)...
            pygame.transform.scale(
                self.canvas, self.window.get_size(), self.window
            )
            # ...then draw smooth text on top, at full resolution.
            theme.flush_text(self.window)
            pygame.display.flip()

        pygame.quit()