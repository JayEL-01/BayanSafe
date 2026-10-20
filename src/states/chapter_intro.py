"""Short in-world conversations shown as a new story chapter begins."""
import math

import pygame

from src.core import settings
from src.entities.npc import NPC
from src.states.base_state import BaseState
from src.states.loading import LoadingScreen
from src.states.big_map import BigMap
from src.ui import theme
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text
from src.world.scene_art import SceneArt


class _PortraitCamera:
    # Portraits remain screen-positioned, but use the same smaller character
    # scale as the world so they do not overpower the establishing backdrop.
    zoom = 0.72

    @staticmethod
    def apply(rect):
        return pygame.Rect(rect)


class ChapterIntro(BaseState):
    """Play a short, staged character scene before control returns to the player."""

    def __init__(self, game, stage_id):
        super().__init__(game)
        self.stage_id = stage_id
        self.opener = load_json("data/chapter_openers.json")[stage_id]
        self.scene_art = SceneArt(load_json(f"data/stages/{stage_id}.json"), stage_id)
        self.elapsed = 0.0
        self.beat = -1  # establishing moment, then one character at a time
        self.type_progress = 0.0
        self.confirm_rect = pygame.Rect(196, 151, 112, 20)
        self.portraits = []
        for index, person in enumerate(self.opener["dialogue"]):
            npc = NPC({
                "id": f"intro_{stage_id}_{index}",
                "name": person["speaker"],
                "pos": [0, 0],
                "color": person["color"],
                "dialogue": [person["line"]],
            })
            npc.time = 0.0
            self.portraits.append(npc)

    def begin_chapter(self):
        self.game.state_manager.change(LoadingScreen(
            self.game,
            lambda: BigMap(self.game, self.stage_id),
            f"ARRIVING AT {self.opener['place']}",
            duration=0.65,
        ))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.advance_scene()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (self.beat >= len(self.opener["dialogue"])
                    and self.confirm_rect.collidepoint(self.game.to_canvas_pos(event.pos))):
                self.begin_chapter()

    def advance_scene(self):
        if self.beat >= 0 and self.type_progress < len(self.current_text()):
            self.type_progress = len(self.current_text())
            return
        if self.beat < len(self.opener["dialogue"]):
            self.beat += 1
            self.type_progress = 0.0
            return
        self.begin_chapter()

    def current_text(self):
        if self.beat < 0:
            return self.opener["scene"]
        if self.beat < len(self.opener["dialogue"]):
            return self.opener["dialogue"][self.beat]["line"]
        return ""

    def update(self, dt):
        self.elapsed += dt
        for index, portrait in enumerate(self.portraits):
            portrait.time = self.elapsed + index * 0.7
            target_x = 76 if index == 0 else 244
            portrait.rect.center = (round(target_x + math.sin(self.elapsed * 1.7 + index) * 2),
                                    100 + round(math.sin(self.elapsed * 3.1 + index) * 2))
        if self.type_progress < len(self.current_text()):
            self.type_progress = min(len(self.current_text()), self.type_progress + dt * 34)

    def draw(self, surface):
        self.draw_backdrop(surface)
        theme.draw_text(surface, self.opener["chapter"], (160, 9), "small",
                        theme.HONEY, anchor="center")
        theme.draw_text(surface, self.opener["place"], (160, 25), "tiny",
                        theme.CREAM, anchor="center")

        # The camera settles into the scene as the two characters arrive.
        for index, portrait in enumerate(self.portraits):
            person = self.opener["dialogue"][index]
            tint = tuple(person["color"])
            x, y = portrait.rect.center
            pygame.draw.ellipse(surface, (12, 21, 25), (x - 18, y + 8, 36, 6))
            if index == self.beat:
                pygame.draw.circle(surface, tint, (x, y - 4), 19, 1)
            portrait.draw(surface, _PortraitCamera())

        box = pygame.Rect(10, 119, 300, 48)
        if self.beat < 0:
            speaker, accent = "STORY", theme.SKY
        elif self.beat >= len(self.opener["dialogue"]):
            speaker, accent = "CHAPTER READY", theme.SAGE
        else:
            speaker = self.opener["dialogue"][self.beat]["speaker"].upper()
            accent = tuple(self.opener["dialogue"][self.beat]["color"])
        theme.draw_panel(surface, box, accent=accent, alpha=250)
        theme.draw_text(surface, speaker, (18, 123), "tiny", theme.HONEY)
        text = self.current_text()
        visible = text[:int(self.type_progress)]
        lines = wrap_text(visible, theme.get_font("tiny"), 282)[:2]
        for index, line in enumerate(lines):
            theme.draw_text(surface, line, (18, 135 + index * 9), "tiny", theme.CREAM)

        if self.beat >= len(self.opener["dialogue"]):
            theme.draw_button(surface, self.confirm_rect, "BEGIN", selected=True, font="tiny")
            instruction = "ENTER THE CHAPTER  ·  ENTER"
        else:
            instruction = "ENTER / E  ·  NEXT LINE"
        theme.draw_text(surface, instruction, (160, 175), "tiny", theme.CREAM_DIM,
                        anchor="center")

    def draw_backdrop(self, surface):
        stage_camera = _IntroSceneCamera()
        self.scene_art.draw_ground(surface, stage_camera)
        self.scene_art.draw_details(surface, stage_camera)
        self.scene_art.draw_landmarks(surface, stage_camera)
        self.scene_art.draw_chapter_establishment(surface, stage_camera)
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((7, 14, 23, 38))
        surface.blit(shade, (0, 0))


class _IntroSceneCamera:
    """Fit the authored chapter location into the intro's small canvas."""

    def __init__(self):
        self.offset = pygame.Vector2(0, 0)
        self.zoom = 0.5
        self.viewport = pygame.Rect(0, 0, settings.INTERNAL_WIDTH,
                                    settings.INTERNAL_HEIGHT)

    def apply(self, rect):
        rect = pygame.Rect(rect)
        return pygame.Rect(round(rect.x * self.zoom), round(rect.y * self.zoom),
                           max(1, round(rect.w * self.zoom)),
                           max(1, round(rect.h * self.zoom)))
