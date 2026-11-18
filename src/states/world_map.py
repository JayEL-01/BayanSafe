"""Interactive story-progression world map for BayanSafe.

The player's island painting (``assets/images/world/worldmap.png``) is the
map. Story locations are configured in ``data/world_map.json`` and pinned
onto the art at config-driven normalized positions that follow the island's
geography. Each location renders in one of three live-computed states:

* ``locked``    - veiled in grey with a padlock; clicking does nothing
* ``active``    - pulsing warm glow plus a "CURRENTLY EXPLORING" tag
* ``completed`` - original colors with a checkmark, replayable

States are always derived from the game session (merged with the logged-in
player's database progress on entry) - never hardcoded in the UI.
"""
import math

import pygame

from src.core import settings
from src.core.audio import play
from src.core.database import db_manager
from src.states.base_state import BaseState
from src.ui import theme
from src.utils.data_loader import BASE_DIR, load_json
from src.utils.helpers import wrap_text

# Progression states (computed from the session for every draw).
COMPLETED = "completed"
ACTIVE = "active"
READY = "ready"      # unlocked but not the current frontier
LOCKED = "locked"

LOCKED_HINT = ("A sealed region of the island. Secure the region you are "
               "exploring to chart a path here.")


class WorldMap(BaseState):
    """Island map that tracks and drives the canonical story progression."""

    PANEL_TOP = 133            # compact info rail below the map
    HIT_RADIUS = 7             # mouse hit radius around each pin
    VEIL_RADIUS = 14           # grey shroud drawn over locked regions
    FLASH_TIME = 2.0

    # pin head fill / border per state
    PIN_COLORS = {
        COMPLETED: (theme.SAGE, (40, 88, 52)),
        ACTIVE: (theme.HONEY, (146, 96, 22)),
        READY: (theme.WOOD_LIGHT, (92, 60, 36)),
        LOCKED: ((118, 112, 104), (66, 62, 58)),
    }

    LABEL_COLORS = {
        COMPLETED: theme.SAGE,
        ACTIVE: theme.HONEY,
        READY: theme.CREAM,
        LOCKED: (150, 142, 132),
    }

    def __init__(self, game):
        super().__init__(game)
        self.data = load_json("data/world_map.json")
        self.title = str(self.data.get("title", "ISLAND STORY MAP"))
        self.locations = [
            {
                "stage_id": str(entry["stage_id"]),
                "name": str(entry.get("name", entry["stage_id"])),
                "label": str(entry.get("label", "")),
                "description": str(entry.get("description", "")),
                "x": float(entry.get("x", 0.5)),
                "y": float(entry.get("y", 0.5)),
                "label_dx": int(entry.get("label_dx", 0)),
                "label_dy": int(entry.get("label_dy", 9)),
            }
            for entry in self.data.get("locations", [])
        ]

        self.background = None
        self.map_rect = pygame.Rect(0, 0, settings.INTERNAL_WIDTH, self.PANEL_TOP)
        self._load_background()

        self.pulse = 0.0
        self.selected = 0        # keyboard focus
        self.hover = None        # marker under the mouse (info display only)
        self.flash_message = ""
        self.flash_timer = 0.0

        self._sync_progress_from_database()
        # focus wherever the story currently stands
        self.selected = self.active_index()

    # ------------------------------------------------------------- setup
    def _load_background(self):
        """Aspect-fit the player's island painting above the info rail."""
        try:
            image = pygame.image.load(
                str(BASE_DIR / str(self.data.get("background_image", "")))
            )
        except (pygame.error, OSError, ValueError):
            return
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            image = image.convert()
        width, height = image.get_size()
        area = pygame.Rect(0, 0, settings.INTERNAL_WIDTH, self.PANEL_TOP - 2)
        scale = min(area.width / width, area.height / height)
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        self.background = pygame.transform.smoothscale(image, size)
        self.map_rect = self.background.get_rect(center=area.center)

    # -------------------------------------------------------- progression
    def session(self):
        return getattr(self.game, "session", None)

    def _norm(self, stage_id):
        session = self.session()
        if session is None:
            return stage_id
        return session.STAGE_ALIASES.get(stage_id, stage_id)

    def active_index(self):
        """Index of the first story location not yet completed."""
        session = self.session()
        if session is None:
            return 0
        for i, loc in enumerate(self.locations):
            if self._norm(loc["stage_id"]) not in session.completed:
                return i
        return max(0, len(self.locations) - 1)

    def stage_state(self, index):
        """Live state (locked/ready/active/completed) of a location."""
        session = self.session()
        if session is None or not (0 <= index < len(self.locations)):
            return LOCKED
        stage_id = self._norm(self.locations[index]["stage_id"])
        if stage_id in session.completed:
            return COMPLETED
        if index == self.active_index():
            return ACTIVE
        if session.is_unlocked(stage_id):
            return READY
        return LOCKED

    def _sync_progress_from_database(self):
        """Merge the logged-in player's database progression into the session.

        Uses the existing ``player_stage_progress`` tables through
        ``db_manager`` - no second progression system is introduced. Only
        canonical story stages are merged, and merging only ever ADDS
        progress (it never removes local progress).
        """
        session = self.session()
        if session is None or not db_manager.is_connected:
            return
        player_id = getattr(session, "db_player_id", None)
        if not player_id:
            player_id = session._ensure_db_player()
            if not player_id:
                return
        progress = db_manager.load_player_progress(int(player_id))
        if not progress:
            return
        changed = False

        db_completed = {
            session.STAGE_ALIASES.get(s, s) for s in (progress.get("completed") or ())
        }
        db_unlocked = {
            session.STAGE_ALIASES.get(s, s) for s in (progress.get("unlocked") or ())
        }

        # Validate that completed stages form a contiguous chain starting from prologue.
        # Story progression in BayanSafe is strictly linear: an isolated later chapter
        # (e.g. from an ad-hoc test or corrupted row) must never be marked completed
        # if its predecessor was never finished.
        for norm in session.STAGE_ORDER:
            if norm in db_completed or norm in session.completed:
                if norm not in session.completed:
                    session.completed.add(norm)
                    changed = True
                idx = session.STAGE_ORDER.index(norm)
                if idx + 1 < len(session.STAGE_ORDER):
                    session.unlocked.add(session.STAGE_ORDER[idx + 1])
            else:
                # Stop: no subsequent chapter can be completed without its predecessor
                break

        for stage in db_unlocked:
            if stage in session.STAGE_ORDER and stage not in session.unlocked:
                idx = session.STAGE_ORDER.index(stage)
                if idx == 0 or session.STAGE_ORDER[idx - 1] in session.completed:
                    session.unlocked.add(stage)
                    changed = True
        if changed:
            session.save()

    # --------------------------------------------------------- geometry
    def marker_pos(self, index):
        """Canvas position of a location pin (normalized coordinates map onto
        the blitted image rect, so pins track the art at any scale)."""
        if not (0 <= index < len(self.locations)):
            return (0, 0)
        loc = self.locations[index]
        return (self.map_rect.x + round(loc["x"] * self.map_rect.w),
                self.map_rect.y + round(loc["y"] * self.map_rect.h))

    def location_at(self, pos):
        for i in range(len(self.locations)):
            mx, my = self.marker_pos(i)
            if (pos[0] - mx) ** 2 + (pos[1] - my) ** 2 <= self.HIT_RADIUS ** 2:
                return i
        return None

    def display_index(self):
        """Which location the info panel is talking about right now."""
        if self.hover is not None and 0 <= self.hover < len(self.locations):
            return self.hover
        return min(max(self.selected, 0), max(0, len(self.locations) - 1))

    # -------------------------------------------------------- interaction
    def select(self, index, sound=True):
        if 0 <= index < len(self.locations) and index != self.selected:
            self.selected = index
            self.hover = None
            if sound:
                play("tick")

    def travel_to(self, index):
        """React to a click or ENTER on a location."""
        if not (0 <= index < len(self.locations)):
            return
        state = self.stage_state(index)
        if state == LOCKED:
            self.select(index, sound=False)
            self.flash_message = "LOCKED: SECURE THE REGION YOU ARE EXPLORING FIRST"
            self.flash_timer = self.FLASH_TIME
            play("back")
            return
        if state == COMPLETED and self.selected != index:
            # first click on a finished region only focuses it; replaying
            # needs a deliberate second click
            self.select(index)
            return
        self.begin_journey(self.locations[index]["stage_id"])

    def begin_journey(self, stage_id=None):
        """Load the first level of the given (unlocked) story stage."""
        session = self.session()
        if stage_id is None:
            index = self.active_index()
            stage_id = self.locations[index]["stage_id"] if self.locations else "prologue"
        stage_id = self._norm(stage_id)
        play("confirm")
        from src.states.chapter import ChapterState
        from src.states.loading import LoadingScreen
        from src.story.chapter_registry import load_level
        chapter_id, level_id = ChapterState.DEFAULT_LEVELS.get(
            stage_id, ("prologue", "tutorial"))
        name = next((loc["name"] for loc in self.locations
                     if self._norm(loc["stage_id"]) == stage_id), stage_id)
        self.game.state_manager.change(LoadingScreen(
            self.game,
            lambda: load_level(self.game, chapter_id, level_id),
            f"TRAVELING TO {name}",
        ))

    def leave(self):
        """Back out of the map: to the screen below, or the main menu."""
        play("back")
        manager = self.game.state_manager
        if len(getattr(manager, "stack", [])) > 1:
            manager.pop()
        else:
            from src.states.main_menu import MainMenu
            manager.change(MainMenu(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e,
                             pygame.K_KP_ENTER):
                self.travel_to(self.display_index())
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_PAGEDOWN):
                self.select((self.selected + 1) % max(1, len(self.locations)))
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_PAGEUP):
                self.select((self.selected - 1) % max(1, len(self.locations)))
            elif event.key == pygame.K_ESCAPE:
                self.leave()
        elif event.type == pygame.MOUSEMOTION:
            self.hover = self.location_at(self.game.to_canvas_pos(event.pos))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self.location_at(self.game.to_canvas_pos(event.pos))
            if index is not None:
                self.travel_to(index)

    def update(self, dt):
        self.pulse += dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

    # ------------------------------------------------------------ drawing
    def draw(self, surface):
        theme.draw_background(surface)          # warm wooden desk
        if self.background is not None:
            pygame.draw.rect(surface, theme.SHADOW, self.map_rect.move(2, 3))
            surface.blit(self.background, self.map_rect.topleft)
            pygame.draw.rect(surface, theme.WOOD_FRAME, self.map_rect, 1)
        else:
            surface.fill((46, 84, 102), self.map_rect)   # calm ocean fallback
            pygame.draw.rect(surface, theme.WOOD_FRAME, self.map_rect, 1)

        self._draw_route(surface)
        for i in range(len(self.locations)):     # veils under everything
            if self.stage_state(i) == LOCKED:
                self._draw_veil(surface, self.marker_pos(i))
        for i in range(len(self.locations)):     # pins
            self._draw_pin(surface, i)
        for i in range(len(self.locations)):     # labels over pins
            self._draw_label(surface, i)
        self._draw_title_chip(surface)
        self._draw_active_marker(surface)
        self._draw_info_panel(surface)

    # - - - - - - - - - - - - - - - - - - - - - - - - route and markers
    def _draw_route(self, surface):
        """Dashed journey path in story order; warm behind the frontier,
        grey beyond it."""
        if len(self.locations) < 2:
            return
        active = self.active_index()
        for i in range(len(self.locations) - 1):
            start, end = self.marker_pos(i), self.marker_pos(i + 1)
            if i + 1 <= active:
                color = theme.mix(theme.HONEY, theme.CREAM_DIM, 0.3)
            else:
                color = (108, 101, 94)
            self._draw_dashed_line(surface, start, end, color)

    def _draw_dashed_line(self, surface, start, end, color):
        x0, y0 = start
        x1, y1 = end
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 4:
            return
        cells = max(1, int(length // 4))
        for i in range(cells):
            t0 = i / cells
            t1 = min(1.0, (i + 0.55) / cells)
            p0 = (round(x0 + (x1 - x0) * t0), round(y0 + (y1 - y0) * t0))
            p1 = (round(x0 + (x1 - x0) * t1), round(y0 + (y1 - y0) * t1))
            pygame.draw.line(surface, color, p0, p1, 1)

    def _draw_veil(self, surface, pos):
        """Soft dark shroud that greys out a locked region of the art."""
        r = self.VEIL_RADIUS
        veil = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(veil, (24, 22, 26, 112), (r + 1, r + 1), r)
        surface.blit(veil, (pos[0] - r - 1, pos[1] - r - 1))

    def _draw_pin(self, surface, index):
        pos = self.marker_pos(index)
        state = self.stage_state(index)
        fill, border = self.PIN_COLORS[state]
        x, y = pos
        head = (x, y - 4)
        if index == self.display_index():       # focus ring (hover/keyboard)
            ring = theme.CREAM if state != LOCKED else theme.CREAM_DIM
            pygame.draw.circle(surface, ring, head, 6, 1)
        pygame.draw.polygon(surface, border, [(x - 2, y), (x + 2, y), (x, y + 3)])
        pygame.draw.circle(surface, border, head, 5)
        pygame.draw.circle(surface, fill, head, 4)
        if state == COMPLETED:                  # small cream checkmark
            pygame.draw.line(surface, theme.CREAM, (x - 2, y - 4), (x - 1, y - 3))
            pygame.draw.line(surface, theme.CREAM, (x - 1, y - 3), (x + 2, y - 6))
        elif state == ACTIVE:                   # bright core for the glow
            pygame.draw.circle(surface, (255, 252, 240), head, 1)
        elif state == LOCKED:                   # padlock beside the pin
            self._draw_padlock(surface, x + 6, y - 6)

    @staticmethod
    def _draw_padlock(surface, x, y):
        dark = (58, 54, 50)
        pygame.draw.rect(surface, dark, (x, y + 1, 5, 4))          # body
        pygame.draw.rect(surface, dark, (x + 1, y - 2, 3, 3), 1)  # shackle
        surface.set_at((x + 2, y + 3), theme.CREAM_DIM)            # keyhole

    def _draw_label(self, surface, index):
        state = self.stage_state(index)
        if state == ACTIVE:
            return          # the animated tag replaces the static label
        loc = self.locations[index]
        x, y = self.marker_pos(index)
        theme.draw_text(surface, loc["label"],
                        (x + loc["label_dx"], y + loc["label_dy"]),
                        "tiny", self.LABEL_COLORS[state], anchor="midtop")

    def _draw_active_marker(self, surface):
        """Pulsing warm glow + 'CURRENTLY EXPLORING' tag on the frontier."""
        index = self.active_index()
        if not (0 <= index < len(self.locations)) or self.stage_state(index) != ACTIVE:
            return
        x, y = self.marker_pos(index)

        # breathing glow ring (drawn behind the pin's bright core)
        t = (self.pulse * 0.8) % 1.0          # ~1.25 s cycle
        radius = 6 + int(t * 9)               # 6 -> 15 px
        alpha = max(0, int(150 * (1.0 - t)))
        size = 36
        glow = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(glow, (*theme.HONEY, alpha // 3), center, radius)
        pygame.draw.circle(glow, (*theme.HONEY, alpha), center,
                           max(2, radius - 2), 2)
        surface.blit(glow, (x - size // 2, y - size // 2 - 4))

        # floating status tag
        bob = round(math.sin(self.pulse * 3.0) * 1.0)
        font = theme.get_font("tiny")
        width = font.size("CURRENTLY EXPLORING")[0] + 6
        if y >= 24:                            # below the pin by default
            tag_y = y + 4 + 9 + bob
        else:                                  # near the top edge: above
            tag_y = y - 18 - bob
        rect = pygame.Rect(0, 0, width, font.get_height() + 1)
        rect.midtop = (x, tag_y)
        rect.clamp_ip(surface.get_rect())
        chip = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        chip.fill((*theme.WOOD_DARK, 200))
        surface.blit(chip, rect.topleft)
        pygame.draw.rect(surface, theme.HONEY, rect, 1)
        theme.draw_text(surface, "CURRENTLY EXPLORING", (rect.x + 3, rect.y + 1),
                        "tiny", theme.HONEY, shadow=False)

    def _draw_title_chip(self, surface):
        font = theme.get_font("tiny")
        width = font.size(self.title)[0] + 6
        height = font.get_height() + 1
        chip = pygame.Surface((width, height), pygame.SRCALPHA)
        chip.fill((*theme.WOOD_DARK, 170))
        surface.blit(chip, (4, 3))
        pygame.draw.rect(surface, theme.WOOD_BORDER, (4, 3, width, height), 1)
        theme.draw_text(surface, self.title, (7, 4), "tiny",
                        theme.CREAM_DIM, shadow=False)

    # ------------------------------------------------------- info panel
    def _draw_info_panel(self, surface):
        panel = pygame.Rect(2, self.PANEL_TOP,
                           settings.INTERNAL_WIDTH - 4,
                           settings.INTERNAL_HEIGHT - self.PANEL_TOP - 2)
        theme.draw_panel(surface, panel, accent=theme.HONEY)
        if not self.locations:
            return
        index = self.display_index()
        loc = self.locations[index]
        state = self.stage_state(index)
        left = panel.x + 8
        right = panel.right - 8

        # name + status chip
        theme.draw_text(surface, loc["name"], (left, panel.y + 3),
                        "small", theme.HONEY)
        status, status_color = self._status_text(state)
        theme.draw_text(surface, status, (right, panel.y + 4), "tiny",
                        status_color, anchor="topright")

        # description (or the locked flash message)
        if self.flash_timer > 0:
            theme.draw_text(surface, self.flash_message,
                            (left, panel.y + 15), "tiny", theme.CORAL)
        else:
            desc = loc["description"] if state != LOCKED else LOCKED_HINT
            font = theme.get_font("tiny")
            for i, line in enumerate(wrap_text(desc, font, panel.w - 16)[:2]):
                theme.draw_text(surface, line, (left, panel.y + 15 + i * 9),
                                "tiny", theme.CREAM_DIM)

        # footer: overall progress + contextual hint
        secured = sum(1 for i in range(len(self.locations))
                      if self.stage_state(i) == COMPLETED)
        theme.draw_text(surface, f"REGIONS SECURED: {secured}/{len(self.locations)}",
                        (left, panel.y + 34), "tiny", theme.SAGE)
        theme.draw_text(surface, self._hint_text(state), (right, panel.y + 34),
                        "tiny", theme.CREAM_DIM, anchor="topright")

    def _status_text(self, state):
        if state == ACTIVE:
            return "CURRENTLY EXPLORING", theme.HONEY
        if state == COMPLETED:
            if all(self.stage_state(i) == COMPLETED
                   for i in range(len(self.locations))):
                return "STORY COMPLETE", theme.SAGE
            return "COMPLETED", theme.SAGE
        if state == READY:
            return "UNLOCKED", theme.CREAM
        return "LOCKED", theme.CREAM_DIM

    @staticmethod
    def _hint_text(state):
        if state == ACTIVE:
            return "ENTER / CLICK: CONTINUE EXPLORING"
        if state == COMPLETED:
            return "ENTER / CLICK AGAIN: REPLAY REGION"
        if state == READY:
            return "ENTER / CLICK: EXPLORE REGION"
        return "COMPLETE THE ACTIVE REGION TO UNLOCK"
