class StateManager:
    """Keeps a stack of states. The top one is the active screen."""

    def __init__(self):
        self.stack = []

    def push(self, state):
        """Put a new state on top (e.g. Pause over a Stage)."""
        self.stack.append(state)
        state.enter()

    def pop(self):
        """Remove the top state (e.g. close Pause)."""
        if self.stack:
            self.stack.pop().exit()

    def change(self, state):
        """Replace the top state with a new one."""
        self.pop()
        self.push(state)

    def current(self):
        return self.stack[-1] if self.stack else None