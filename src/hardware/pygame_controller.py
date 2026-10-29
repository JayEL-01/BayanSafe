"""Optional USB HID joystick/buttons adapter using Pygame's standard input API.

Custom serial boards should implement the same high-level key-event contract
after their protocol and pinout are confirmed.
"""
import pygame


class PygameController:
    DEFAULT_BUTTONS = {
        0: pygame.K_RETURN,   # confirm / primary large button
        1: pygame.K_ESCAPE,   # back / secondary large button
        2: pygame.K_UP,       # small button 1: previous option / menu item
        3: pygame.K_DOWN,     # small button 2: next option / menu item
    }

    def __init__(self, deadzone=0.28, repeat_delay=0.36, repeat_rate=0.16):
        pygame.joystick.init()
        self.deadzone = float(deadzone)
        self.repeat_delay = float(repeat_delay)
        self.repeat_rate = float(repeat_rate)
        self.buttons = dict(self.DEFAULT_BUTTONS)
        self.devices = []
        self.active_axes = {}
        self.repeat_timers = {}
        self.button_state = {}
        self._refresh()

    def _refresh(self):
        count = pygame.joystick.get_count()
        if count != len(self.devices):
            for device in self.devices:
                try:
                    device.quit()
                except pygame.error:
                    pass
            self.devices.clear()
            self.active_axes.clear()
            self.repeat_timers.clear()
            self.button_state.clear()
        while len(self.devices) < count:
            joystick = pygame.joystick.Joystick(len(self.devices))
            joystick.init()
            self.devices.append(joystick)

    def _post_key(self, key):
        return pygame.event.Event(pygame.KEYDOWN, key=key, repeat=False)

    def poll_events(self, dt):
        """Translate first-controller directions and button edges to game keys."""
        self._refresh()
        if not self.devices:
            self.active_axes.clear()
            self.repeat_timers.clear()
            self.button_state.clear()
            return []
        joystick = self.devices[0]
        events = []
        axes = {}
        try:
            if joystick.get_numaxes() >= 2:
                x, y = joystick.get_axis(0), joystick.get_axis(1)
                axes[pygame.K_LEFT] = x < -self.deadzone
                axes[pygame.K_RIGHT] = x > self.deadzone
                axes[pygame.K_UP] = y < -self.deadzone
                axes[pygame.K_DOWN] = y > self.deadzone
        except pygame.error:
            self.devices.clear()
            self.active_axes.clear()
            self.repeat_timers.clear()
            self.button_state.clear()
            return []
        for key, active in axes.items():
            was_active = self.active_axes.get(key, False)
            if active:
                self.repeat_timers[key] = self.repeat_timers.get(key, 0.0) - dt
                if not was_active or self.repeat_timers[key] <= 0:
                    events.append(self._post_key(key))
                    self.repeat_timers[key] = self.repeat_delay if not was_active else self.repeat_rate
            else:
                self.repeat_timers.pop(key, None)
            self.active_axes[key] = active
        for button, key in self.buttons.items():
            try:
                active = button < joystick.get_numbuttons() and bool(joystick.get_button(button))
            except pygame.error:
                active = False
            if active and not self.button_state.get(button, False):
                events.append(self._post_key(key))
            self.button_state[button] = active
        return events
