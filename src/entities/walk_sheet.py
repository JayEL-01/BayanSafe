import pygame

ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}   # row order of sheets
FRAME_COLUMNS = {"down": (0, 1, 2, 3), "left": (0, 1, 2, 3),
                 "right": (2, 3, 2, 3), "up": (0, 1, 2, 3)}


class WalkSheet:
    """Cuts a 4x4 walking sheet and picks the right frame."""

    def __init__(self, path, height=24, fps=8, mirror_right=True):
        sheet = pygame.image.load(path)
        try:
            if pygame.display.get_surface() is not None:
                sheet = sheet.convert_alpha()
        except Exception:
            pass
        fw, fh = sheet.get_width() // 4, sheet.get_height() // 4
        w = round(fw * height / fh)
        self.frames = {}
        for name, row in ROWS.items():
            source_row = ROWS["left"] if name == "right" and mirror_right else row
            source_columns = FRAME_COLUMNS["left"] if name == "right" and mirror_right else FRAME_COLUMNS[name]
            frames = [
                pygame.transform.scale(
                    sheet.subsurface((c * fw, source_row * fh, fw, fh)), (w, height)
                )
                for c in source_columns
            ]
            if name == "right" and mirror_right:
                frames = [pygame.transform.flip(frame, True, False) for frame in frames]
            self.frames[name] = frames
        self.size = (w, height)
        self.fps = fps
        self.facing = "down"
        self.timer = 0.0
        self.index = 0

    def image_for(self, direction, moving=True, phase=0):
        """Return a directional pose without changing the shared animation clock."""
        if not moving:
            return self.frames.get(direction, self.frames["down"])[0]
        frames = self.frames.get(direction, self.frames["down"])
        return frames[int(phase) % len(frames)]

    def update(self, dt, dx, dy):
        """dx, dy = which way the player is walking (0 if standing)."""
        if dx or dy:
            if abs(dx) > abs(dy) + 0.12:
                self.facing = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) + 0.12:
                self.facing = "down" if dy > 0 else "up"
            self.timer += dt
            self.index = int(self.timer * self.fps) % 4
        else:
            self.timer = 0.0
            self.index = 0          # standing pose

    def image(self):
        return self.frames[self.facing][self.index]
