import math
import random

import pygame

from src.core import audio, settings
from src.core.strings import guide, tr
from src.states.base_state import BaseState
from src.ui import theme
from src.ui.button import Button
from src.utils.data_loader import BASE_DIR

BG_PATH = "assets/images/ui/guide_bg.png"       # the notebook-on-a-table image
ICON_DIR = "assets/images/ui"                    # hz_typhoon.png, hz_earthquake.png, hz_flood.png, ...
ICON_SCALE = 3                                   # whole-number zoom for the tiny hz_*.png icons (2 = smaller, 4 = bigger)

# hazard id -> words that identify it in a page title (English + Filipino), used to pick hz_<id>.png
HAZARD_WORDS = (
    ("typhoon", ("typhoon", "bagyo", "storm")),
    ("earthquake", ("earthquake", "lindol")),
    ("flood", ("flood", "baha")),
    ("volcano", ("volcan", "bulkan")),
    ("wildfire", ("wildfire", "fire", "sunog")),
)
ICON_KEYS = [k for k, _ in HAZARD_WORDS]
DEFAULT_ORDER = ICON_KEYS                        # if a title can't be matched, page 1 = typhoon, 2 = earthquake...

# ---- where things sit on the 320x180 canvas (measured from guide_bg.png) ----
LEFT_PAGE = pygame.Rect(56, 29, 100, 117)
RIGHT_PAGE = pygame.Rect(164, 29, 100, 117)
SPINE_X = 160
PAGE_W, PAGE_H = LEFT_PAGE.w, LEFT_PAGE.h
BOOK_CLIP = pygame.Rect(50, 24, 220, 128)       # the turning page never draws outside the book

# the four colored tabs already painted on the image: (rect, accent color) for pages 1..4
TABS = [
    (pygame.Rect(267, 44, 10, 13), (30, 120, 150)),     # blue
    (pygame.Rect(267, 59, 10, 12), (240, 170, 20)),     # yellow
    (pygame.Rect(267, 73, 10, 13), (210, 60, 35)),      # red
    (pygame.Rect(267, 88, 10, 13), (90, 130, 40)),      # green
]

INK = (34, 22, 12)                              # near-black brown: maximum contrast on the cream paper
RULE = (228, 186, 112)                          # ruled lines, a touch darker than the paper
MARGIN = (214, 120, 90)                         # faint red margin line
DARK = (40, 25, 15)
PAPER = (250, 214, 140)
FAUX_BOLD = False                               # True = draw each text twice, 1px apart, for heavier letters

BUL_X = 8                                       # bullet x inside a page
TEXT_X = 14                                     # text x inside a page
TEXT_W = PAGE_W - TEXT_X - 5                    # wrap width
TEXT_BOTTOM = 102                               # lowest y text may reach (page arrows sit below)
LEFT_TOP = 59                                   # left page: text starts under the title + icon
RIGHT_TOP = 8
FLIP_TIME = 0.4                                 # seconds for one page turn

# ---- extras (turn any of them off if it feels like too much) ----
ENABLE_TYPING = True                            # text writes itself in after the page settles (click to skip)
ENABLE_GLOW = True                              # lantern flicker
ENABLE_DUST = True                              # specks drifting through the lantern light
ENABLE_TAB_HOVER = True                         # tabs slide out and show the hazard name when hovered
TYPE_CPS = 50                                   # typing speed: letters per second
LANTERN_POS = (17, 29)                          # where the lantern flame is on the canvas
GLOW_RADIUS = 95
DUST_COUNT = 14

W = settings.INTERNAL_WIDTH


def _wrap(font, text, width):
    lines, current = [], ""
    for word in text.split():
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _gradient(width, height, alpha, flip=False):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(width):
        pygame.draw.line(surf, (70, 44, 22, int(alpha * (1 - x / width))), (x, 0), (x, height))
    return pygame.transform.flip(surf, True, False) if flip else surf


class GuideState(BaseState):
    """Hazard guide written on the notebook image. LEFT/RIGHT, the corner arrows or the
    colored tabs turn the page with a real page-flip."""

    def __init__(self, game):
        super().__init__(game)
        self.time = 0.0
        self.page = 0
        self.prev_page = 0
        self.flip_dir = 1
        self.flip_t = FLIP_TIME             # not flipping at the start
        self._rows = {}                     # page -> (rows, font name, row height)

        bg = pygame.image.load(str(BASE_DIR / BG_PATH)).convert()
        if bg.get_size() != (320, 180):
            bg = pygame.transform.smoothscale(bg, (320, 180))
        self.bg = bg

        self.icons = {}                     # hazard id -> scaled hz_<id>.png (missing files just fall back to shapes)
        for key in ICON_KEYS:
            path = BASE_DIR / ICON_DIR / f"hz_{key}.png"
            if path.exists():
                img = pygame.image.load(str(path)).convert_alpha()
                size = (img.get_width() * ICON_SCALE, img.get_height() * ICON_SCALE)
                self.icons[key] = pygame.transform.scale(img, size)       # nearest-neighbour: keeps pixel art sharp

        self.back_button = Button("", (W // 2 - 35, 157, 70, 13), self.back)
        self.back_button.selected = True
        self.left = pygame.Rect(LEFT_PAGE.x + 3, LEFT_PAGE.bottom - 14, 12, 12)
        self.right = pygame.Rect(RIGHT_PAGE.right - 15, RIGHT_PAGE.bottom - 14, 12, 12)

        self.type_t = 0.0                   # time since the page settled (drives the typing)
        self._last_tick = 0
        self.hover_tab = None

        self.glow = self._make_glow()
        rng = random.Random(7)
        self.motes = [[rng.uniform(0, 170), rng.uniform(0, 150), rng.uniform(2, 6), rng.uniform(0, 6.3)]
                      for _ in range(DUST_COUNT)]
        self.mote_dot = pygame.Surface((2, 2), pygame.SRCALPHA)
        self.mote_dot.fill((255, 225, 150, 255))

        self.edge = _gradient(12, PAGE_H + 10, 110)              # shadow cast by the turning page
        self.edge_left = _gradient(12, PAGE_H + 10, 110, flip=True)

    def _make_glow(self):
        """Soft warm light around the lantern: a bright core plus a wide faint halo."""
        r = GLOW_RADIUS
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for d in range(r, 0, -1):
            a = 26 * (1 - d / r) ** 1.5 + 60 * max(0.0, 1 - d / 28) ** 2
            pygame.draw.circle(surf, (255, 175, 70, int(a)), (r, r), d)
        return surf

    # ---------- actions ----------
    def back(self):
        self.game.state_manager.pop()      # if your StateManager names this differently, change it here

    @property
    def flipping(self):
        return self.flip_t < FLIP_TIME

    def _go(self, index, direction):
        index %= len(guide())
        if index != self.page and not self.flipping:
            self.prev_page = self.page
            self.page = index
            self.flip_dir = direction
            self.flip_t = 0.0
            self.type_t = 0.0
            self._last_tick = 0
            audio.play("tock", 0.3)

    def _flip(self, step):
        self._go(self.page + step, 1 if step > 0 else -1)

    def accent(self, page):
        return TABS[page % len(TABS)][1]

    # ---------- input ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._flip(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._flip(1)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN):
                self.back()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            self.hover_tab = None
            for i, (rect, _) in enumerate(TABS[:len(guide())]):
                if rect.inflate(4, 3).collidepoint(pos):
                    self.hover_tab = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for i, (rect, _) in enumerate(TABS[:len(guide())]):
                if rect.inflate(4, 3).collidepoint(pos):
                    self._go(i, 1 if i > self.page else -1)
                    return
            if self.left.collidepoint(pos):
                self._flip(-1)
            elif self.right.collidepoint(pos):
                self._flip(1)
            elif self.back_button.contains(pos):
                self.back_button.activate()
            elif BOOK_CLIP.collidepoint(pos):
                self.type_t = 1e6              # click the book = finish writing instantly

    def update(self, dt):
        self.time += dt
        self.flip_t += dt
        if not self.flipping:
            self.type_t += dt
            shown = int(self.type_t * TYPE_CPS)
            if ENABLE_TYPING and shown < self._typed_total() and shown // 3 != self._last_tick:
                self._last_tick = shown // 3                    # a tiny scratch every 3 letters
                audio.play("tick", 0.08)
        for m in self.motes:                                    # dust drifts up and sways
            m[1] -= m[2] * dt
            m[0] += math.sin(self.time * 0.7 + m[3]) * 5 * dt
            if m[1] < -2:
                m[0], m[1] = random.uniform(0, 170), 152

    def _typed_total(self):
        pages = guide()
        rows, _, _ = self._page_rows(self.page % len(pages), pages[self.page % len(pages)])
        return sum(len(text) for _, _, _, text in rows)

    # ---------- hazard icons ----------
    def _icon_key(self, page, data):
        for field in ("id", "hazard", "key"):
            value = str(data.get(field, "")).lower()
            if value in ICON_KEYS:
                return value
        title = str(data.get("title", "")).lower()
        for key, words in HAZARD_WORDS:
            if any(w in title for w in words):
                return key
        return DEFAULT_ORDER[page % len(DEFAULT_ORDER)]

    # shape icons: only used if the hz_<id>.png file is missing
    def _shape_typhoon(self, s, cx, cy, col):
        for k in range(22):
            a = self.time * 2.5 + k * 0.5
            r = 2 + k * 0.6
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8
            pygame.draw.rect(s, col, (int(x), int(y), 2 if k < 14 else 1, 2 if k < 14 else 1))
        pygame.draw.rect(s, PAPER, (cx - 1, cy - 1, 3, 3))

    def _shape_earthquake(self, s, cx, cy, col):
        shake = round(math.sin(self.time * 30) * 1)
        pts = [(cx, cy - 15), (cx - 5, cy - 7), (cx + 3, cy - 1), (cx - 4, cy + 6), (cx + 1, cy + 15)]
        pygame.draw.lines(s, col, False, [(x + shake, y) for x, y in pts], 2)

    def _shape_flood(self, s, cx, cy, col):
        pygame.draw.rect(s, DARK, (cx - 6, cy - 10, 12, 10))
        pygame.draw.polygon(s, DARK, [(cx - 8, cy - 10), (cx + 8, cy - 10), (cx, cy - 17)])
        for row in range(3):
            y0 = cy - 3 + row * 6
            for x in range(-16, 17, 2):
                y = y0 + math.sin((x + self.time * 18 * (1 if row % 2 else -1)) * 0.35) * 2
                pygame.draw.rect(s, col, (cx + x, int(y), 2, 3))

    def _shape_warning(self, s, cx, cy, col):
        pygame.draw.polygon(s, col, [(cx, cy - 14), (cx - 14, cy + 11), (cx + 14, cy + 11)])
        pygame.draw.rect(s, PAPER, (cx - 1, cy - 5, 3, 9))
        pygame.draw.rect(s, PAPER, (cx - 1, cy + 6, 3, 3))

    def draw_icon(self, surface, key, cx, cy, col):
        img = self.icons.get(key)
        if img:
            bob = round(math.sin(self.time * 2.5))                  # gentle float
            surface.blit(img, img.get_rect(center=(cx, cy + bob)))
        else:
            shape = getattr(self, f"_shape_{key}", self._shape_warning)
            shape(surface, cx, cy, col)

    # ---------- layout ----------
    def _page_rows(self, page, data):
        """Wrap the bullets. Uses the normal font; if there is too much text it drops to the
        small font so everything still fits on the two pages."""
        if page in self._rows:
            return self._rows[page]
        # Match the actual font heights; tighter ruled-line spacing made
        # neighboring rows touch or overlap on some guide pages.
        for font_name, row_h in (("body", 13), ("tiny", 10)):
            font = theme.get_font(font_name)
            flat = []
            for line in data["lines"]:
                for i, text in enumerate(_wrap(font, line, TEXT_W)):
                    flat.append((i == 0, text))
            left_y = list(range(LEFT_TOP, TEXT_BOTTOM - row_h + 1, row_h))
            right_y = list(range(RIGHT_TOP, TEXT_BOTTOM - row_h + 1, row_h))
            if len(flat) <= len(left_y) + len(right_y):
                break
        slots = [("left", y) for y in left_y] + [("right", y) for y in right_y]
        rows = [(side, y, first, text) for (side, y), (first, text) in zip(slots, flat)]
        self._rows[page] = (rows, font_name, row_h)
        return self._rows[page]

    # ---------- drawing one page ----------
    def render_half(self, pages, page, side):
        """One page as its own surface: the paper from the image, ruled lines, bullets and the
        hazard icon. (Text is NOT drawn here: theme.draw_text always draws on the real screen,
        so the writing is drawn separately by draw_texts.)"""
        left = side == "left"
        rect = LEFT_PAGE if left else RIGHT_PAGE
        s = self.bg.subsurface(rect).copy()

        data = pages[page % len(pages)]
        col = self.accent(page)
        ink_accent = theme.mix(col, DARK, 0.58)
        rows, _, row_h = self._page_rows(page, data)

        top = LEFT_TOP if left else RIGHT_TOP
        for y in range(top, TEXT_BOTTOM, row_h):                       # ruled lines
            pygame.draw.line(s, RULE, (6, y + row_h - 1), (PAGE_W - 7, y + row_h - 1))
        if left:
            cx = PAGE_W // 2
            self.draw_icon(s, self._icon_key(page, data), cx, 34, ink_accent)
            pygame.draw.line(s, ink_accent, (cx - 30, 56), (cx + 30, 56))
        else:
            pygame.draw.line(s, MARGIN, (4, 4), (4, TEXT_BOTTOM + 2))   # red margin line

        return s

    def _text(self, surface, text, pos, font, color, anchor=None):
        kw = {"anchor": anchor} if anchor else {}
        theme.draw_text(surface, text, pos, font, color, shadow=False, **kw)
        if FAUX_BOLD:
            theme.draw_text(surface, text, (pos[0] + 1, pos[1]), font, color, shadow=False, **kw)

    def draw_texts(self, surface, pages, page):
        """The writing for both pages, at real canvas coordinates."""
        data = pages[page % len(pages)]
        ink_accent = theme.mix(self.accent(page), DARK, 0.58)
        rows, font_name, _ = self._page_rows(page, data)

        title_font = "heading" if theme.get_font("heading").size(data["title"])[0] <= PAGE_W - 8 else "body"
        self._text(surface, data["title"], (LEFT_PAGE.x + PAGE_W // 2, LEFT_PAGE.y + 9),
                   title_font, ink_accent, anchor="center")
        remaining = int(self.type_t * TYPE_CPS) if ENABLE_TYPING else 10 ** 9
        font = theme.get_font(font_name)
        for side, y, first, text in rows:
            part = text[:max(0, remaining)]
            remaining -= len(text)
            if not part:
                break
            base = LEFT_PAGE if side == "left" else RIGHT_PAGE
            if first:                                                  # bullet appears with its line
                pygame.draw.rect(surface, self.accent(page), (base.x + BUL_X - 1, base.y + y + 3, 3, 3))
                pygame.draw.rect(surface, ink_accent, (base.x + BUL_X - 1, base.y + y + 3, 3, 3), 1)
            self._text(surface, part, (base.x + TEXT_X, base.y + y), font_name, INK)
            if remaining <= 0 and int(self.time * 6) % 2:             # blinking pen cursor
                cx = base.x + TEXT_X + font.size(part)[0] + 1
                pygame.draw.rect(surface, INK, (cx, base.y + y + 1, 1, 6))

    # ---------- drawing ----------
    def draw(self, surface):
        pages = guide()
        count = len(pages)
        page = self.page % count
        ink_accent = theme.mix(self.accent(page), DARK, 0.58)

        surface.blit(self.bg, (0, 0))

        # work out what is on each side, and which leaf (if any) is mid-turn
        leaf = None
        if self.flipping:
            p = min(1.0, self.flip_t / FLIP_TIME)
            e = p * p * (3 - 2 * p)                              # ease in/out
            old, new = self.prev_page, self.page
            if self.flip_dir > 0:
                phi = math.pi * e                                # leaf turns right -> left
                left_page, right_page = old, new
                face = (old, "right") if phi < math.pi / 2 else (new, "left")
            else:
                phi = math.pi * (1 - e)                          # leaf turns left -> right
                left_page, right_page = new, old
                face = (old, "left") if phi > math.pi / 2 else (new, "right")
            leaf = (phi, face)
        else:
            left_page = right_page = self.page

        surface.blit(self.render_half(pages, left_page, "left"), LEFT_PAGE)
        surface.blit(self.render_half(pages, right_page, "right"), RIGHT_PAGE)

        if leaf:
            phi, (face_page, face_side) = leaf
            lift = math.sin(phi)
            w = max(2, int(abs(math.cos(phi)) * PAGE_W))
            h = PAGE_H + int(lift * 6)                          # a lifted page looks a bit taller
            y = LEFT_PAGE.y - (h - PAGE_H) // 2
            x = RIGHT_PAGE.x if face_side == "right" else LEFT_PAGE.right - w

            old_clip = surface.get_clip()
            surface.set_clip(BOOK_CLIP)
            edge = self.edge if face_side == "right" else self.edge_left      # shadow on the page below
            edge.set_alpha(int(255 * lift))
            surface.blit(edge, (x + w if face_side == "right" else x - 12, LEFT_PAGE.y - 5))

            img = pygame.transform.scale(self.render_half(pages, face_page, face_side), (w, h))
            shade = pygame.Surface((w, h), pygame.SRCALPHA)
            shade.fill((60, 36, 18, int(120 * lift)))           # darker when the page stands on edge
            img.blit(shade, (0, 0))
            surface.blit(img, (x, y))
            free_x = x + w - 1 if face_side == "right" else x
            pygame.draw.line(surface, (170, 120, 60), (free_x, y), (free_x, y + h))
            surface.set_clip(old_clip)
        else:
            self.draw_texts(surface, pages, page)               # writing appears once the page has settled

        # lantern light flickers over the scene
        if ENABLE_GLOW:
            flick = 0.78 + 0.12 * math.sin(self.time * 7) + 0.08 * math.sin(self.time * 13 + 1.3) \
                + 0.05 * math.sin(self.time * 23 + 4.1)
            self.glow.set_alpha(int(255 * max(0.3, min(1.0, flick))))
            surface.blit(self.glow, (LANTERN_POS[0] - GLOW_RADIUS, LANTERN_POS[1] - GLOW_RADIUS))
        if ENABLE_DUST:
            for x, y, _, phase in self.motes:
                near = max(0.0, 1 - math.hypot(x - LANTERN_POS[0], y - LANTERN_POS[1]) / 140)
                a = int(255 * near * (0.5 + 0.5 * math.sin(self.time * 2 + phase)))
                if a > 20:
                    self.mote_dot.set_alpha(a)
                    surface.blit(self.mote_dot, (int(x), int(y)))

        # hovered tab slides out a little and shows its hazard name
        if ENABLE_TAB_HOVER and self.hover_tab is not None and self.hover_tab != page:
            rect, tab_col = TABS[self.hover_tab]
            pygame.draw.rect(surface, DARK, (rect.right - 1, rect.y + 1, 4, rect.h - 2))
            pygame.draw.rect(surface, tab_col, (rect.right, rect.y + 2, 2, rect.h - 4))
        if ENABLE_TAB_HOVER and self.hover_tab is not None:
            theme.draw_text(surface, pages[self.hover_tab]["title"], (318, TABS[self.hover_tab][0].centery),
                            "tiny", theme.CREAM, anchor="midright")

        # active tab sticks out a little further
        if page < len(TABS):
            rect, tab_col = TABS[page]
            pygame.draw.rect(surface, DARK, (rect.right - 1, rect.y + 1, 5, rect.h - 2))
            pygame.draw.rect(surface, tab_col, (rect.right, rect.y + 2, 3, rect.h - 4))

        # page arrows and dots
        for r, direction in ((self.left, -1), (self.right, 1)):
            cy = r.centery
            if direction < 0:
                pts = [(r.right - 2, cy - 4), (r.right - 2, cy + 4), (r.x + 2, cy)]
            else:
                pts = [(r.x + 2, cy - 4), (r.x + 2, cy + 4), (r.right - 2, cy)]
            pygame.draw.polygon(surface, ink_accent, pts)
        for i in range(count):
            c = ink_accent if i == page else RULE
            pygame.draw.rect(surface, c, (RIGHT_PAGE.centerx - count * 4 + i * 8, RIGHT_PAGE.bottom - 9, 4, 4))

        self.back_button.text = tr("back")
        self.back_button.draw(surface, self.time)
        theme.draw_text(surface, tr("hint_guide"), (W // 2, 175), "tiny",
                        theme.CREAM_DIM, shadow=False, anchor="center")
