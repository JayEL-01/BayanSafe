class EventBus:
    """Systems call emit() to announce something; others subscribe()."""

    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, callback):
        self.listeners.setdefault(event_name, []).append(callback)

    def emit(self, event_name, **data):
        for callback in self.listeners.get(event_name, []):
            callback(**data)