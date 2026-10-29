import pygame
from src.ui import theme
from src.core import settings
from src.utils.helpers import wrap_text


class DialogueBox:
    BUBBLE_TOP = 28
    BUBBLE_BOTTOM = 158
    BUBBLE_SIDE_GAP = 12

    def __init__(self, font):
        self.font = font
        self.lines = []
        self.index = 0
        self.speaker = ""
        self.active = False
        self.chars = 0.0
        self.on_finish = None

    def open(self, speaker, lines, on_finish=None):
        self.speaker = str(speaker or "NEIGHBOR")
        self.lines = [str(line) for line in (lines or []) if str(line).strip()] or ["..."]
        self.index, self.chars = 0, 0.0
        self.active = True
        self.on_finish = on_finish

    def advance(self):
        """Press interact: finish typing, or go to the next line."""
        if not self.active:
            return
        if self.chars < len(self.lines[self.index]):
            self.chars = len(self.lines[self.index])
            return
        self.index += 1
        self.chars = 0.0
        if self.index >= len(self.lines):
            self.active = False
            if self.on_finish:
                self.on_finish()

    def update(self, dt):
        if self.active:
            self.chars += 40 * dt

    def draw(self, surface, anchor=None, avoid_rects=()):
        if not self.active:
            return
        if anchor is None:
            # Keep the dialogue clear of the fixed in-game controls rail.
            box = pygame.Rect(8, settings.INTERNAL_HEIGHT - 76, settings.INTERNAL_WIDTH - 16, 56)
            theme.draw_panel(surface, box, title=self.speaker.upper(), accent=theme.HONEY)
            shown = self.lines[self.index][:int(self.chars)]
            lines = wrap_text(shown, self.font, box.w - 24)[:3]
            text_x, text_y, line_gap = box.x + 7, box.y + 19, 11
        else:
            width = min(190, settings.INTERNAL_WIDTH - 18)
            shown = self.lines[self.index][:int(self.chars)]
            # Reserve a small corner for the advance marker so it cannot sit
            # on top of the final word in a long dialogue line.
            lines = wrap_text(shown, self.font, width - 24)[:5]
            height = 19 + max(1, len(lines)) * 10
            candidates = []
            for x, y, side in (
                (anchor[0] - width // 2, anchor[1] - height - 10, "bottom"),
                (anchor[0] - width // 2, anchor[1] + 10, "top"),
                (anchor[0] - width - 10, anchor[1] - height // 2, "right"),
                (anchor[0] + 10, anchor[1] - height // 2, "left"),
            ):
                x = max(self.BUBBLE_SIDE_GAP,
                        min(x, settings.INTERNAL_WIDTH - width - self.BUBBLE_SIDE_GAP))
                # The game reserves y=0..21 for status and y=164..180 for
                # controls. Leave room for the bubble tail as well.
                y = max(self.BUBBLE_TOP, min(y, self.BUBBLE_BOTTOM - height))
                candidate = pygame.Rect(x, y, width, height)
                candidates.append((candidate, side))
            clear = next(
                ((rect, side) for rect, side in candidates
                 if not any(rect.colliderect(avoid) for avoid in avoid_rects)),
                None,
            )
            if clear:
                box, tail_side = clear
            else:
                # Fallback stays centered in the playable field, never on the
                # HUD rails, even when every character-side placement is busy.
                box = pygame.Rect((settings.INTERNAL_WIDTH - width) // 2,
                                  max(self.BUBBLE_TOP,
                                      (self.BUBBLE_TOP + self.BUBBLE_BOTTOM - height) // 2),
                                  width, height)
                tail_side = "top"
            pygame.draw.rect(surface, (10, 15, 26), box.inflate(2, 2))
            pygame.draw.rect(surface, (248, 244, 222), box)
            pygame.draw.rect(surface, (245, 190, 76), box, 1)
            theme.draw_text(surface, self.speaker, (box.x + 7, box.y + 3),
                            self.font, (143, 85, 40), shadow=False)
            text_x, text_y, line_gap = box.x + 7, box.y + 13, 10
            tip_x = max(box.x + 9, min(anchor[0], box.right - 9))
            tip_y = max(box.y + 8, min(anchor[1], box.bottom - 8))
            if tail_side == "bottom":
                pygame.draw.polygon(surface, (248, 244, 222),
                                    [(tip_x - 4, box.bottom - 1), (tip_x + 4, box.bottom - 1),
                                     (tip_x, box.bottom + 6)])
            elif tail_side == "top":
                pygame.draw.polygon(surface, (248, 244, 222),
                                    [(tip_x - 4, box.y + 1), (tip_x + 4, box.y + 1),
                                     (tip_x, box.y - 6)])
            elif tail_side == "right":
                pygame.draw.polygon(surface, (248, 244, 222),
                                    [(box.right - 1, tip_y - 4), (box.right - 1, tip_y + 4),
                                     (box.right + 6, tip_y)])
            else:
                pygame.draw.polygon(surface, (248, 244, 222),
                                    [(box.x + 1, tip_y - 4), (box.x + 1, tip_y + 4),
                                     (box.x - 6, tip_y)])

        for i, line in enumerate(lines):
            color = theme.CREAM if anchor is None else (36, 43, 46)
            theme.draw_text(surface, line, (text_x, text_y + i * line_gap),
                            self.font, color, shadow=False)

        if self.chars >= len(self.lines[self.index]) and (pygame.time.get_ticks() // 400) % 2 == 0:
            x, y = box.right - 12, box.bottom - 9
            pygame.draw.polygon(surface, theme.HONEY, [(x, y), (x + 6, y), (x + 3, y + 4)])
