import math
import random
import time

import pygame

from src.core import audio
from src.entities.reference_art import player_sprite
from src.states.base_state import BaseState
from src.states.loading import LoadingScreen
from src.states.mission_prep import MissionPrep
from src.ui import theme
from src.ui.select_backdrop import SelectBackdrop
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text

CENTERS = [90, 230]     # x of each hero on the 320x180 canvas
FEET_Y = 104            # where their feet touch the floor
ZOOM = 2                # heroes are drawn 2x bigger than the walking sheet
LEAVE_TIME = 1.9        # total seconds of the "drop down, cross the mat, leave" after confirming
DROP_TIME = 0.25        # the hop down from the floor
FADE_START = 1.2        # when the screen starts fading to black
WALK_SPEED = 95         # pixels per second while leaving
MAT_X = 160             # the banig mat in the middle: the hero walks across it
EXIT_FPS = 8            # walking animation speed while leaving
ABILITY_ICON = {"first_aid": "aid", "sprint": "light"}   # ability id -> icon name in theme.ICONS

# ---- middle wall props ----
SHOW_POSTER = True                  # small go-bag poster on the wall
SHOW_DOG = True                     # sleeping dog on the banig mat
SHOW_CLOCK = False                  # wall clock (off: too busy)
SHOW_ABILITY_CARD = False           # ability description card (off: too busy)
POSTER_PAGES = 1                    # 1 = just the go-bag list, 2 = + storm signals, 3 = + evacuate map
POSTER_RECT = (134, 38, 52, 62)     # x, y, w, h of the pinned poster
PAGE_TIME = 6.0                     # seconds each poster page stays up
PAGE_FLIP = 0.3                     # flutter time when the page changes
CHECKLIST = ("Water", "Torch", "Radio", "Aid kit", "Whistle")
SIGNALS = (                         # PAGASA wind signals: (number, wind speed, color)
    (1, "39-61 kph", (70, 130, 200)),
    (2, "62-88 kph", (225, 200, 60)),
    (3, "89-117 kph", (230, 140, 40)),
    (4, "118-184 kph", (210, 60, 50)),
    (5, "185+ kph", (190, 60, 170)),
)
ABILITY_INFO = {                    # shown on the small card under the poster (edit to match your game)
    "sprint": "Quick speed burst",
    "first_aid": "Heals you up",
}
DOG_POS = (160, 140)                # sleeping dog on the banig mat (center x, y)
CLOCK_POS = (190, 39)               # small wall clock

# ---- tip board ----
TYPE_CPS = 45           # typewriter speed: letters per second
READ_TIME = 5.0         # seconds a finished tip stays before the next one (pauses on mouse hover)
FLIP_TIME = 0.3         # how long the paper flutters when the tip changes
TEXT_X = 54             # where the tip text starts inside the board (the tag sits on the left)
TEXT_W = 218            # width of the tip text
HAZARD_TAGS = {         # id: (label, color)
    "typhoon": ("TYPHOON", (70, 130, 190)),
    "flood": ("FLOOD", (50, 100, 180)),
    "earthquake": ("EARTHQUAKE", (150, 100, 55)),
    "volcano": ("VOLCANO", (190, 70, 60)),
    "wildfire": ("WILDFIRE", (210, 120, 40)),
    "general": ("TIP", (80, 150, 90)),
}
HAZARD_WORDS = (        # checked in this order to guess a tip's hazard from its text
    ("volcano", ("volcan", "ashfall", "lava", "phivolcs", "eruption")),
    ("earthquake", ("earthquake", "drop, cover", "aftershock", "tremor")),
    ("flood", ("flood", "drown", "current")),
    ("typhoon", ("typhoon", "storm", "signal no", "pagasa", "strong wind")),
    ("wildfire", ("wildfire", "fire", "smoke")),
)


def _guess_hazard(text):
    low = text.lower()
    for hazard, words in HAZARD_WORDS:
        if any(w in low for w in words):
            return hazard
    return "general"


def _parse_tip(item):
    """A tip in trivia.json can be a plain string or {"text": "...", "hazard": "flood"}."""
    if isinstance(item, dict):
        text = str(item.get("text", ""))
        hazard = item.get("hazard") or _guess_hazard(text)
    else:
        text = str(item)
        hazard = _guess_hazard(text)
    return text, (hazard if hazard in HAZARD_TAGS else "general")


def _along(points, f):
    """Point at fraction f (0..1) along a polyline."""
    segs = [(points[i], points[i + 1]) for i in range(len(points) - 1)]
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    d = f * sum(lengths)
    for (a, b), ln in zip(segs, lengths):
        if d <= ln and ln > 0:
            u = d / ln
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        d -= ln
    return points[-1]


class CharacterSelect(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.characters = load_json("data/characters.json")
        tips = [_parse_tip(t) for t in load_json("data/trivia.json")] or [("Stay safe!", "general")]
        random.shuffle(tips)
        self.tips = tips
        self.board_rect = pygame.Rect(20, 153, 280, 27)
        self.board_hover = False

        self.font = theme.get_font("tiny")
        self._set_tip(0, sound=False)
        self.selected = 0
        self.t = 0.0
        self.hop_t = 1.0            # time since the selection changed (drives the hop)
        self.leaving = False
        self.identity_editing = False
        self.identity_text = ""
        self.identity_error = ""
        self.leave_t = 0.0
        self._last_step = -1
        self._landed = False
        self.backdrop = SelectBackdrop()
        self.fade = pygame.Surface((320, 180))
        self.fade.fill((0, 0, 0))

        # for the stat bars: the best hero is about 80% full
        self.speed_max = max(c["speed"] for c in self.characters) * 1.25
        self.hp_max = max(c["max_health"] for c in self.characters) * 1.25

        self.cards = [pygame.Rect(cx - 52, 28, 104, 124) for cx in CENTERS]

        self.down, self.up, self.dimmed = [], [], []
        for c in self.characters:
            reference = player_sprite(c.get("id", "juan"))
            if reference:
                height = 62
                width = round(reference.get_width() * height / reference.get_height())
                hero = pygame.transform.scale(reference, (width, height))
                # Keep one stable front-facing pose; the exit animation moves
                # the whole sprite rather than changing direction every frame.
                down = up = [hero] * 4
            else:
                box = pygame.Surface((32, 56), pygame.SRCALPHA)
                box.fill((*tuple(c["color"]), 255))
                down = up = [box] * 4
            dim = down[0].copy()
            dim.fill((125, 125, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.down.append(down)
            self.up.append(up)
            self.dimmed.append(dim)

        self.shadow = pygame.Surface((34, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, (0, 0, 0, 90), self.shadow.get_rect())

    # ---------- actions ----------
    def select(self, i):
        if i != self.selected and not self.leaving:
            self.selected = i
            self.hop_t = 0.0
            audio.play("tick")

    def confirm(self):
        if self.leaving or self.identity_editing:
            return
        self.identity_text = self.game.session.challenger_id
        self.identity_error = ""
        self.identity_editing = True
        pygame.key.start_text_input()

    def finish_identity_entry(self):
        tag = self.identity_text.strip().upper()
        if len(tag) < 3:
            self.identity_error = "Use at least 3 letters or numbers."
            return
        self.game.session.challenger_id = tag
        self.game.session.challenger_name = tag
        self.identity_editing = False
        pygame.key.stop_text_input()
        self.leaving = True
        self.leave_t = 0.0
        self._last_step = -1
        self._landed = False
        audio.play("confirm")
        audio.play("hop", 0.8)

    def _set_tip(self, index, sound=True):
        self.tip_index = index % len(self.tips)
        text, self.tip_hazard = self.tips[self.tip_index]
        self.tip_lines = wrap_text(text, self.font, TEXT_W)[:3]
        self.tip_total = sum(len(line) for line in self.tip_lines)
        self.type_t = -0.15 if sound else 0.0      # typing starts just after the paper flutters
        self.read_t = 0.0
        self.flip_t = 0.0 if sound else FLIP_TIME
        self._last_tick = 0
        if sound:
            audio.play("whoosh", 0.3)

    def next_tip(self, step=1):
        if not self.leaving:
            self._set_tip(self.tip_index + step)

    def _finish(self):
        self.game.session.character = self.characters[self.selected]
        self.game.session.save()
        stage_id = self.game.session.current_stage
        self.game.state_manager.change(LoadingScreen(
            self.game, lambda: MissionPrep(self.game, stage_id), "PREPARING YOUR JOURNEY"))

    # ---------- input ----------
    def handle_event(self, event):
        if self.identity_editing:
            if event.type == pygame.TEXTINPUT:
                allowed = "".join(char for char in event.text.upper()
                                  if char.isalnum() or char in "-_")
                self.identity_text = (self.identity_text + allowed)[:14]
                self.identity_error = ""
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.identity_text = self.identity_text[:-1]
                    self.identity_error = ""
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.finish_identity_entry()
                elif event.key == pygame.K_ESCAPE:
                    self.identity_editing = False
                    pygame.key.stop_text_input()
            return
        if self.leaving:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.select((self.selected - 1) % len(self.characters))
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.select((self.selected + 1) % len(self.characters))
            elif event.key in (pygame.K_DOWN, pygame.K_s):      # joystick down = next tip
                self.next_tip(1)
            elif event.key in (pygame.K_UP, pygame.K_w):        # joystick up = previous tip
                self.next_tip(-1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.confirm()
            elif event.key == pygame.K_ESCAPE:
                audio.play("back")
                self.game.state_manager.pop()

        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            self.backdrop.look_at(pos[0])
            self.board_hover = self.board_rect.collidepoint(pos)
            for i, card in enumerate(self.cards):
                if card.collidepoint(pos):
                    self.select(i)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            if self.board_rect.collidepoint(pos):               # click the board = next tip
                self.next_tip(1)
                return
            for i, card in enumerate(self.cards):
                if card.collidepoint(pos):
                    self.select(i)
                    self.confirm()

    def update(self, dt):
        self.t += dt
        self.hop_t += dt
        self.backdrop.update(dt)
        self.type_t += dt
        self.flip_t += dt
        shown = max(0, int(self.type_t * TYPE_CPS))
        done = shown >= self.tip_total
        if not done and shown // 3 != self._last_tick:          # a tiny tick every 3 letters
            self._last_tick = shown // 3
            audio.play("tick", 0.1)
        if done and not self.board_hover and not self.leaving:  # auto-advance after reading time
            self.read_t += dt
            if self.read_t > READ_TIME:
                self.next_tip(1)
        if self.leaving:
            self.leave_t += dt
            if not self._landed and self.leave_t >= DROP_TIME:      # lands on the floor
                self._landed = True
                audio.play("thud", 0.5)
            if self.leave_t >= DROP_TIME:                           # quiet footsteps
                step = int((self.leave_t - DROP_TIME) * EXIT_FPS)
                if step != self._last_step and step % 2 == 0:
                    audio.play("tick", 0.35)
                self._last_step = step
            if self.leave_t >= LEAVE_TIME:
                self._finish()

    # ---------- drawing ----------
    def leave_pose(self, i):
        """Where the chosen hero is while leaving: hops down, then walks over the mat and out."""
        cx = CENTERS[i]
        t = self.leave_t
        if t < DROP_TIME:                                    # the drop: a small hop down
            u = t / DROP_TIME
            return cx, FEET_Y + 2 + 10 * u - 5 * math.sin(math.pi * u)
        w = t - DROP_TIME
        x = cx + (MAT_X - cx) * min(1.0, w / 0.9)            # drift to the middle, onto the mat
        y = FEET_Y + 12 + w * WALK_SPEED                     # then straight out of the bottom
        return x, y

    def draw_character(self, surface, i, selected):
        cx = CENTERS[i]
        x = cx

        if selected and self.leaving:
            x, y = self.leave_pose(i)
            if self.leave_t < DROP_TIME:
                frame = self.down[i][0]
            else:
                frame = self.down[i][int((self.leave_t - DROP_TIME) * EXIT_FPS) % 4]
            surface.blit(self.shadow, self.shadow.get_rect(center=(int(x), int(y) - 2)))
        elif selected:
            surface.blit(self.shadow, self.shadow.get_rect(center=(cx, FEET_Y)))
            frame = self.down[i][int(self.t * 5) % 4]
            hop = -round(3 * math.sin(math.pi * min(1.0, self.hop_t / 0.25)))
            y = FEET_Y + 2 + hop
        else:
            surface.blit(self.shadow, self.shadow.get_rect(center=(cx, FEET_Y)))
            frame = self.dimmed[i]
            y = FEET_Y + 2 + (-1 if math.sin(self.t * 2 + i * 2) > 0.3 else 0)   # slow idle bob

        tint = theme.mix((255, 255, 255), self.backdrop.tint, 0.8)
        if tint != (255, 255, 255):
            frame = frame.copy()
            frame.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(frame, frame.get_rect(midbottom=(int(x), int(y))))

        if selected and not self.leaving:     # bouncing arrow above the head
            top = FEET_Y - frame.get_height() - 5
            b = int(round(math.sin(self.t * 6) * 1.5))
            pygame.draw.polygon(surface, theme.HONEY,
                                [(cx - 4, top + b), (cx + 4, top + b), (cx, top + 4 + b)])

    def draw_info(self, surface, i, selected):
        c = self.characters[i]
        cx = CENTERS[i]

        # wooden name plaque (same plank as the menu buttons)
        theme.draw_button(surface, pygame.Rect(cx - 42, 106, 84, 14), c["name"], selected=selected)

        # stats panel: two bars + ability with an icon
        panel = pygame.Rect(cx - 50, 121, 100, 30)
        theme.draw_panel(surface, panel, accent=theme.HONEY if selected else theme.LAVENDER,
                         alpha=230 if selected else 190)
        rows = (("SPEED", c["speed"], self.speed_max, theme.SKY),
                ("HP", c["max_health"], self.hp_max, theme.CORAL))
        for n, (label, value, maximum, color) in enumerate(rows):
            y = panel.y + 4 + n * 9
            theme.draw_text(surface, label, (panel.x + 5, y), self.font, theme.CREAM_DIM, shadow=False)
            theme.draw_bar(surface, (panel.x + 34, y + 1, 58, 5), value, maximum, color)
        y = panel.y + 21
        icon = ABILITY_ICON.get(c["ability"], "light")
        theme.draw_icon(surface, icon, (panel.x + 5, y), theme.HONEY)
        theme.draw_text(surface, c["ability"].replace("_", " ").title(), (panel.x + 16, y + 1),
                        self.font, theme.HONEY, shadow=False)

    # ---------- middle wall props ----------
    def draw_poster(self, surface):
        """Pinned poster that flips between GO BAG, STORM SIGNAL and EVACUATE pages."""
        page = int(self.t / PAGE_TIME) % POSTER_PAGES
        local = self.t % PAGE_TIME
        p = min(1.0, local / PAGE_FLIP)
        dy = round(math.sin(p * math.pi * 3) * 2 * (1 - p)) if (POSTER_PAGES > 1 and self.t > PAGE_TIME) else 0
        paper = pygame.Rect(POSTER_RECT).move(0, dy)
        ink = (62, 44, 30)
        brown = (98, 68, 44)

        pygame.draw.rect(surface, theme.SHADOW, paper.move(1, 2))
        pygame.draw.rect(surface, (206, 182, 138), paper)
        pygame.draw.rect(surface, brown, paper, 1)
        for px in (paper.x + 3, paper.right - 5):
            pygame.draw.rect(surface, (160, 55, 45), (px, paper.y + 3, 2, 2))   # red pins

        titles = ("GO BAG", "STORM SIGNAL", "EVACUATE")
        theme.draw_text(surface, titles[page], (paper.centerx, paper.y + 5),
                        self.font, (140, 62, 48), shadow=False, anchor="midtop")

        if page == 0:       # checklist that ticks in one by one
            checked = min(len(CHECKLIST), int(local * 1.1))
            for n, item in enumerate(CHECKLIST):
                y = paper.y + 16 + n * 9
                box = pygame.Rect(paper.x + 6, y + 1, 5, 5)
                pygame.draw.rect(surface, ink, box, 1)
                if n < checked:
                    pygame.draw.lines(surface, (60, 140, 70), False,
                                      [(box.x, box.y + 2), (box.x + 2, box.y + 4), (box.x + 6, box.y - 1)])
                theme.draw_text(surface, item, (paper.x + 14, y), self.font, ink, shadow=False)

        elif page == 1:     # PAGASA wind signals
            for n, (num, speed, color) in enumerate(SIGNALS):
                y = paper.y + 16 + n * 9
                sw = pygame.Rect(paper.x + 6, y, 7, 6)
                pygame.draw.rect(surface, color, sw)
                pygame.draw.rect(surface, ink, sw, 1)
                theme.draw_text(surface, str(num), sw.center, self.font, (255, 255, 255),
                                shadow=False, anchor="center")
                theme.draw_text(surface, speed, (paper.x + 16, y), self.font, ink, shadow=False)

        else:               # mini evacuation map: house -> safe zone
            area = pygame.Rect(paper.x + 5, paper.y + 15, paper.w - 10, 38)
            pygame.draw.rect(surface, (200, 220, 170), area)
            pygame.draw.rect(surface, brown, area, 1)
            house = pygame.Rect(area.x + 4, area.bottom - 12, 8, 6)
            pygame.draw.rect(surface, (180, 120, 70), house)
            pygame.draw.polygon(surface, (150, 60, 50),
                                [(house.x - 1, house.y), (house.right, house.y), (house.centerx, house.y - 4)])
            safe = pygame.Rect(area.right - 14, area.y + 4, 10, 10)
            pygame.draw.rect(surface, (60, 150, 80), safe)
            pygame.draw.rect(surface, (255, 255, 255), (safe.centerx - 1, safe.y + 2, 2, 6))
            pygame.draw.rect(surface, (255, 255, 255), (safe.x + 2, safe.centery - 1, 6, 2))
            path = [(house.centerx, house.y + 6), (house.centerx, area.centery),
                    (safe.centerx, area.centery), (safe.centerx, safe.bottom)]
            for a, b in zip(path, path[1:]):
                pygame.draw.line(surface, brown, a, b, 1)
            for k in range(3):                                  # dots travelling along the route
                f = (self.t * 0.5 + k / 3) % 1.0
                x, y = _along(path, f)
                pygame.draw.rect(surface, (200, 50, 50), (int(x) - 1, int(y) - 1, 2, 2))
            theme.draw_text(surface, "SAFE", (safe.centerx, safe.bottom + 1), self.font,
                            (60, 150, 80), shadow=False, anchor="midtop")

        for n in range(POSTER_PAGES if POSTER_PAGES > 1 else 0):  # page dots
            col = (150, 60, 50) if n == page else (190, 165, 120)
            pygame.draw.rect(surface, col, (paper.centerx - 7 + n * 5, paper.bottom - 5, 3, 2))

    def draw_clock(self, surface):
        cx, cy = CLOCK_POS
        lt = time.localtime()
        pygame.draw.circle(surface, theme.SHADOW, (cx + 1, cy + 1), 6)
        pygame.draw.circle(surface, (120, 84, 50), (cx, cy), 6)
        pygame.draw.circle(surface, (240, 228, 196), (cx, cy), 5)
        minute = lt.tm_min + lt.tm_sec / 60
        hour = (lt.tm_hour % 12) + minute / 60
        for angle, length, color in ((hour / 12, 2.5, (70, 48, 32)), (minute / 60, 4, (70, 48, 32))):
            a = angle * 2 * math.pi - math.pi / 2
            pygame.draw.line(surface, color, (cx, cy),
                             (cx + round(math.cos(a) * length), cy + round(math.sin(a) * length)))

    def draw_ability_card(self, surface):
        c = self.characters[self.selected]
        text = ABILITY_INFO.get(c["ability"], "Special ability")
        card = pygame.Rect(126, 94, 68, 11)
        theme.draw_panel(surface, card, accent=theme.HONEY, alpha=215)
        old = surface.get_clip()
        surface.set_clip(card.inflate(-4, 0))
        theme.draw_text(surface, text, card.center, self.font, theme.CREAM, shadow=False, anchor="center")
        surface.set_clip(old)

    def draw_dog(self, surface):
        """A sleeping aspin on the banig mat. It wakes and looks at whoever you pick."""
        cx, cy = DOG_POS
        awake = self.hop_t < 0.7
        side = -1 if self.selected == 0 else 1
        fur, dark, light = (168, 124, 80), (98, 66, 40), (198, 160, 114)
        breathe = 0 if awake else (1 if math.sin(self.t * 2) > 0 else 0)

        surface.blit(self.shadow, self.shadow.get_rect(center=(cx, cy + 4)))
        pygame.draw.ellipse(surface, fur, (cx - 11, cy - 6 - breathe, 22, 9 + breathe))     # body
        pygame.draw.ellipse(surface, light, (cx - 6, cy - 2, 12, 4))                         # belly

        wag = round(math.sin(self.t * 14) * 1.5) if awake else 0                             # tail
        pygame.draw.ellipse(surface, dark, (cx - side * 12 - 2, cy - 4 + wag, 5, 3))

        if awake:
            hx, hy = cx + side * 9, cy - 10
        else:
            hx, hy = cx + side * 9, cy - 4 - breathe
        head = pygame.Rect(0, 0, 9, 8 if awake else 6)
        head.center = (hx, hy)
        pygame.draw.ellipse(surface, fur, head)
        pygame.draw.rect(surface, (40, 28, 20), (hx + side * 4 - (1 if side > 0 else 0), hy, 2, 2))   # nose
        if awake:
            pygame.draw.polygon(surface, dark, [(hx - 3, hy - 2), (hx - 1, hy - 6), (hx + 1, hy - 2)])   # perked ears
            pygame.draw.polygon(surface, dark, [(hx + 1, hy - 2), (hx + 3, hy - 6), (hx + 4, hy - 2)])
            pygame.draw.rect(surface, (30, 20, 14), (hx + side * 2, hy - 2, 1, 2))
        else:
            pygame.draw.rect(surface, dark, (hx - 3, hy - 3, 4, 3))                              # floppy ear
            pygame.draw.line(surface, (30, 20, 14), (hx + side * 1, hy - 1), (hx + side * 3, hy - 1))  # closed eye
            for k in range(2):                                                                   # floating zzz
                ph = (self.t * 0.6 + k * 0.5) % 1.0
                theme.draw_text(surface, "z", (cx + side * 15 + k * 6, int(cy - 10 - ph * 12)),
                                self.font, theme.CREAM, shadow=False)

    def draw_notice_board(self, surface):
        p = min(1.0, self.flip_t / FLIP_TIME)
        dy = round(math.sin(p * math.pi * 3) * 2 * (1 - p))      # the paper flutters on change
        board = self.board_rect.move(0, dy)
        ink = (70, 48, 32)

        pygame.draw.rect(surface, theme.SHADOW, board.move(1, 2))
        pygame.draw.rect(surface, (232, 214, 168), board)
        pygame.draw.rect(surface, (120, 84, 50), board, 1)
        for px, py in ((board.x + 3, board.y + 3), (board.right - 5, board.y + 3)):
            pygame.draw.rect(surface, (200, 50, 50), (px, py, 2, 2))      # red pins

        # hazard tag + tip counter on the left
        label, color = HAZARD_TAGS[self.tip_hazard]
        tag = pygame.Rect(board.x + 7, board.y + 5, 42, 9)
        pygame.draw.rect(surface, theme.SHADOW, tag.move(0, 1))
        pygame.draw.rect(surface, color, tag)
        pygame.draw.line(surface, theme.mix(color, (255, 255, 255), 0.4), (tag.x, tag.y), (tag.right - 1, tag.y))
        theme.draw_text(surface, label, tag.center, self.font, theme.CREAM, anchor="center")
        theme.draw_text(surface, f"{self.tip_index + 1}/{len(self.tips)}", (tag.centerx, board.y + 16),
                        self.font, (120, 84, 50), shadow=False, anchor="midtop")

        # typewriter text
        remaining = max(0, int(self.type_t * TYPE_CPS))
        done = remaining >= self.tip_total
        for n, line in enumerate(self.tip_lines):
            part = line[:remaining]
            remaining -= len(line)
            if not part:
                break
            ly = board.y + n * 9
            theme.draw_text(surface, part, (board.x + TEXT_X, ly), self.font, ink, shadow=False)
            if not done and remaining <= 0 and int(self.t * 6) % 2:       # blinking cursor
                cx = board.x + TEXT_X + self.font.size(part)[0] + 1
                pygame.draw.rect(surface, ink, (cx, ly + 1, 2, 5))
        if done and not self.board_hover:                                   # "more tips" arrow
            b = int(round(math.sin(self.t * 5) * 1))
            ax, ay = board.right - 10, board.bottom - 7 + b
            pygame.draw.polygon(surface, (120, 84, 50), [(ax, ay), (ax + 5, ay), (ax + 2, ay + 3)])

    def draw(self, surface):
        self.backdrop.draw(surface, glow_pos=(CENTERS[self.selected], FEET_Y))

        # middle props sit behind the heroes
        if SHOW_POSTER:
            self.draw_poster(surface)
        if SHOW_CLOCK:
            self.draw_clock(surface)
        if SHOW_DOG:
            self.draw_dog(surface)

        for i in range(len(self.characters)):
            self.draw_character(surface, i, i == self.selected)

        if not self.leaving:
            theme.draw_text(surface, "Select Your Character", (160, 3), "heading",
                            theme.HONEY, anchor="midtop")
            theme.draw_text(surface, "LEFT / RIGHT: choose     UP / DOWN: tips     OK: confirm", (160, 17),
                            self.font, theme.CREAM, anchor="midtop")
            for i in range(len(self.characters)):
                self.draw_info(surface, i, i == self.selected)
            if SHOW_ABILITY_CARD:
                self.draw_ability_card(surface)
            self.draw_notice_board(surface)
        else:                                  # fade to black (text is skipped: it draws after the canvas)
            fade = (self.leave_t - FADE_START) / (LEAVE_TIME - FADE_START)
            self.fade.set_alpha(int(255 * max(0.0, min(1.0, fade))))
            surface.blit(self.fade, (0, 0))

        if self.identity_editing:
            # Text is rendered after the canvas is scaled, so discard the
            # underlying screen's queued text before drawing this modal.
            theme.TEXT_QUEUE.clear()
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((7, 12, 24, 205))
            surface.blit(shade, (0, 0))
            panel = pygame.Rect(32, 48, 256, 82)
            theme.draw_panel(surface, panel, title="LEADERBOARD PLAYER ID", accent=theme.HONEY)
            theme.draw_text(surface, "Choose a unique tag for your scores.",
                            (160, 69), "tiny", theme.CREAM, anchor="center")
            field = pygame.Rect(65, 81, 190, 20)
            pygame.draw.rect(surface, (12, 22, 34), field)
            pygame.draw.rect(surface, theme.SKY, field, 1)
            cursor = "_" if pygame.time.get_ticks() // 400 % 2 == 0 else ""
            field_text = self.identity_text + cursor if self.identity_text else "TYPE YOUR ID"
            field_color = theme.CREAM if self.identity_text else theme.CREAM_DIM
            theme.draw_text(surface, field_text, field.center,
                            "small", field_color, anchor="center")
            instruction = self.identity_error or "TYPE A TAG  ·  ENTER: CONTINUE  ·  ESC: CANCEL"
            color = theme.CORAL if self.identity_error else theme.CREAM_DIM
            theme.draw_text(surface, instruction, (160, 111), "tiny", color, anchor="center")
