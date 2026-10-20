"""Opening story map built from the player's supplied island route reference."""
import pygame

from src.core import settings
from src.states.base_state import BaseState
from src.states.mission_prep import MissionPrep
from src.ui import theme
from src.utils.data_loader import BASE_DIR, load_json


class WorldMap(BaseState):
    """Show the island's full route once, then begin the continuous campaign."""

    FOOTER_TOP = 130
    FOOTER_HEIGHT = settings.INTERNAL_HEIGHT - FOOTER_TOP

    def __init__(self, game):
        super().__init__(game)
        self.data = load_json("data/world_map.json")
        self.pages = []
        for entry in self.data.get("pages", []):
            try:
                loaded = pygame.image.load(str(BASE_DIR / entry["image"])).convert()
                width, height = loaded.get_size()
                # Preserve the map's full-size detail; the opaque footer covers its
                # lower edge instead of shrinking every label across the island.
                scale = min(settings.INTERNAL_WIDTH / width,
                            settings.INTERNAL_HEIGHT / height)
                size = (max(1, round(width * scale)), max(1, round(height * scale)))
                self.pages.append((pygame.transform.smoothscale(loaded, size), entry["title"]))
            except (pygame.error, OSError, KeyError):
                continue
        self.page = 0
        self.pulse = 0.0
        self.begin_rect = pygame.Rect(92, 147, 136, 18)

    def change_page(self, step):
        if self.pages:
            self.page = (self.page + step) % len(self.pages)

    def begin_journey(self):
        stage_id = self.game.session.current_stage
        self.game.state_manager.change(MissionPrep(self.game, stage_id))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.begin_journey()
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_PAGEDOWN):
                self.change_page(1)
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_PAGEUP):
                self.change_page(-1)
            elif event.key == pygame.K_ESCAPE:
                self.game.state_manager.pop()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            if self.begin_rect.collidepoint(pos):
                self.begin_journey()
            elif pos[1] >= self.FOOTER_TOP and pos[0] < 32:
                self.change_page(-1)
            elif pos[1] >= self.FOOTER_TOP and pos[0] >= settings.INTERNAL_WIDTH - 32:
                self.change_page(1)

    def update(self, dt):
        self.pulse += dt

    def draw(self, surface):
        if self.pages:
            surface.fill((228, 211, 173))
            image, title = self.pages[self.page]
            surface.blit(image, ((settings.INTERNAL_WIDTH - image.get_width()) // 2,
                                 (settings.INTERNAL_HEIGHT - image.get_height()) // 2))
        else:
            surface.fill((43, 80, 75))

        # The full reference is split into readable route, region, and hazard
        # pages; it is not replaced by a separate selectable-mission map.
        rail = pygame.Surface((settings.INTERNAL_WIDTH, self.FOOTER_HEIGHT), pygame.SRCALPHA)
        rail.fill((17, 27, 39, 245))
        surface.blit(rail, (0, self.FOOTER_TOP))
        pygame.draw.line(surface, theme.HONEY, (0, self.FOOTER_TOP),
                         (settings.INTERNAL_WIDTH, self.FOOTER_TOP), 1)
        page_title = self.pages[self.page][1] if self.pages else "ISLAND STORY MAP"
        theme.draw_text(surface, f"PAGE {self.page + 1} OF {max(1, len(self.pages))}  ·  {page_title}",
                        (160, 132), "tiny", theme.CREAM, anchor="midtop")
        selected = int(self.pulse * 2) % 2 == 0
        theme.draw_button(surface, self.begin_rect, "BEGIN THE JOURNEY", selected=selected,
                          font="tiny")
        theme.draw_text(surface, "LEFT / RIGHT: CHANGE PAGE  ·  ENTER: START",
                        (160, 172), "tiny", theme.CREAM_DIM, anchor="center")
