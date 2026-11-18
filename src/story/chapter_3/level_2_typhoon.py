"""Chapter 3 - Level 2: Harbor Gale & Snapback Hazard (Harbor).

Location: Harbor Breakwater & Fishing Jetty.
Disaster: Maritime Typhoon Gale (TCWS #3 & Gale Warning).

Mission flow (new mechanics, different from Level 1)
    1. Inspect mooring lines at the boat shed   -> LineInspection (go / no-go reaction)
    2. Cross the breakwater between wave sets    -> WaveSpray (timed lanes, knockback)
    3. Help Tatay Pio: choose safely, then ease
       the straining mooring line                -> TensionBalance (keep needle in band)
    4. A cable snaps: dodge snapback lines while
       the GALE countdown runs                   -> SnapbackLines + countdown
    5. Reach the Coast Guard bunker

Optional supplies (hard hat, radio, megaphone) boost the supply score.
"""

import random

import pygame

from src.story.base_level import (
    BaseLevel,
    MiniGame,
    FlyingDebris,
    ParticleField,
    Vignette,
    LightningFlash,
    draw_bar,
    draw_water,
)
from src.maps.block_map import BlockMap
from src.hazards.typhoon import TyphoonHazard
from src.config.palette import COLOR_GROUND_HARBOR, COLOR_UI_BORDER, COLOR_UI_DANGER, COLOR_UI_TEXT
from src.ui import theme


# ======================================================================
# New minigames
# ======================================================================
class TensionBalance(MiniGame):
    """Keep a straining mooring line's tension inside the green band.

    Gusts keep pushing the tension up. SPACE eases the line a little.
    Hold the needle in the band long enough to win; if it hits the red
    end the line snaps (fail), and being out of the band drains progress.
    """

    BAND = (0.32, 0.68)

    def __init__(self, title: str, hint: str, hold: float = 4.0,
                 time_limit: float = 16.0, **kw):
        kw.setdefault("footer", "[SPACE] Ease the line")
        super().__init__(title, hint, **kw)
        self.hold = hold
        self.time_limit = time_limit
        self.time_left = time_limit
        self.tension = 0.45
        self.progress = 0.0
        self._push = 0.0
        self._gust = random.uniform(0.6, 1.2)

    def current_hint(self) -> str:
        if self.tension > 0.82:
            return "TOO TIGHT! Ease the line now!"
        return self.hint

    def _tick(self, dt: float) -> None:
        self.time_left -= dt
        self._gust -= dt
        if self._gust <= 0:
            self._gust = random.uniform(0.7, 1.5)
            self._push = random.uniform(0.25, 0.45)
        self._push = max(0.0, self._push - 0.5 * dt)
        self.tension = max(0.0, self.tension + (0.12 + self._push) * dt)

        lo, hi = self.BAND
        if lo <= self.tension <= hi:
            self.progress += dt
        else:
            self.progress = max(0.0, self.progress - dt * 0.6)

        if self.tension >= 1.0 or self.time_left <= 0:
            self._finish(False)
        elif self.progress >= self.hold:
            self._finish(True)

    def _on_press(self) -> None:
        self.tension = max(0.0, self.tension - 0.10)

    def _draw_body(self, surface, rect, meter) -> None:
        pygame.draw.rect(surface, (18, 20, 26), meter)
        inner = meter.inflate(-4, -4)
        lo, hi = self.BAND

        # danger end
        dx = inner.x + int(0.85 * inner.w)
        danger_col = (200, 50, 45) if int(self.t * 6) % 2 == 0 else (140, 36, 34)
        pygame.draw.rect(surface, danger_col, (dx, inner.y, inner.right - dx, inner.h))
        # safe band
        bx = inner.x + int(lo * inner.w)
        bw = int((hi - lo) * inner.w)
        pygame.draw.rect(surface, (60, 170, 90), (bx, inner.y, bw, inner.h))
        # needle
        nx = inner.x + int(max(0.0, min(1.0, self.tension)) * inner.w)
        pygame.draw.rect(surface, (245, 245, 240), (nx - 1, meter.y, 3, meter.h))
        pygame.draw.rect(surface, COLOR_UI_BORDER, meter, 1)

        # hold progress + time left
        draw_bar(surface, pygame.Rect(meter.x, rect.y + 69, meter.w, 7),
                 self.progress / self.hold, (90, 200, 120), seg=6)


class LineInspection(MiniGame):
    """Go / no-go reaction game: reject frayed mooring lines with SPACE.

    Lines slide past one at a time. Press SPACE on a frayed line; let
    sound lines pass. Rejecting a good line or missing a bad one is a miss.
    """

    ROPE_A = (205, 172, 112)
    ROPE_B = (160, 128, 78)

    def __init__(self, title: str, hint: str, lines: int = 8, max_misses: int = 3,
                 show: float = 1.3, **kw):
        kw.setdefault("footer", "[SPACE] Reject frayed line")
        super().__init__(title, hint, **kw)
        self.total = lines
        self.max_misses = max_misses
        self.show = show

        bad_n = random.randint(3, max(3, lines // 2 + 1))
        bad_idx = set(random.sample(range(lines), bad_n))
        self.specs = [
            {
                "bad": i in bad_idx,
                "frays": [random.uniform(0.2, 0.8) for _ in range(2)],
            }
            for i in range(lines)
        ]
        self.index = 0
        self.timer = show
        self.gap = 0.0
        self.misses = 0
        self.results = []
        self.flash = 0.0
        self.flash_good = True

    def current_hint(self) -> str:
        if self.flash > 0 and not self.flash_good:
            return "Check the fibres carefully!"
        return self.hint

    def _tick(self, dt: float) -> None:
        self.flash = max(0.0, self.flash - dt)
        if self.gap > 0:
            self.gap -= dt
            return
        self.timer -= dt
        if self.timer <= 0:
            self._resolve(False)

    def _on_press(self) -> None:
        if self.gap <= 0:
            self._resolve(True)

    def _resolve(self, flagged: bool) -> None:
        spec = self.specs[self.index]
        correct = flagged == spec["bad"]
        if not correct:
            self.misses += 1
        self.results.append(correct)
        self.flash, self.flash_good = 0.35, correct
        self.index += 1
        self.timer = self.show
        self.gap = 0.3
        if self.misses >= self.max_misses:
            self._finish(False)
        elif self.index >= self.total:
            self._finish(True)

    def _draw_rope(self, surface, inner, spec) -> None:
        cy = inner.centery
        for i, x in enumerate(range(inner.x, inner.right, 5)):
            frac = (x - inner.x) / max(1, inner.w)
            thin = spec["bad"] and any(abs(frac - f) < 0.05 for f in spec["frays"])
            h = 2 if thin else 6
            col = self.ROPE_A if i % 2 == 0 else self.ROPE_B
            pygame.draw.rect(surface, col, (x, cy - h // 2, 5, h))
        if spec["bad"]:
            for f in spec["frays"]:
                fx = inner.x + int(f * inner.w)
                for dx, dy in ((-3, -4), (0, -5), (3, -4), (-2, 4), (2, 5)):
                    pygame.draw.line(surface, (230, 205, 150), (fx, cy), (fx + dx, cy + dy), 1)

    def _draw_body(self, surface, rect, meter) -> None:
        pygame.draw.rect(surface, (18, 20, 26), meter)
        inner = meter.inflate(-6, -6)
        if self.index < self.total and self.gap <= 0:
            self._draw_rope(surface, inner, self.specs[self.index])
            ratio = max(0.0, self.timer / self.show)
            pygame.draw.rect(surface, (240, 190, 70),
                             (meter.x, meter.bottom + 2, int(meter.w * ratio), 2))

        if self.flash > 0:
            border = (110, 230, 140) if self.flash_good else (255, 110, 100)
        else:
            border = COLOR_UI_BORDER
        pygame.draw.rect(surface, border, meter, 1)

        # one pip per line: green = right call, red = miss
        px = rect.x + 12
        for i in range(self.total):
            r = pygame.Rect(px + i * 10, rect.y + 69, 7, 7)
            if i < len(self.results):
                pygame.draw.rect(surface, (90, 220, 120) if self.results[i] else (220, 70, 60), r)
            pygame.draw.rect(surface, COLOR_UI_BORDER, r, 1)
        theme.draw_text(
            surface, f"MISS {self.misses}/{self.max_misses}",
            (rect.right - 10, rect.y + 68), size="tiny",
            color=COLOR_UI_DANGER if self.misses else COLOR_UI_TEXT,
            shadow=False, anchor="topright",
        )


# ======================================================================
# World hazards for this level
# ======================================================================
class WaveSpray:
    """Timed wave-spray lanes across the breakwater.

    Each lane cycles: idle -> warning (blinking) -> active spray. The lanes
    are phase-shifted so there is always a gap to slip through.
    """

    def __init__(self, rects, period: float = 4.0, warn: float = 1.1,
                 active: float = 0.8, offsets=None):
        self.rects = [pygame.Rect(r) for r in rects]
        self.period = period
        self.warn = warn
        self.active = active
        self.offsets = offsets or [i * (period / len(rects)) for i in range(len(rects))]
        self.t = 0.0

    def update(self, dt: float) -> None:
        self.t += dt

    def state(self, i: int) -> str:
        local = (self.t + self.offsets[i]) % self.period
        if local >= self.period - self.active:
            return "active"
        if local >= self.period - self.active - self.warn:
            return "warn"
        return "idle"

    def hits(self, rect: pygame.Rect) -> bool:
        return any(self.state(i) == "active" and rect.colliderect(r)
                   for i, r in enumerate(self.rects))

    def draw(self, surface: pygame.Surface, camera) -> None:
        for i, r in enumerate(self.rects):
            s = camera.apply(r)
            st = self.state(i)
            if st == "warn":
                if int(self.t * 8) % 2 == 0:
                    for x in range(s.left, s.right, 6):
                        surface.fill((200, 220, 245), (x, s.top, 3, 1))
                        surface.fill((200, 220, 245), (x, s.bottom - 1, 3, 1))
                    surface.fill((230, 70, 60), (s.centerx - 1, s.centery - 6, 3, 7))
                    surface.fill((230, 70, 60), (s.centerx - 1, s.centery + 3, 3, 2))
            elif st == "active":
                layer = pygame.Surface(s.size, pygame.SRCALPHA)
                layer.fill((200, 225, 250, 150))
                surface.blit(layer, s.topleft)
                rnd = random.Random(int(self.t * 20) + i)
                for _ in range(10):
                    surface.fill((255, 255, 255),
                                 (s.left + rnd.randrange(max(1, s.w - 2)),
                                  s.top + rnd.randrange(max(1, s.h - 2)), 2, 2))


class SnapbackLines(FlyingDebris):
    """Snapped mooring cables whipping across the walkway.

    Reuses FlyingDebris warning lanes + hit-testing but draws a rope.
    """

    SHEET_W, SHEET_H = 44, 5

    def draw(self, surface, camera):
        super().draw(surface, camera)  # warning lanes (+ plain sheet underneath)
        for s in self.sheets:
            r = camera.apply(pygame.Rect(int(s["x"]), s["y"], self.SHEET_W, self.SHEET_H))
            pygame.draw.rect(surface, (205, 172, 112), r)
            for x in range(r.left + 2, r.right, 5):
                pygame.draw.line(surface, (160, 128, 78), (x, r.top), (x, r.bottom - 1))
            pygame.draw.rect(surface, (24, 22, 32), r, 1)
            tip_x = r.right if s["dir"] > 0 else r.left
            surface.fill((255, 245, 170), (tip_x - 1, r.centery - 1, 3, 3))


# ======================================================================
# Level
# ======================================================================
class Chapter3Level2Typhoon(BaseLevel):
    GALE_TIME = 55.0
    GALE_RETRY = 30.0

    SPRAY_LANES = [(160, 158, 36, 44), (196, 158, 36, 44), (232, 158, 36, 44)]

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="chapter_3",
            level_id="level_2_typhoon",
            title="Chapter 3 - Level 2: The Crashing Seawall",
            subtitle="Harbor Jetty - Gale Warning & Mooring Safety",
            disaster_type="Typhoon & Gale Warning (PCG No-Sail)",
            lesson_source="Philippine Coast Guard (PCG) Sea Travel Advisory & Mooring Snapback Guidelines",
            lesson_text=(
                "Under PCG No-Sail protocols, all sea travel for vessels of any tonnage is strictly suspended.\n"
                "When mooring ships during severe gales, stay far away from taut synthetic ropes;\n"
                "a snapping mooring cable recoils with supersonic speed and lethal kinetic force.\n"
                "Anchor boats in sheltered coves and seek onshore shelter immediately."
            ),
        )

        # Level state (before building the world)
        self._pio_state = "idle"     # idle | busy | done
        self._cd = 0.0               # hint throttle
        self.spray = None
        self.snaps = None
        self._locker = None

        # Atmosphere
        self.rain = ParticleField("rain", seed=9, count=160)
        self.lightning = LightningFlash(interval=(5.0, 10.0), seed=21)
        self.vignette = Vignette(color=(20, 30, 50), max_alpha=120)

        self._build_world()

        self.hazards.append(TyphoonHazard(tcws_level=3))
        self.objectives = [
            "You inspect mooring lines at the boat shed",
            "You cross the spray and help Tatay Pio at the jetty",
            "You dodge snapback lines to the Coast Guard post",
        ]
        self.guide_points = [
            self.guide_interactable("lines"),
            self.guide_npc("Tatay Pio"),
            (520, 90),
        ]
        self.set_meter("safe", "SAFETY", 1.0, good_high=True)
        self.show_hint("Gale warning! Check the mooring lines at the boat shed.", 5.0)

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Harbor Seawall & Breakwater", width=640, height=360, ground_color=COLOR_GROUND_HARBOR
        )
        bm = self.block_map

        # Breakwater walkway, ramp up to the station, and sea
        bm.add_road(30, 160, 580, 40)
        bm.add_road(490, 128, 40, 34)
        bm.add_water(0, 240, 640, 120)

        # Buildings
        bm.add_building("warehouse", "BOAT SHED", 60, 60, 90, 70)
        bm.add_building("shelter", "COAST GUARD POST", 460, 50, 120, 80)
        bm.add_safe_zone(460, 50, 120, 80, label="PCG STATION", trigger_id="pcg_safe")

        # Wave splash strip (visual hazard along the seaward edge)
        bm.add_hazard_zone("flood", 180, 200, 180, 40, label="WAVE SPLASH")

        # Interactable: mooring line rack at the shed (inspection minigame)
        self._locker = self.add_interactable(
            "lines", "MOORING LINES", (62, 134, 24, 16), (160, 120, 70),
            on_interact=self._open_inspection,
        )

        # Timed wave-spray lanes across the walkway
        self.spray = WaveSpray(self.SPRAY_LANES, period=4.0, warn=1.1, active=0.8,
                               offsets=[0.0, 1.6, 3.0])

        # Optional supplies
        self.add_pickup("hardhat", "Hard Hat", (125, 144), "hardhat")
        self.add_pickup("radio", "Radio", (290, 142), "radio")
        self.add_pickup("megaphone", "Megaphone", (425, 142), "megaphone")

        # NPC beyond the spray zone
        self.add_npc(
            "tatay_pio",
            "Tatay Pio",
            (330, 140),
            [
                "The Coast Guard hoisted the red flag! No boats are allowed out to sea!",
                "The swell is lifting the bancas so violently that the nylon ropes are humming!",
                "Step back from the line tension! Do not stand in the snapback zone!",
            ],
            role="resident",
        )

        self.player.pos = pygame.Vector2(50, 175)
        self.player.rect.topleft = (50, 175)
        self.set_checkpoint((50, 175))

    # ------------------------------------------------------------------
    # Step 1: mooring line inspection
    # ------------------------------------------------------------------
    def _open_inspection(self, item):
        if item["done"]:
            self.show_hint("The lines are already inspected.", 2.5)
            return
        self.start_minigame(
            LineInspection(
                "INSPECT MOORING LINES",
                "Reject FRAYED lines (SPACE). Let sound lines pass.",
                lines=8, max_misses=3, show=1.3, icon="stick",
                win_text="LINES CHECKED!", fail_text="TOO MANY ERRORS!",
            ),
            on_win=self._inspection_done,
            on_fail=lambda: self.show_hint("Inspection failed. Try the rack again.", 3.0),
        )

    def _inspection_done(self):
        self._locker["done"] = True
        self.record_score("warnings_followed")
        self.set_checkpoint((100, 175))
        self.show_hint("Good eye. Now cross the spray lanes. Time the waves!", 4.5)
        if self.current_objective_idx == 0:
            self.complete_objective()

    # ------------------------------------------------------------------
    # Step 3: Tatay Pio - decision, then tension minigame
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Tatay Pio":
            return

        if self._pio_state == "done":
            self.start_dialogue("Tatay Pio", ["Run to the bunker! Stay low and clear of any taut line!"])
            return
        if self._pio_state == "busy":
            return
        if self.current_objective_idx < 1:
            self.start_dialogue("Tatay Pio", ["Check the mooring lines at the boat shed first, anak!"])
            return

        self._pio_state = "busy"
        self.ask(
            "harbor_snapback_choice",
            "A nylon mooring cable is stretched near maximum breaking tension. Where do you stand?",
            [
                {
                    "text": "Stand outside the rope's arc of recoil behind a reinforced concrete pillar",
                    "safe": True,
                    "lesson": "Positioning behind solid barriers protects personnel from catastrophic rope snap.",
                },
                {
                    "text": "Straddle the taut line while pulling down with your whole body weight",
                    "safe": False,
                    "lesson": "Parting lines snap back with force capable of amputating limbs or causing death.",
                },
            ],
            on_safe=self._start_tension_minigame,
            retry_hint="A snapping line can kill. Pick the safer position.",
        )

    def _start_tension_minigame(self):
        self.start_minigame(
            TensionBalance(
                "EASE THE MOORING LINE",
                "Keep the needle in the green band!",
                hold=4.0, time_limit=16.0, icon="stick",
                win_text="LINE STEADY!", fail_text="LINE SNAPPED!",
            ),
            on_win=self._line_secured,
            on_fail=self._line_failed,
        )

    def _line_failed(self):
        self._pio_state = "idle"
        self.show_hint("The line strained too far. Talk to Tatay Pio to try again.", 3.5)

    def _line_secured(self):
        self._pio_state = "done"
        self.score_system.assist_resident("Tatay Pio")
        self.set_checkpoint((340, 175))
        if self.current_objective_idx == 1:
            self.complete_objective()
        self._begin_snapback()

    # ------------------------------------------------------------------
    # Step 4: snapback lines + gale countdown
    # ------------------------------------------------------------------
    def _begin_snapback(self):
        self.snaps = SnapbackLines((300, 160, 310, 40), interval=(2.0, 3.2),
                                   speed=230.0, warn=1.1, seed=13)
        self.start_countdown(self.GALE_TIME, "GALE", self._gale_expired)
        self.show_hint("A cable snapped! Dodge the whipping lines to the bunker!", 5.0)

    def _gale_expired(self):
        self.hurt("The gale pushed you back to the checkpoint!", respawn=True)
        self.start_countdown(self.GALE_RETRY, "GALE", self._gale_expired)

    # ------------------------------------------------------------------
    # Step 5: reach the bunker
    # ------------------------------------------------------------------
    def on_trigger_activated(self, trigger_id: str):
        if trigger_id != "pcg_safe" or self.completed:
            return
        if self.current_objective_idx < 2:
            if self._cd <= 0:
                self.show_hint("Finish your tasks before sheltering.", 3.0)
                self._cd = 3.0
            return
        self.stop_countdown()
        self.score_system.complete_evacuation("ch3_2")
        self.complete_objective()  # last objective -> completes the level

    # ------------------------------------------------------------------
    # Per-frame hooks
    # ------------------------------------------------------------------
    def update_level(self, dt: float):
        self.rain.update(dt)
        self.lightning.update(dt)
        self._cd = max(0.0, self._cd - dt)
        self.set_meter("safe", "SAFETY", 1.0 - min(6, self.setbacks) / 6.0, good_high=True)

        if self.is_busy() or self.completed:
            return

        self.spray.update(dt)
        if self.spray.hits(self.player.rect):
            if self.hurt("Wave spray! Wait for the swell to pass."):
                # knock the player back so waves actually cost progress
                nx = max(30, self.player.rect.x - 24)
                self.player.rect.x = nx
                self.player.pos.x = nx

        if self.snaps is not None:
            self.snaps.update(dt)
            if self.snaps.hits(self.player.rect):
                self.hurt("Snapback! Stay out of the rope lanes.", respawn=True, penalty=5.0)

    def draw_under_player(self, surface: pygame.Surface):
        sea = self.camera.apply(pygame.Rect(0, 240, 640, 120))
        draw_water(surface, sea, self._anim_t, alpha=100, color=(30, 80, 140))
        draw_water(surface, sea.move(0, 4), self._anim_t * 1.4 + 3, alpha=40)

    def draw_over_world(self, surface: pygame.Surface):
        self.spray.draw(surface, self.camera)
        if self.snaps is not None:
            self.snaps.draw(surface, self.camera)
        self.rain.draw(surface)
        self.vignette.draw(surface, strength=0.5)
        self.lightning.draw(surface)