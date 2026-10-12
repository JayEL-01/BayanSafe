import pygame

ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}   # row order of your sheets


class WalkSheet:
    """Cuts a 4x4 walking sheet and picks the right frame."""

    def __init__(self, path, height=24, fps=8):
        sheet = pygame.image.load(path).convert_alpha()
        fw, fh = sheet.get_width() // 4, sheet.get_height() // 4
        w = round(fw * height / fh)
        self.frames = {}
        for name, row in ROWS.items():
            self.frames[name] = [
                pygame.transform.scale(sheet.subsurface((c * fw, row * fh, fw, fh)), (w, height))
                for c in range(4)
            ]
        self.size = (w, height)
        self.fps = fps
        self.facing = "down"
        self.timer = 0.0
        self.index = 0

    def update(self, dt, dx, dy):
        """dx, dy = which way the player is walking (0 if standing)."""
        if dx or dy:
            if abs(dx) > abs(dy):
                self.facing = "right" if dx > 0 else "left"
            else:
                self.facing = "down" if dy > 0 else "up"
            self.timer += dt
            self.index = int(self.timer * self.fps) % 4
        else:
            self.timer = 0.0
            self.index = 0          # standing pose

    def image(self):
        return self.frames[self.facing][self.index]