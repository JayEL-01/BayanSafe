import pygame

from src.core import settings
from src.core.session import GameSession
from src.core.state_manager import StateManager
from src.ui import theme
from src.ui.confirm_dialog import ConfirmDialog, exit_texts
from src.hardware.pygame_controller import PygameController


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
        self.controller = PygameController()
        self.exit_dialog = None          # the "Leave BayanSafe?" box (made when needed)

    def quit(self):
        self.running = False

    def ask_quit(self):
        """Opens the 'are you sure?' box. Use this instead of quit() from buttons and keys."""
        if self.exit_dialog and self.exit_dialog.active:
            return
        self.exit_dialog = ConfirmDialog(*exit_texts(), on_yes=self.quit)   # re-reads the language
        self.exit_dialog.open()

    @property
    def dialog_open(self):
        return bool(self.exit_dialog and self.exit_dialog.active)

    def to_canvas_pos(self, pos):
        """Convert a window mouse position to canvas position."""
        return (pos[0] // settings.SCALE, pos[1] // settings.SCALE)

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000  # seconds
            controller_events = self.controller.poll_events(dt)

            for event in [*pygame.event.get(), *controller_events]:
                if event.type == pygame.QUIT:                 # the window's X button
                    if self.dialog_open:
                        self.quit()                           # pressing X again really closes it
                    else:
                        self.ask_quit()
                elif self.dialog_open:
                    self.exit_dialog.handle_event(event, self)
                else:
                    # A prior event may have changed screens. Always dispatch
                    # to the current screen so one input batch cannot operate
                    # on a stale state after a transition.
                    state = self.state_manager.current()
                    if state is not None:
                        state.handle_event(event)

            if self.dialog_open:
                self.exit_dialog.update(dt)                   # the screen underneath is frozen
            else:
                state = self.state_manager.current()
                if state is None:
                    break
                state.update(dt)

            # update() can also finish a mission or open the next screen.
            state = self.state_manager.current()
            if state is None:
                break

            theme.TEXT_QUEUE.clear()
            self.canvas.fill((0, 0, 0))
            state.draw(self.canvas)

            if self.dialog_open:
                theme.TEXT_QUEUE.clear()                      # the screen's own text would draw over the box
                theme.dim(self.canvas, 150)
                self.exit_dialog.draw(self.canvas)

            # Scale the small canvas up to the window (pixel art)...
            pygame.transform.scale(
                self.canvas, self.window.get_size(), self.window
            )
            # ...then draw smooth text on top, at full resolution.
            theme.flush_text(self.window)
            pygame.display.flip()

        pygame.quit()
