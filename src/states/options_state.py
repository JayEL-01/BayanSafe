import pygame

from src.core import audio, prefs, settings
from src.core.strings import tr
from src.states.base_state import BaseState
from src.ui import theme
from src.ui.button import Button
from src.ui.image_backdrop import ImageBackdrop


# the sewn-on canvas patch (matches the tan bag, instead of the old purple panel)
CANVAS = (158, 122, 76)
CANVAS_LIGHT = (196, 158, 102)
CANVAS_DARK = (88, 58, 36)
CANVAS_LINE = (144, 108, 66)     # faint weave lines
STITCH = (236, 212, 160)
PATCH = pygame.Rect(62, 22, 196, 106)


def draw_patch(surface, rect, title):
    """A canvas patch with a header ribbon, stitched edge and four rivets."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, theme.SHADOW, rect.move(2, 3))                  # drop shadow
    pygame.draw.rect(surface, CANVAS, rect)
    for y in range(rect.y + 3, rect.bottom - 2, 4):                           # weave lines
        pygame.draw.line(surface, CANVAS_LINE, (rect.x + 2, y), (rect.right - 3, y))
    pygame.draw.line(surface, CANVAS_LIGHT, (rect.x, rect.y), (rect.right - 1, rect.y))
    pygame.draw.rect(surface, CANVAS_DARK, rect, 1)

    ribbon = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, 15)              # darker header strip
    pygame.draw.rect(surface, theme.mix(CANVAS, CANVAS_DARK, 0.35), ribbon)
    pygame.draw.line(surface, CANVAS_DARK, (ribbon.x, ribbon.bottom), (ribbon.right - 1, ribbon.bottom))

    inner = rect.inflate(-8, -8)                                              # dashed stitching
    for x in range(inner.x, inner.right, 4):
        for y in (inner.y, inner.bottom - 1):
            surface.set_at((x, y), STITCH)
            surface.set_at((x + 1, y), STITCH)
    for y in range(inner.y, inner.bottom, 4):
        for x in (inner.x, inner.right - 1):
            surface.set_at((x, y), STITCH)
            surface.set_at((x, y + 1), STITCH)

    for rx, ry in ((rect.x + 5, rect.y + 5), (rect.right - 6, rect.y + 5),
                   (rect.x + 5, rect.bottom - 6), (rect.right - 6, rect.bottom - 6)):
        pygame.draw.circle(surface, CANVAS_DARK, (rx, ry + 1), 2)             # metal rivets
        pygame.draw.circle(surface, (190, 190, 184), (rx, ry), 2)
        surface.set_at((rx - 1, ry - 1), (255, 255, 250))

    theme.draw_text(surface, title, (rect.centerx, rect.y + 8), "button", theme.CREAM,
                    anchor="center")


class OptionsState(BaseState):
    """Language (English / Filipino) and sound on/off preferences."""

    def __init__(self, game):
        super().__init__(game)
        self.backdrop = ImageBackdrop("options_bg.png")     # the inside of a go-bag
        self.time = 0.0
        self.selected = 0
        w, h, gap = 150, 18, 7
        x = (settings.INTERNAL_WIDTH - w) // 2
        self.rects = [pygame.Rect(x, 48 + i * (h + gap), w, h) for i in range(3)]
        self.buttons = [Button("", tuple(self.rects[i]), cb)
                        for i, cb in enumerate((self.toggle_language, self.toggle_sfx, self.back))]
        self._refresh()
        self._aim()
        self.backdrop.light[:] = self.backdrop.target        # start already lit on the first button

    # ---------- actions ----------
    def toggle_language(self):
        prefs.put("language", "fil" if prefs.get("language") == "en" else "en")
        audio.play("tock", 0.4)
        self._refresh()

    def toggle_sfx(self):
        prefs.put("sfx", not prefs.get("sfx"))
        audio.play("tock", 0.4)
        self._refresh()

    def back(self):
        audio.play("back")
        self.game.state_manager.pop()      # if your StateManager names this differently, change it here

    def _refresh(self):
        self.buttons[0].text = f"{tr('language')}: {tr('lang_name')}"
        self.buttons[1].text = f"{tr('sfx')}: {tr('on') if prefs.get('sfx') else tr('off')}"
        self.buttons[2].text = tr("back")
        for i, b in enumerate(self.buttons):
            b.selected = (i == self.selected)

    def _aim(self):
        """Point the flashlight at the selected button."""
        r = self.rects[self.selected]
        self.backdrop.aim(r.centerx, r.centery)

    def _select(self, i):
        if i != self.selected:
            self.selected = i
            audio.play("tock", 0.3)
            self._refresh()
            self._aim()

    # ---------- state API ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._select((self.selected - 1) % len(self.buttons))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select((self.selected + 1) % len(self.buttons))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT):
                self.buttons[self.selected].activate()
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.back()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for i, b in enumerate(self.buttons):
                if b.contains(pos):
                    self._select(i)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for b in self.buttons:
                if b.contains(pos):
                    b.activate()

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        self.backdrop.draw(surface, self.time)
        draw_patch(surface, PATCH, tr("options_title"))
        for b in self.buttons:
            b.draw(surface, self.time)

        strip = pygame.Surface((settings.INTERNAL_WIDTH, 14), pygame.SRCALPHA)   # keeps the hint readable
        strip.fill((14, 10, 8, 170))
        surface.blit(strip, (0, 158))
        theme.draw_text(surface, tr("hint_options"), (settings.INTERNAL_WIDTH // 2, 165),
                        "tiny", theme.CREAM, shadow=False, anchor="center")
