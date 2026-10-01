"""Living-scene effects and HUD widgets for the main menu.

HAZARDS: typhoon, flood, earthquake, volcano, wildfire. Each one is driven by a single
number (level, 0..1) that the backdrop computes. The typhoon code is unchanged.

TUNING: the anchors below are canvas pixels (320x180). Press F2 in the menu to see
markers on every anchor, then nudge the numbers until they sit on your art.
"""
import math
import random

import pygame

from src.core import settings
from src.core.strings import tips, tr
from src.ui import theme

W, H = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

HAZARDS = ["typhoon", "flood", "earthquake", "volcano", "wildfire"]

# ------------------------------------------------------------------
# ANCHORS (edit these to match your background art)
# ------------------------------------------------------------------
CHIMNEY = (46, 99)                    # cooking smoke rises from here (hut roof)
FLAG_BASE = (80, 121)                 # foot of the typhoon signal pole
LINE_A, LINE_B = (84, 139), (103, 137)    # clothesline ends
STORE_LAMP = (240, 124, 8, 3)         # sari-sari store lamp (x, y, w, h)
RADIO = (262, 141)                    # blinking radio
CHICKEN_LANE = (222, 310, 160)        # x_min, x_max, ground y
KID_LANE = (-8, 92, 160)

VOLCANO_CRATER = (237, 60)            # eruption plume, glow and lava bombs start here
LAVA_PATH = [(237, 62), (234, 70), (236, 79), (232, 89), (235, 99), (231, 109)]   # lava down the slope

# (x, ground y, big). Fires light up in this order as the wildfire grows.
FIRE_SPOTS = [(10, 150, 1), (300, 142, 1), (40, 128, 0), (262, 126, 0), (128, 118, 0),
              (214, 121, 0), (176, 117, 0), (96, 122, 0), (286, 152, 1), (150, 152, 1),
              (60, 146, 1), (110, 150, 0), (190, 150, 1), (236, 148, 1), (75, 118, 0),
              (250, 118, 0), (28, 140, 1), (272, 124, 0)]
FIRE_STEP = 0.05                      # each fire lights up this much later than the one before

RAIN_COUNT = 120
STORM_CYCLE = 7.0                     # seconds between lightning strikes at peak typhoon
FLOOD_RISE = 135                      # pixels the water climbs at the peak (135 reaches the title)
QUAKE_SHAKE = 3.0                     # max screen shake in pixels
ERUPT_CYCLE = 4.5                     # seconds between big blasts at peak eruption
BOMB_GRAVITY = 110.0

CLOUD_COLORS = {                      # (light, dark) cloud shades per hazard
    "typhoon": ((226, 230, 240), (62, 72, 98)),
    "flood": ((215, 222, 235), (80, 92, 118)),
    "volcano": ((150, 138, 135), (62, 54, 56)),
    "wildfire": ((140, 125, 115), (58, 50, 48)),
}


def level_for(storm):
    """Hazard strength 0..1 -> (danger level name, signal number 0..3)."""
    if storm < 0.15:
        return "NORMAL", 0
    if storm < 0.5:
        return "WATCH", 1
    if storm < 0.85:
        return "WARNING", 2
    return "CRITICAL", 3


# ------------------------------------------------------------------
# TINY SPRITES
# ------------------------------------------------------------------
PAL = {"R": (210, 60, 50), "W": (240, 235, 225), "Y": (240, 190, 60), "K": (40, 30, 30),
       "S": (240, 190, 150), "H": (50, 35, 30), "B": (70, 120, 200), "P": (90, 70, 60),
       "G": (220, 120, 40), "O": (245, 140, 40), "F": (255, 225, 100)}

CHICKEN = ["....RR..",
           "...WWKY.",
           "WW.WWW..",
           "WWWWWW..",
           ".WWWWW..",
           "..WWW...",
           "..Y.Y..."]

KID = [".HHH..",
       ".HSS..",
       ".SSS..",
       "GBBB..",
       "GBBB..",
       ".BBB..",
       ".PPP.."]
KID_LEGS = [[".P.P..", "P..P.."],
            ["..PP..", "..PP.."]]

FIRE_FRAMES = [
    ["...R....", "..RR....", "..ROR.R.", ".RROORR.", ".ROOFOR.", "RROFFFOR", "ROOFFFOR", "RROOOORR"],
    ["....R...", "...RR...", ".R.ROR..", ".RROOR..", "RROFOOR.", "ROFFFOR.", "ROFFFOOR", "RROOOORR"],
    ["...R....", "..RRR...", "..ROR...", ".RROORR.", "RROOFOR.", "ROOFFOR.", "RROFFFOR", "RROOOORR"],
]

# 8x8 icons for the Danger chip (added to the theme's icon table)
HAZARD_ICONS = {
    "ic_typhoon": ["..###...", ".#####..", "#######.", "########",
                   ".#.#.#..", "#.#.#.#.", ".#.#.#..", "........"],
    "ic_flood": ["........", "........", ".##..##.", "#..##..#",
                 "........", ".##..##.", "#..##..#", "########"],
    "ic_earthquake": ["...###..", "..##....", ".##.....", "######..",
                      "..##....", ".##.....", "##......", "#......."],
    "ic_volcano": ["..#..#..", "...##...", "...##...", "..####..",
                   ".######.", ".######.", "########", "########"],
    "ic_wildfire": ["...#....", "..##..#.", "..###.#.", ".#####..",
                    ".######.", "########", "########", ".######."],
}
theme.ICONS.update(HAZARD_ICONS)


class MenuFX:
    def __init__(self):
        rng = random.Random(9)
        self.birds = [(rng.uniform(0, W), rng.uniform(18, 56), rng.uniform(8, 16),
                       rng.uniform(0, 6.28)) for _ in range(4)]
        rng = random.Random(21)
        self.rain = [(rng.uniform(0, W + 20), rng.uniform(0, H), rng.uniform(150, 230))
                     for _ in range(RAIN_COUNT)]
        self.banks = [(rng.uniform(0, W), rng.uniform(6, 40), rng.uniform(46, 80), rng.uniform(4, 9))
                      for _ in range(7)]

        # extra randomness for the new hazards (separate seeds so the typhoon looks the same)
        rng = random.Random(33)
        self.cracks = []
        for sx in (150, 172, 200):
            pts, x, y = [(sx, 150)], sx, 150
            for _ in range(10):
                x += rng.randint(-6, 6)
                y += rng.randint(2, 4)
                pts.append((x, y))
            self.cracks.append(pts)
        self.dust = [(rng.uniform(20, 300), rng.uniform(146, 168), rng.uniform(0, 1)) for _ in range(9)]
        self.debris = [(rng.uniform(0, W), rng.uniform(8, 22)) for _ in range(5)]
        self.embers = [(rng.randrange(len(FIRE_SPOTS)), rng.uniform(0, 1),
                        rng.uniform(0.35, 0.7), rng.uniform(-1, 1)) for _ in range(80)]
        self.rng = random.Random(77)

        self.t = 0.0
        self.hazard = "typhoon"
        self.level = 0.0
        self.storm = 0.0          # typhoon strength only (0 for other hazards)
        self.sway = 0.0           # wind for laundry / smoke
        self.cloud = 0.0          # cloud-bank strength
        self.shake_amp = 0.0      # earthquake shake in pixels
        self.chicken_x, self.chicken_dir = float(CHICKEN_LANE[0]), 1
        self.kid_x, self.kid_dir = float(KID_LANE[0]), 1
        self._sprites = {}
        self._strike_on = False
        self.sounds = []          # (name, volume) waiting for the menu to play
        self.next_snd = {}
        self.bombs = []           # lava bombs [x, y, vx, vy, life]
        self.spawn = 0.0
        self.erupt_in = 1.5
        self.ring = None          # eruption shock ring age
        self.flash = 0.0
        self.water_top = H        # flood surface y (the title reads this)
        self.zap = None           # seconds since the last typhoon lightning strike (title reads this)

    # ---------- time ----------
    def update(self, dt, level, hazard="typhoon"):
        if hazard != self.hazard:                       # new disaster: reset its effects
            self.hazard = hazard
            self.bombs.clear()
            self.ring = None
            self.flash = 0.0
            self.erupt_in = 1.5
            self.next_snd.clear()
        self.t += dt
        t = self.t
        self.level = level
        self.storm = level if hazard == "typhoon" else 0.0
        self.sway = {"typhoon": level, "earthquake": 0.6 * level,
                     "wildfire": 0.5 * level}.get(hazard, 0.0)
        if hazard == "earthquake":
            self.cloud = 0.0
        elif hazard == "flood":
            self.cloud = level * 0.9
        else:
            self.cloud = level

        if hazard == "earthquake" and level > 0.2:
            self.shake_amp = level * (0.55 + 0.45 * abs(math.sin(t * 0.9))) * QUAKE_SHAKE
        else:
            self.shake_amp = 0.0

        # villagers
        self.chicken_x += self.chicken_dir * 6 * dt
        if self.chicken_x > CHICKEN_LANE[1]:
            self.chicken_dir = -1
        elif self.chicken_x < CHICKEN_LANE[0]:
            self.chicken_dir = 1
        self.kid_x += self.kid_dir * (16 + 30 * level) * dt      # runs faster in danger
        if self.kid_x > KID_LANE[1]:
            self.kid_dir = -1
        elif self.kid_x < KID_LANE[0]:
            self.kid_dir = 1

        # sounds
        if hazard == "earthquake" and level > 0.25:
            self._every("rumble", 1.5, 0.25 + 0.45 * level)
        elif hazard == "flood" and level > 0.3:
            self._every("swish", 2.6, 0.12 + 0.25 * level)
        elif hazard == "wildfire" and level > 0.2:
            self._every("crackle", 1.3, 0.12 + 0.35 * level)
        elif hazard == "volcano":
            self._volcano(dt)

        # lava bombs, ring and flash always age
        for b in self.bombs:
            b[3] += BOMB_GRAVITY * dt
            b[0] += b[2] * dt
            b[1] += b[3] * dt
            b[4] -= dt
        self.bombs = [b for b in self.bombs
                      if b[4] > 0 and b[1] < VOLCANO_CRATER[1] + 40]
        if self.ring is not None:
            self.ring += dt
            if self.ring > 0.8:
                self.ring = None
        self.flash = max(0.0, self.flash - dt)

    def _every(self, name, gap, volume):
        if self.t >= self.next_snd.get(name, 0.0):
            self.sounds.append((name, volume))
            self.next_snd[name] = self.t + gap

    def _volcano(self, dt):
        k = self.level
        if k > 0.2:
            self._every("rumble", 2.8, 0.15 + 0.2 * k)
        if k > 0.35:
            self.spawn -= dt
            if self.spawn <= 0:
                self._bomb()
                self.spawn = 1.0 / (3.0 + 16 * k)
        if k > 0.5:
            self.erupt_in -= dt
            if self.erupt_in <= 0:
                self.erupt_in = ERUPT_CYCLE * (1.5 - 0.6 * k)
                self.sounds.append(("boom", 0.55))
                self.flash = 0.18
                self.ring = 0.0
                for _ in range(10):
                    self._bomb(big=True)

    def _bomb(self, big=False):
        if len(self.bombs) >= 40:
            return
        r = self.rng
        sp = 1.4 if big else 1.0
        cx, cy = VOLCANO_CRATER
        self.bombs.append([cx + r.uniform(-3, 3), float(cy),
                           r.uniform(-34, 34) * sp, -r.uniform(55, 95) * sp, 3.0])

    def consume_sounds(self):
        out, self.sounds = self.sounds, []
        return out

    def shake_offset(self):
        m = int(round(self.shake_amp))
        if m < 1:
            return 0, 0
        r = random.Random(int(self.t * 30))
        h = (m + 1) // 2
        return r.randint(-m, m), r.randint(-h, h)

    # ---------- sprite cache ----------
    def _sprite(self, rows, flip, scale=1):
        key = (tuple(rows), flip, scale)
        if key not in self._sprites:
            s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    if ch in PAL:
                        s.set_at((x, y), PAL[ch])
            if flip:
                s = pygame.transform.flip(s, True, False)
            if scale > 1:
                s = pygame.transform.scale(s, (s.get_width() * scale, s.get_height() * scale))
            self._sprites[key] = s
        return self._sprites[key]

    # ---------- sky layer (before the palms) ----------
    def draw_sky(self, surface):
        t, cloud = self.t, self.cloud
        if cloud > 0.08:
            count = max(1, int(len(self.banks) * min(1.0, cloud * 1.5)))
            light, dark = CLOUD_COLORS.get(self.hazard, CLOUD_COLORS["typhoon"])
            shade = theme.mix(light, dark, min(1.0, cloud * 1.2))
            for x0, y, w, speed in self.banks[:count]:
                x = (x0 + t * speed) % (W + 2 * w) - w
                h = int(w * 0.28)
                pygame.draw.ellipse(surface, shade, (int(x), int(y), int(w), h))
                pygame.draw.ellipse(surface, shade, (int(x + w * 0.2), int(y - h * 0.4), int(w * 0.5), h))
                pygame.draw.ellipse(surface, shade, (int(x + w * 0.45), int(y + h * 0.1), int(w * 0.5), h))
        self._plume(surface)
        if self.level < 0.4:                              # birds go home when danger rises
            for bx, by, speed, ph in self.birds:
                x = int((bx + t * speed) % (W + 20) - 10)
                y = int(by + math.sin(t + ph) * 3)
                flap = 2 if math.sin(t * 8 + ph) > 0 else -1
                pygame.draw.line(surface, (40, 40, 60), (x - 3, y + flap), (x, y))
                pygame.draw.line(surface, (40, 40, 60), (x + 3, y + flap), (x, y))

    def _plume(self, surface):
        if self.hazard != "volcano" or self.level < 0.12:
            return
        k = self.level
        s = min(1.0, k * 1.5)
        cx, cy = VOLCANO_CRATER
        for j in range(28):
            age = (self.t * 0.2 + j / 28) % 1.0
            x = cx - age * (20 + 60 * k) + math.sin(age * 5 + j) * 3
            y = cy - age * (34 + 80 * k)
            r = int((3 + age * (8 + 9 * k)) * s)
            if r >= 1:
                pygame.draw.circle(surface, theme.mix((64, 56, 58), (150, 142, 146), age),
                                   (int(x), int(y)), r)

    # ---------- ground layer (before the grass) ----------
    def draw_ground(self, surface):
        self.water_top = H
        self._smoke(surface)
        self._flag(surface)
        self._laundry(surface)
        self._villagers(surface)
        self._quake_ground(surface)
        self._flood(surface)
        self._fire_smoke(surface)

    def _smoke(self, surface):
        cx, cy = CHIMNEY
        for k in range(6):
            age = (self.t * 0.35 + k / 6) % 1.0
            x = cx + math.sin(age * 5 + k) * 2 + age * (4 + 8 * self.sway)
            y = cy - age * 20
            size = 2 if age < 0.6 else 1
            surface.fill(theme.mix((225, 225, 232), (150, 155, 170), age),
                         (int(x), int(y), size, size))

    def _flag(self, surface):
        """Typhoon signal flag: rises as the storm grows, with one dot per signal level."""
        signal = level_for(self.storm)[1]
        bx, by = FLAG_BASE
        pygame.draw.line(surface, (70, 52, 36), (bx, by), (bx, by - 17))
        if signal:
            fy = by - 4 - signal * 4
            wave = max(-1, min(1, int(round(math.sin(self.t * 6) * (0.5 + self.storm)))))
            pygame.draw.rect(surface, theme.CORAL, (bx + 1, fy, 8 + wave, 5))
            for i in range(signal):
                surface.set_at((bx + 2 + i * 2, fy + 2), theme.CREAM)

    def _laundry(self, surface):
        (ax, ay), (bx, by) = LINE_A, LINE_B
        pygame.draw.line(surface, (70, 52, 36), (ax, ay), (ax, ay + 6))
        pygame.draw.line(surface, (70, 52, 36), (bx, by), (bx, by + 6))
        pts = []
        for i in range(9):
            u = i / 8
            pts.append((ax + (bx - ax) * u, ay + (by - ay) * u + 3 * 4 * u * (1 - u)))
        pygame.draw.lines(surface, theme.CREAM_DIM, False, pts, 1)
        colors = (theme.SKY, theme.CORAL, theme.CREAM, theme.HONEY)
        for color, u in zip(colors, (0.2, 0.42, 0.66, 0.86)):
            px = ax + (bx - ax) * u
            py = ay + (by - ay) * u + 3 * 4 * u * (1 - u)
            sway = math.sin(self.t * (2 + self.sway * 6) + u * 5) * (0.6 + self.sway * 2.2)
            pygame.draw.polygon(surface, color, [
                (int(px), int(py)), (int(px) + 3, int(py)),
                (int(px) + 3 + int(round(sway)), int(py) + 4), (int(px) + int(round(sway)), int(py) + 4)])

    def _villagers(self, surface):
        if self.level < 0.5:                              # the chicken hides from danger
            s = self._sprite(CHICKEN, self.chicken_dir < 0)
            bob = 1 if int(self.t * 4) % 2 else 0
            surface.blit(s, (int(self.chicken_x), CHICKEN_LANE[2] - s.get_height() + bob))
        if self.hazard == "flood" and self.level > 0.55:  # the kid evacuates when water is high
            return
        leg = int(self.t * (6 + 10 * self.level)) % 2
        s = self._sprite(KID + KID_LEGS[leg], self.kid_dir < 0)
        surface.blit(s, (int(self.kid_x), KID_LANE[2] - s.get_height()))

    # ---------- earthquake ----------
    def _quake_ground(self, surface):
        if self.hazard != "earthquake" or self.level < 0.2:
            return
        k = self.level
        s = min(1.0, (k - 0.2) / 0.5)
        for x, y, ph in self.dust:
            age = (self.t * 0.5 + ph) % 1.0
            r = int(1 + age * 5 * s)
            pygame.draw.circle(surface, theme.mix((205, 180, 145), (150, 130, 110), age),
                               (int(x), int(y - age * 14 * s)), r)
        grow = max(0.0, (k - 0.4) / 0.5)
        for pts in self.cracks:
            n = int(len(pts) * min(1.0, grow))
            if n >= 2:
                pygame.draw.lines(surface, (48, 30, 22), False, pts[:n], 1)

    # ---------- flood ----------
    def _flood(self, surface):
        if self.hazard != "flood" or self.level < 0.12:
            return
        t = self.t
        rise = int(FLOOD_RISE * min(1.0, self.level * 1.15))
        top = H - rise
        self.water_top = top
        layer = pygame.Surface((W, rise + 4), pygame.SRCALPHA)
        for x in range(0, W, 2):
            wy = int(2 + math.sin(x * 0.09 + t * 2.2) * 1.5 + math.sin(x * 0.23 - t * 3) * 0.8)
            pygame.draw.rect(layer, (75, 125, 180, 175), (x, wy, 2, rise + 4 - wy))
            pygame.draw.rect(layer, (190, 225, 245, 200), (x, wy, 2, 1))
        surface.blit(layer, (0, top - 2))
        for x0, speed in self.debris:                     # floating junk
            x = (x0 + t * speed) % (W + 20) - 10
            y = top + 2 + math.sin(t * 2 + x0)
            pygame.draw.rect(surface, (110, 72, 40), (int(x), int(y), 5, 2))
            pygame.draw.rect(surface, (150, 100, 60), (int(x), int(y), 5, 1))

    def water_y(self, x):
        """Surface height of the flood at column x (the title uses this to sit in the water)."""
        t = self.t
        wy = int(2 + math.sin(x * 0.09 + t * 2.2) * 1.5 + math.sin(x * 0.23 - t * 3) * 0.8)
        return self.water_top - 2 + wy

    # ---------- wildfire ----------
    @staticmethod
    def _lit(i, k):
        return k >= 0.12 + i * FIRE_STEP

    def _fire_smoke(self, surface):
        if self.hazard != "wildfire":
            return
        k = self.level
        for i, (x, y, _) in enumerate(FIRE_SPOTS):
            if not self._lit(i, k):
                continue
            for j in range(3):
                age = (self.t * 0.22 + j / 3 + i * 0.13) % 1.0
                px = x + math.sin(age * 4 + i) * 3 + age * (10 + 14 * k)
                py = y - 8 - age * (26 + 20 * k)
                pygame.draw.circle(surface, theme.mix((78, 70, 70), (130, 124, 124), age),
                                   (int(px), int(py)), int(2 + age * 5))

    def _fire(self, surface):
        k = self.level
        for i, (x, y, big) in enumerate(FIRE_SPOTS):
            if not self._lit(i, k):
                continue
            scale = 3 if (big and k > 0.8) else (2 if (big and k > 0.5) else 1)
            spr = self._sprite(FIRE_FRAMES[(int(self.t * 8) + i) % 3], False, scale)
            rect = spr.get_rect(midbottom=(x, y))
            surface.fill((34, 12, 0), rect.inflate(10, 8), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(spr, rect)
        for idx, ph, sp, drift in self.embers:
            if not self._lit(idx, k):
                continue
            sx, sy, _ = FIRE_SPOTS[idx]
            age = (self.t * sp + ph) % 1.0
            ex = sx + drift * 6 + age * (drift * 10 + 8)
            ey = sy - 6 - age * (30 + 30 * k)
            surface.set_at((int(ex), int(ey)), theme.mix((255, 200, 80), (160, 40, 20), age))

    # ---------- volcano ----------
    def _lava(self, surface):
        k = self.level
        if k < 0.1:
            return
        cx, cy = VOLCANO_CRATER
        flick = 0.8 + 0.2 * math.sin(self.t * 11) * math.sin(self.t * 3.7)
        g = int(200 * k * flick)
        surface.fill((g, int(g * 0.45), int(g * 0.1)), (cx - 3, cy - 2, 6, 3),
                     special_flags=pygame.BLEND_RGB_ADD)
        surface.fill((g // 5, g // 10, g // 30), pygame.Rect(cx - 3, cy - 2, 6, 3).inflate(24, 16),
                     special_flags=pygame.BLEND_RGB_ADD)
        cyc = self.t % 2.3                                # volcanic lightning inside the ash
        if k > 0.7 and cyc < 0.1:
            r = random.Random(int(self.t / 2.3))
            bx, by = cx + r.randint(-6, 6), cy - 20
            pts = [(bx, by)]
            for _ in range(5):
                bx += r.randint(-6, 6)
                by += r.randint(5, 9)
                pts.append((bx, by))
            pygame.draw.lines(surface, (255, 240, 200), False, pts, 1)
        surface.fill((g // 3, g // 6, g // 20), pygame.Rect(cx - 3, cy - 2, 6, 3).inflate(10, 8),
                     special_flags=pygame.BLEND_RGB_ADD)
        n = int(len(LAVA_PATH) * min(1.0, k * 1.3))
        if n >= 2:
            pygame.draw.lines(surface, (255, int(110 + 70 * flick), 40), False, LAVA_PATH[:n], 1)
        for x, y, vx, vy, _ in self.bombs:
            surface.fill((255, 170, 60), (int(x), int(y), 2, 2))
            surface.set_at((int(x - vx * 0.04), int(y - vy * 0.04)), (220, 90, 30))
        if self.ring is not None:
            r = int(self.ring * 80)
            size = 2 * r + 4
            f = 1 - self.ring / 0.8
            s = pygame.Surface((size, size))
            pygame.draw.circle(s, (int(150 * f), int(80 * f), int(30 * f)), (size // 2, size // 2), r, 1)
            surface.blit(s, (cx - size // 2, cy - size // 2), special_flags=pygame.BLEND_RGB_ADD)
        if self.flash > 0:
            v = int(70 * self.flash / 0.18)
            surface.fill((v, int(v * 0.6), int(v * 0.25)), special_flags=pygame.BLEND_RGB_ADD)

    # ---------- after the day/night tint ----------
    def draw_lights(self, surface, night):
        if night > 0.3:
            flicker = 0.75 + 0.25 * math.sin(self.t * 17) * math.sin(self.t * 5.3)
            g = int(130 * night * flicker)
            surface.fill((g, int(g * 0.75), int(g * 0.3)), STORE_LAMP,
                         special_flags=pygame.BLEND_RGB_ADD)
            surface.fill((g // 4, g // 5, g // 10), pygame.Rect(STORE_LAMP).inflate(6, 4),
                         special_flags=pygame.BLEND_RGB_ADD)
        color = (255, 70, 60) if int(self.t * 2) % 2 == 0 else (110, 40, 40)
        surface.set_at(RADIO, color)
        surface.set_at((RADIO[0] + 1, RADIO[1]), color)
        if self.hazard == "volcano":
            self._lava(surface)
        elif self.hazard == "wildfire":
            self._fire(surface)

    def draw_weather(self, surface):
        t, k, h = self.t, self.level, self.hazard
        self.zap = None

        amount, slant = 0.0, 0.25
        if h == "typhoon" and k > 0.35:
            amount = (k - 0.35) / 0.65
        elif h == "flood" and k > 0.1:
            amount, slant = min(1.0, k / 0.5) * 0.7, 0.08
        if amount > 0:
            count = int(len(self.rain) * min(1.0, amount))
            for x, y, speed in self.rain[:count]:
                px = int((x - t * speed * slant) % (W + 20) - 10)
                py = int((y + t * speed) % H)
                pygame.draw.line(surface, (170, 195, 230), (px + 2, py - 4), (px, py))

        if h == "volcano" and k > 0.3:                    # falling ash
            n = int(115 * min(1.0, (k - 0.3) / 0.5))
            for x, y, speed in self.rain[:n]:
                px = int((x + t * 5 + math.sin(t + y) * 3) % W)
                py = int((y + t * speed * 0.12) % H)
                surface.set_at((px, py), (170, 162, 156))
                surface.set_at((px + 1, py), (120, 112, 108))

        if h == "wildfire" and k > 0.1:                   # orange haze
            g = int(70 * min(1.0, k * 1.3))
            surface.fill((g, g // 3, 0), (0, 70, W, H - 70), special_flags=pygame.BLEND_RGB_ADD)

        if h == "typhoon" and k > 0.85:
            cycle = t % STORM_CYCLE
            self.zap = cycle
            first = cycle < 0.07
            flash = 1.0 if first else (0.6 if 0.14 <= cycle < 0.22 else 0.0)
            if first and not self._strike_on:
                self.sounds.append(("thunder", 0.5))
            self._strike_on = first
            if flash:
                v = int(95 * flash)
                surface.fill((v, v, v + 12), special_flags=pygame.BLEND_RGB_ADD)
            if first:
                rng = random.Random(int(t // STORM_CYCLE))
                x = rng.randint(40, 280)
                pts = [(x, 0)]
                for y in range(10, 95, 10):
                    x += rng.randint(-8, 8)
                    pts.append((x, y))
                pygame.draw.lines(surface, (255, 255, 235), False, pts, 1)
        else:
            self._strike_on = False

    def draw_debug(self, surface):
        for pos in (CHIMNEY, FLAG_BASE, LINE_A, LINE_B, RADIO, VOLCANO_CRATER):
            pygame.draw.rect(surface, (255, 0, 255), (pos[0] - 1, pos[1] - 1, 3, 3), 1)
        pygame.draw.rect(surface, (255, 255, 0), STORE_LAMP, 1)
        for lane in (CHICKEN_LANE, KID_LANE):
            pygame.draw.line(surface, (0, 255, 255), (lane[0], lane[2]), (lane[1], lane[2]))
        pygame.draw.lines(surface, (255, 128, 0), False, LAVA_PATH, 1)
        for x, y, _ in FIRE_SPOTS:
            pygame.draw.rect(surface, (255, 80, 0), (x - 2, y - 2, 5, 5), 1)


# ------------------------------------------------------------------
# HUD WIDGETS (drawn by the main menu, after the buttons)
# ------------------------------------------------------------------
_footer = None


def draw_alert_chip(surface, t, level, hazard="typhoon"):
    """Danger Meter preview: hazard icon, danger level and hazard name."""
    name, _ = level_for(level)
    color = theme.LEVEL_COLORS[name]
    rect = pygame.Rect(4, 4, 66, 22)
    theme.draw_panel(surface, rect, alpha=215, accent=color)
    if name != "CRITICAL" or int(t * 3) % 2 == 0:
        theme.draw_icon(surface, "ic_" + hazard, (rect.x + 3, rect.y + 7), color)
    theme.draw_text(surface, tr(name), (rect.x + 14, rect.y + 3), "tiny", color, shadow=False)
    theme.draw_text(surface, tr("h_" + hazard), (rect.x + 14, rect.y + 12), "tiny",
                    theme.CREAM_DIM, shadow=False)


def draw_gobag(surface, t):
    """Four go-bag items that fill in one by one."""
    rect = pygame.Rect(268, 4, 48, 13)
    theme.draw_panel(surface, rect, alpha=215, accent=theme.SKY)
    filled = min(int(t / 1.4) % 7, 4)
    for i, name in enumerate(("light", "water", "radio", "aid")):
        color = theme.HONEY if i < filled else theme.PLUM_LIGHT
        theme.draw_icon(surface, name, (rect.x + 3 + i * 11, rect.y + 2), color)


def draw_footer(surface, t):
    """Rotating preparedness tip on a dark strip, plus the version number."""
    global _footer
    if _footer is None:
        _footer = pygame.Surface((W, 14), pygame.SRCALPHA)
        _footer.fill((*theme.SHADOW, 150))
    surface.blit(_footer, (0, H - 14))
    lines = tips()
    theme.draw_text(surface, lines[int(t // 6) % len(lines)], (W // 2, H - 7), "tiny",
                    theme.CREAM, shadow=False, anchor="center")
    theme.draw_text(surface, "v0.1", (W - 4, H - 7), "tiny", theme.CREAM_DIM,
                    shadow=False, anchor="midright")