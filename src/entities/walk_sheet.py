import pygame

ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}   # row order of your sheets
# The right-facing row in the supplied character sheets begins with two
# left-facing frames. Reuse the two true right-facing frames to prevent a turn.
FRAME_COLUMNS = {"down": (0, 1, 2, 3), "left": (0, 1, 2, 3),
                 "right": (2, 3, 2, 3), "up": (0, 1, 2, 3)}


class WalkSheet:
    """Cuts a 4x4 walking sheet and picks the right frame."""

    def __init__(self, path, height=24, fps=8, mirror_right=True):
        sheet = pygame.image.load(path).convert_alpha()
        fw, fh = sheet.get_width() // 4, sheet.get_height() // 4
        w = round(fw * height / fh)
        self.frames = {}
        for name, row in ROWS.items():
            # The supplied right-facing row contains frames facing left during
            # part of its cycle. Mirror the consistent left row instead.
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
            # Keep the last facing through near-diagonal input so tiny changes
            # in key timing do not make the sprite flicker between directions.
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


class ReferencePlayerSheet:
    """Adapter for the reference pack's two-idle/four-walk/four-direction atlas."""

    def __init__(self, character_id, height=25, fps=8):
        from src.entities.reference_art import GAME_ART_DIR

        character = "maria" if str(character_id).casefold() == "maria" else "juan"
        self.frames = {}
        self.facing = "down"
        self.timer = 0.0
        self.index = 0
        self.fps = fps
        rows = {"down": 0, "left": 1, "right": 2, "up": 3}
        width = max(1, round(height * 0.72))
        for direction, row in rows.items():
            frames = []
            for column in range(2, 6):
                path = GAME_ART_DIR / "player_frames" / f"{character}_{row}_{column}.png"
                frame = pygame.image.load(str(path)).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
                frames.append(frame)
            self.frames[direction] = frames
        idle_path = GAME_ART_DIR / "player_frames" / f"{character}_0_0.png"
        self.idle = pygame.image.load(str(idle_path)).convert_alpha()
        self.idle = pygame.transform.scale(self.idle, (width, height))
        self.size = (width, height)

    def update(self, dt, dx, dy):
        if dx or dy:
            if abs(dx) > abs(dy) + 0.12:
                self.facing = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) + 0.12:
                self.facing = "down" if dy > 0 else "up"
            self.timer += dt
            self.index = int(self.timer * self.fps) % 4
        else:
            self.timer = 0.0
            self.index = 0

    def image(self):
        if self.timer <= 0:
            return self.idle if self.facing == "down" else self.frames[self.facing][0]
        return self.frames[self.facing][self.index]
