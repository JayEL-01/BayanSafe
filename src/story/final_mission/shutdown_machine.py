"""Final Mission: Shut Down the Machine.

Location: Project Aegis-Terra Subterranean Core Control Room.
Antagonist: Dr. Elias Voss.
Objectives: Confront Dr. Elias Voss, execute scram protocols, deactivate artificial seismic core.

Flow (4 numbered steps, each unlocks the next, gold arrow on the target):
  1. Grab the MASTER KEY below TERMINAL A
  2. Confront Dr. Voss at the AEGIS CORE
  3. Vent the injectors at the MANIFOLD panel (decision + valve mini-game)
  4. Scram the core at the SCRAM console (decision + phase-dampening mini-game)

Pressure: a CORE OVERLOAD countdown with a RESONANCE meter, arc flashes that
cross the aisle after a red warning, and wrong answers that cost time.
"""

import math
import random

import pygame
from src.story.base_level import BaseLevel, ParticleField, Vignette, TimingMeter
from src.maps.block_map import BlockMap
from src.hazards.earthquake import EarthquakeHazard
from src.config.palette import COLOR_GROUND_FACILITY
from src.core.decision_system import Decision


# ----------------------------------------------------------------------
# Small level-local helpers (pixel effects)
# ----------------------------------------------------------------------
class _ArcLanes:
    """Electric arcs that flash across the aisle after a red warning."""

    WARN, LIVE = 1.1, 0.45

    def __init__(self, xs, y0, y1, width=10, gap=(2.2, 3.4), seed=7):
        self.lanes = [pygame.Rect(x, y0, width, y1 - y0) for x in xs]
        self.gap = gap
        self.rnd = random.Random(seed)
        self.timer = self.rnd.uniform(*gap)
        self.state = {}          # lane index -> ["warn"|"live", seconds left]
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.rnd.uniform(*self.gap)
            free = [i for i in range(len(self.lanes)) if i not in self.state]
            if free:
                self.state[self.rnd.choice(free)] = ["warn", self.WARN]
        for i, s in list(self.state.items()):
            s[1] -= dt
            if s[1] <= 0:
                if s[0] == "warn":
                    s[0], s[1] = "live", self.LIVE
                else:
                    del self.state[i]

    def hits(self, rect):
        return any(
            rect.colliderect(self.lanes[i])
            for i, s in self.state.items() if s[0] == "live"
        )

    def draw(self, surface, camera):
        blink = int(self.t * 10) % 2 == 0
        for i, s in self.state.items():
            r = camera.apply(self.lanes[i])
            cx = r.centerx
            if s[0] == "warn":
                for y in range(r.top, r.bottom, 6):
                    surface.fill((220, 70, 60), (cx - 1, y, 2, 3))
                if blink:
                    surface.fill((240, 90, 70), (cx - 1, r.top - 9, 3, 6))
                    surface.fill((240, 90, 70), (cx - 1, r.top - 1, 3, 2))
            else:
                rnd = random.Random(int(self.t * 30) + i * 97)
                pts = [
                    (cx + rnd.randint(-4, 4) * (1 if k % 2 else -1), y)
                    for k, y in enumerate(range(r.top, r.bottom + 1, 6))
                ]
                pygame.draw.lines(surface, (60, 150, 230), False, pts, 5)
                pygame.draw.lines(surface, (235, 250, 255), False, pts, 2)
                for dx, dy in ((-3, -2), (3, 2)):
                    surface.fill((255, 240, 150), (pts[-1][0] + dx, pts[-1][1] + dy, 2, 2))


def _draw_arrow(surface, camera, pt, t):
    """Bobbing gold arrow whose tip sits on world point *pt*."""
    x, y = camera.apply(pygame.Rect(int(pt[0]), int(pt[1]), 1, 1)).topleft
    w, h = surface.get_size()
    x = max(8, min(w - 8, x))
    y = max(20, min(h - 8, y))
    tip = y + int(round(math.sin(t * 5.0) * 2))
    pygame.draw.polygon(surface, (24, 22, 32), [(x - 7, tip - 11), (x + 7, tip - 11), (x, tip + 3)])
    pygame.draw.polygon(surface, (250, 210, 90), [(x - 5, tip - 9), (x + 5, tip - 9), (x, tip)])


def _mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


class FinalMissionShutdownMachine(BaseLevel):
    # Layout constants (world coordinates) - tweak here
    PLAYER_START = (60, 175)
    KEY_POS = (100, 140)                 # the MASTER KEY map item below
    VOSS_POS = (380, 140)
    MANIFOLD_RECT = (205, 140, 30, 16)   # under TERMINAL B
    SCRAM_RECT = (440, 146, 36, 16)      # under the AEGIS CORE
    CORE_RECT = (340, 50, 140, 90)
    TERMINALS = [(60, 60, 95, 75), (180, 60, 95, 75), (500, 50, 90, 75)]
    ARC_X = (170, 215, 260)
    SURGE_POS = (222, 238)

    OVERLOAD_SECONDS = 180
    OVERLOAD_REPEAT = 70
    VENT_BONUS = 35                      # seconds gained for venting the manifold

    STEP_HINTS = [
        "Alarms blaring! Grab the MASTER KEY below TERMINAL A (follow the arrow).",
        "Key secured. Confront Dr. Voss at the AEGIS CORE.",
        "Voss says vent the injectors first: use the MANIFOLD panel under TERMINAL B.",
        "Pressure is down. Go to the SCRAM console under the core and use the keycard.",
    ]
    ARROW_POINTS = [(100, 128), (380, 124), (220, 130), (458, 138)]

    def __init__(self, game):
        super().__init__(
            game=game,
            chapter_id="final_mission",
            level_id="shutdown_machine",
            title="Final Mission: The Aegis Core",
            subtitle="Central Facility Bunker - Confrontation with Dr. Elias Voss",
            disaster_type="Catastrophic Resonance Overload",
            lesson_source="Philippine Institute of Volcanology and Seismology (PHIVOLCS) Geological Hazard Assessment",
            lesson_text=(
                "Nature cannot be conquered through reckless technological hubris.\n"
                "True community safety is built on resilience, early warnings,\n"
                "transparent public communication, and collective preparedness.\n"
                "A united community that heeds verified science will endure any disaster."
            ),
        )
        # Progress flags (set before the world is built)
        self._has_key = False
        self._voss_met = False
        self._voss_confronted = False
        self._depressurized = False
        self._core_scrammed = False
        self._manifold_ok = False        # injector question answered safely
        self._manifold_vented = False
        self._scram_ok = False           # coil question answered safely
        self._scram_done = False
        self._final_pending = False      # closing Voss dialogue, then complete
        self._surge_used = False
        self._ov_total = float(self.OVERLOAD_SECONDS)
        self._flicker = None

        self.arcs = _ArcLanes(self.ARC_X, 138, 212)
        self.dust = ParticleField("dust", seed=5, count=22)
        self.alarm = Vignette(color=(150, 20, 20), max_alpha=150)

        self._build_world()
        self.hazards.append(EarthquakeHazard(intensity=7))
        self.objectives = [
            "You grab the MASTER KEY at Terminal A",
            "You confront Dr. Voss at the AEGIS Core",
            "You vent injectors at the Terminal B panel",
            "You scram the core at the AEGIS Core console",
        ]
        self.guide_points = list(self.ARROW_POINTS)
        self.set_checkpoint(self.PLAYER_START)
        self.set_meter("resonance", "RESONANCE", 0.0, good_high=False)
        self.start_countdown(self.OVERLOAD_SECONDS, "CORE OVERLOAD", on_expire=self._overload)
        self.show_hint(self.STEP_HINTS[0], 6.0)
        self.enable_world_ambience()

    # ------------------------------------------------------------------
    # World
    # ------------------------------------------------------------------
    def _build_world(self):
        self.block_map = BlockMap(
            "Aegis-Terra Subterranean Control Core",
            width=640,
            height=360,
            ground_color=COLOR_GROUND_FACILITY,
        )
        bm = self.block_map

        # High-tech facility flooring & server aisles
        bm.add_road(40, 160, 560, 40)
        bm.add_road(300, 40, 40, 260)

        # Core reactor chamber & server mainframes
        bm.add_building("research", "TERMINAL A", 60, 60, 95, 75)
        bm.add_building("research", "TERMINAL B", 180, 60, 95, 75)
        bm.add_building("research", "AEGIS CORE", 340, 50, 140, 90)
        bm.add_building("research", "BACKUP SCRAM", 500, 50, 90, 75)
        bm.add_safe_zone(340, 50, 140, 90, label="SCRAM CONSOLE", trigger_id="scram_zone")

        # Keycard item (kept as a map item so inventory / stats stay connected)
        bm.add_item("key", "MASTER KEY", *self.KEY_POS)

        # Control panels the player operates
        self.add_interactable(
            "manifold", "MANIFOLD", self.MANIFOLD_RECT, (90, 160, 220),
            on_interact=self._use_manifold,
        )
        self.add_interactable(
            "scram", "SCRAM", self.SCRAM_RECT, (220, 70, 60),
            on_interact=self._use_scram,
        )

        # Optional gear: soaks up one arc flash
        self.add_pickup("surge", "SURGE KIT", self.SURGE_POS, "firstaid")

        # Antagonist NPC: Dr. Elias Voss
        self.add_npc(
            "dr_elias_voss",
            "Dr. Elias Voss",
            self.VOSS_POS,
            [
                "You don't understand what you're interfering with!",
                "I was building a machine to bleed off tectonic pressure in controlled pulses!",
                "The resonance harmonic ran away! If we don't scram the core, the faultline tears open!",
            ],
            role="antagonist",
        )

        self.player.pos = pygame.Vector2(*self.PLAYER_START)
        self.player.rect.topleft = self.PLAYER_START

    # ------------------------------------------------------------------
    # Quest steps
    # ------------------------------------------------------------------
    def _step_done(self, i):
        return (self._has_key, self._voss_met, self._manifold_vented)[i] if i < 3 else False

    def _sync_steps(self):
        """Advance through every step whose condition is already satisfied."""
        while self.current_objective_idx < 3 and self._step_done(self.current_objective_idx):
            self.complete_objective()
            self.show_hint(self.STEP_HINTS[self.current_objective_idx], 6.0)

    def _need_first(self):
        i = min(self.current_objective_idx, len(self.objectives) - 1)
        self.show_hint("Finish first: " + self.objectives[i], 3.5)

    def on_item_collected(self, item_id: str):
        if item_id == "key":
            self._has_key = True

    # ------------------------------------------------------------------
    # Pressure: overload countdown, arc flashes
    # ------------------------------------------------------------------
    def _resonance(self):
        if self._scram_done or not self.countdown_active:
            return 0.0
        return max(0.0, min(1.0, 1.0 - self.countdown_time / max(1.0, self._ov_total)))

    def _overload(self):
        if self.completed or self._scram_done:
            return
        self._ov_total = float(self.OVERLOAD_REPEAT)
        self.start_countdown(self.OVERLOAD_REPEAT, "CORE OVERLOAD", on_expire=self._overload)
        self.hurt("CORE SURGE! The blast threw you back to the entrance.", respawn=True)

    def _arc_hit(self):
        if self.has_item("surge") and not self._surge_used:
            self._surge_used = True
            self.invuln = 1.0
            self.show_hint("The SURGE KIT absorbed the arc flash! (used up)", 3.0)
            return
        self.hurt("ARC FLASH! Wait for the red warning to pass.", penalty=6)

    def update_level(self, dt):
        self.dust.update(dt)
        if self.completed:
            return

        # Closing beat: after Voss's last words, finish the mission
        if (self._final_pending and self.active_dialogue is None
                and not self.decision_system.is_active() and self.minigame is None):
            self._final_pending = False
            self.complete_objective(3)         # step 4 -> completes the level
            return

        if self.is_busy():
            return

        self._sync_steps()
        self.arcs.update(dt)
        if self.arcs.hits(self.player.rect):
            self._arc_hit()
        if self.countdown_active:
            self.set_meter("resonance", "RESONANCE", self._resonance(), good_high=False)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_under_player(self, surface):
        cam, t = self.camera, self._anim_t
        ratio = self._resonance()

        # Blinking server LEDs along the top of each terminal
        for (x, y, w, h) in self.TERMINALS:
            r = cam.apply(pygame.Rect(x, y, w, h))
            for k in range(5):
                on = int(t * 3 + k * 1.7) % 3 != 0
                if on:
                    col = (230, 70, 60) if ratio > 0.7 else (90, 230, 140)
                else:
                    col = (30, 60, 50)
                surface.fill(col, (r.x + 8 + k * 14, r.y + 8, 4, 3))

        # The Aegis core: pulsing pixel rings, cyan -> red as resonance climbs
        cx, cy = cam.apply(pygame.Rect(self.CORE_RECT)).center
        if self._scram_done:
            for i, sz in enumerate((14, 26, 38)):
                half = sz // 2
                pygame.draw.rect(surface, _mix((40, 70, 80), (20, 30, 36), i / 3),
                                 (cx - half, cy - half, half * 2, half * 2), 2)
            surface.fill((70, 110, 120), (cx - 3, cy - 3, 6, 6))
        else:
            pulse = 0.5 + 0.5 * math.sin(t * (3 + 6 * ratio))
            base = _mix((80, 220, 230), (235, 60, 50), ratio)
            for i, sz in enumerate((14, 26, 38, 50)):
                half = sz // 2 + int(pulse * 3)
                pygame.draw.rect(surface, _mix(base, (20, 24, 30), i * 0.2),
                                 (cx - half, cy - half, half * 2, half * 2), 2)
            surface.fill(_mix(base, (255, 255, 255), 0.5), (cx - 5, cy - 5, 10, 10))

    def draw_over_world(self, surface):
        self.arcs.draw(surface, self.camera)
        self.dust.draw(surface)

        ratio = self._resonance()
        if ratio > 0.35:
            pulse = 0.55 + 0.45 * math.sin(self._anim_t * (4 + 8 * ratio))
            self.alarm.draw(surface, ((ratio - 0.35) / 0.65) * pulse)
        if ratio > 0.5 and int(self._anim_t * 7) % 11 == 0:   # power flicker
            if self._flicker is None or self._flicker.get_size() != surface.get_size():
                self._flicker = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                self._flicker.fill((0, 0, 0, 55))
            surface.blit(self._flicker, (0, 0))

        # Guide arrow for the current step (hidden while you are busy / close)
        i = self.current_objective_idx
        if (not self.completed and not self._scram_done and i < len(self.ARROW_POINTS)
                and not self.is_busy()):
            px, py = self.player.rect.center
            tx, ty = self.ARROW_POINTS[i]
            if (px - tx) ** 2 + (py - (ty + 10)) ** 2 > 28 * 28:
                _draw_arrow(surface, self.camera, self.ARROW_POINTS[i], self._anim_t)

    # ------------------------------------------------------------------
    # Questions with a cost for wrong answers
    # ------------------------------------------------------------------
    def _ask_costly(self, decision_id, prompt, options, on_safe, wrong_msg, penalty=12):
        """Like self.ask(), but a wrong answer also costs core time + a jolt."""

        def builder():
            def on_decide(opt):
                if self.is_safe_option(opt):
                    on_safe()
                else:
                    self.hurt("", penalty=penalty)
                    self.show_hint(wrong_msg, 4.0)
                    self.queue_decision(builder)

            return Decision(
                decision_id=decision_id,
                prompt=prompt,
                options=options,
                on_resolved=on_decide,
            )

        self.queue_decision(builder)

    # ------------------------------------------------------------------
    # Step 2: Dr. Voss
    # ------------------------------------------------------------------
    def on_npc_interacted(self, npc):
        if npc.name != "Dr. Elias Voss":
            return
        if not self._voss_confronted:
            self._voss_met = True
            self.start_dialogue("Dr. Elias Voss", [
                "You don't understand what you're interfering with!",
                "I was building a machine to bleed off tectonic pressure in controlled pulses!",
                "The resonance harmonic ran away! If we don't scram the core, the faultline tears open!",
            ])
            self._ask_costly(
                "scram_step_1",
                "Manifold pressure is critical. How do you vent the thermal injectors?",
                [
                    {
                        "text": "Open bypass pressure-relief valves into the auxiliary basalt buffer chamber",
                        "safe": True,
                        "lesson": "Controlled pressure equalization prevents catastrophic explosive shockwaves.",
                    },
                    {
                        "text": "Slam the emergency shutoff valve shut while pressure is rising at peak rate",
                        "safe": False,
                        "lesson": "Abrupt valve closures against superheated steam cause explosive water hammer ruptures.",
                    },
                ],
                on_safe=self._voss_step1_safe,
                wrong_msg="PRESSURE SPIKE! Never slam a valve against rising steam. Try again.",
            )
            return

        if self._depressurized and not self._scram_ok:
            self.start_dialogue("Dr. Elias Voss", [
                "The manifold is stabilized, but the magnetic coils are running away!",
                "We have seconds before inductive feedback shatters the facility bedrock!",
            ])
            self._ask_costly(
                "scram_step_2",
                "The resonance harmonic is vibrating the bedrock. How do you disconnect the coils?",
                [
                    {
                        "text": "Insert master scram keycard and execute graduated phase-frequency dampening",
                        "safe": True,
                        "lesson": "Gradual phase dampening stabilizes the subterranean faultline without triggering shockwaves.",
                    },
                    {
                        "text": "Smash the main circuit breaker with a metal crowbar to cut all power instantly",
                        "safe": False,
                        "lesson": "Inductive back-EMF discharge under heavy load causes massive arc explosions.",
                    },
                ],
                on_safe=self._voss_step2_safe,
                wrong_msg="ARC EXPLOSION! Never cut power under load. Dampen the phases gradually.",
                penalty=15,
            )
            return

        # Later visits: a short reminder for the current step
        i = self.current_objective_idx
        if i <= 1:
            lines = ["You'll need the MASTER KEY from TERMINAL A to scram the core!"]
        elif i == 2:
            lines = ["Vent the injectors at the TERMINAL B panel first. Bypass valves, never the shutoff!"]
        else:
            lines = ["The SCRAM console under the core! Insert the keycard and dampen the coils slowly!"]
        self.start_dialogue("Dr. Elias Voss", lines)

    def _voss_step1_safe(self):
        self._voss_confronted = True
        self._manifold_ok = True
        if self.current_objective_idx < 2:
            self.complete_objective()
        self.show_hint("Voss convinced! Vent the injectors at the TERMINAL B manifold panel.", 4.0)

    def _voss_step2_safe(self):
        self._scram_ok = True
        self.show_hint("Execute the phase dampening at the SCRAM console under the core!", 4.0)

    def _interact_bypass(self):
        self._manifold_game(None)

    def _bypass_success(self):
        self._manifold_done(None)

    def _interact_scram(self):
        self._scram_game(None)

    # ------------------------------------------------------------------
    # Step 3: vent the injector manifold
    # ------------------------------------------------------------------
    def _use_manifold(self, item):
        if item["done"]:
            return
        if self.current_objective_idx < 2:
            self._need_first()
            return
        if self._manifold_ok:
            self._manifold_game(item)
            return
        self._ask_costly(
            "scram_step_1",
            "Manifold pressure is critical. How do you vent the thermal injectors?",
            [
                {
                    "text": "Open bypass pressure-relief valves into the auxiliary basalt buffer chamber",
                    "safe": True,
                    "lesson": "Controlled pressure equalization prevents catastrophic explosive shockwaves.",
                },
                {
                    "text": "Slam the emergency shutoff valve shut while pressure is rising at peak rate",
                    "safe": False,
                    "lesson": "Abrupt valve closures against superheated steam cause explosive water hammer ruptures.",
                },
            ],
            on_safe=lambda: self._manifold_answered(item),
            wrong_msg="PRESSURE SPIKE! Never slam a valve against rising steam. Try again.",
        )

    def _manifold_answered(self, item):
        self._manifold_ok = True
        self._manifold_game(item)

    def _manifold_game(self, item):
        self.start_minigame(
            TimingMeter(
                "DEPRESSURIZE MANIFOLD", "",
                steps=[
                    "Open bypass valve A",
                    "Open bypass valve B",
                    "Equalize into the basalt buffer",
                ],
                speed=0.95, zone=0.26, max_misses=3,
                icon="fuelcan", win_text="PRESSURE STABLE!",
            ),
            on_win=lambda: self._manifold_done(item),
            on_fail=lambda: self.hurt("The valve jammed! Pressure is still rising. Try again.", penalty=8),
        )

    def _manifold_done(self, item=None):
        if item and isinstance(item, dict):
            item["done"] = True
        self._manifold_vented = True
        self._depressurized = True
        self._ov_total += self.VENT_BONUS
        if self.countdown_active:
            self.countdown_time += self.VENT_BONUS
        self.show_hint(f"Injectors vented! +{self.VENT_BONUS}s on the core timer.", 4.0)

    # ------------------------------------------------------------------
    # Step 4: scram the core
    # ------------------------------------------------------------------
    def _use_scram(self, item):
        if item["done"]:
            return
        if self.current_objective_idx < 3:
            self._need_first()
            return
        if not self._has_key:
            self.show_hint("You need the MASTER KEY from TERMINAL A.", 3.5)
            return
        if self._scram_ok:
            self._scram_game(item)
            return
        self._ask_costly(
            "scram_step_2",
            "The resonance harmonic is vibrating the bedrock. How do you disconnect the coils?",
            [
                {
                    "text": "Insert master scram keycard and execute graduated phase-frequency dampening",
                    "safe": True,
                    "lesson": "Gradual phase dampening stabilizes the subterranean faultline without triggering shockwaves.",
                },
                {
                    "text": "Smash the main circuit breaker with a metal crowbar to cut all power instantly",
                    "safe": False,
                    "lesson": "Inductive back-EMF discharge under heavy load causes massive arc explosions.",
                },
            ],
            on_safe=lambda: self._scram_answered(item),
            wrong_msg="ARC EXPLOSION! Never cut power under load. Dampen the phases gradually.",
            penalty=15,
        )

    def _scram_answered(self, item):
        self._scram_ok = True
        self._scram_game(item)

    def _scram_game(self, item):
        self.start_minigame(
            TimingMeter(
                "PHASE DAMPENING", "",
                steps=[
                    "Insert the MASTER KEYCARD",
                    "Dampen coil A",
                    "Dampen coil B",
                    "Dampen coil C",
                ],
                speed=1.05, zone=0.22, max_misses=3,
                icon="generator", win_text="CORE SCRAMMED!",
            ),
            on_win=lambda: self._scram_success(item),
            on_fail=lambda: self.hurt("The coils are still humming! Re-enter the sequence.", penalty=10),
        )

    def _scram_success(self, item=None):
        if self._scram_done:
            return
        if item and isinstance(item, dict):
            item["done"] = True
        self._scram_done = True
        self._core_scrammed = True
        self.stop_countdown()
        self.clear_meter("resonance")
        self._final_pending = False
        self.start_dialogue("Dr. Elias Voss", [
            "The harmonic... it's collapsing. The faultline is settling.",
            "I wanted to control nature. I should have listened to it.",
            "Thank you. Now go and tell everyone what really happened.",
        ])
        # Finish the mission now, but the shared base keeps the lesson card
        # hidden until Voss's closing dialogue has been read.
        self._sync_steps()
        self.complete_objective(3)

    # ------------------------------------------------------------------
    # Ending hand-off (unchanged)
    # ------------------------------------------------------------------
    def proceed_to_next(self):
        """Transition directly to the canonical ending based on ScoreSystem."""
        from src.story.chapter_registry import launch_ending
        session = getattr(self.game, "session", None)
        if session is not None:
            try:
                session.complete_stage("final_mission")
            except Exception as exc:  # never block the ending on a score write
                print(f"[BayanSafe] Could not record final mission: {exc}")
        launch_ending(self.game, self.score_system)