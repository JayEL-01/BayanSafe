class BaseState:
    """Parent class for every game screen."""

    def __init__(self, game):
        self.game = game

    def enter(self):
        """Called once when this state becomes active."""
        pass

    def exit(self):
        """Called once when this state is removed."""
        pass

    def handle_event(self, event):
        """Called for each keyboard/mouse event."""
        pass

    def update(self, dt):
        """Called every frame. dt = seconds since last frame."""
        pass

    def draw(self, surface):
        """Called every frame. Draw onto the given surface."""
        pass