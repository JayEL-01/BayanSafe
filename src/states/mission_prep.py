import pygame

from src.core import audio
from src.states.base_state import BaseState
from src.states.loading import LoadingScreen
from src.states.big_map import BigMap
from src.ui import theme
from src.entities.reference_art import player_sprite, sprite
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text


PLANS = [
    ("first_aid", "AID KIT", "+20 starting health", (232, 118, 104)),
    ("route_plan", "ROUTE MAP", "More time before danger rises", (124, 178, 204)),
    ("community_radio", "RADIO PLAN", "+100 community-care points", (140, 196, 132)),
]
PACES = ["relaxed", "standard", "challenge"]
PACE_COPY = {
    "relaxed": "More preparation time and extra health",
    "standard": "The planned mission balance",
    "challenge": "Hazards build faster; plan carefully",
}


class MissionPrep(BaseState):
    """Set a single community plan and pace for the continuous story journey."""

    def __init__(self, game, stage_id):
        super().__init__(game)
        self.stage_id = stage_id
        self.stage = load_json(f"data/stages/{stage_id}.json")
        self.opening = load_json("data/chapter_openers.json").get(stage_id, {})
        selected_character = game.session.character
        character_id = (selected_character.get("id", "juan")
                        if isinstance(selected_character, dict) else selected_character or "juan")
        self.player_art = player_sprite(character_id)
        self.plan_index = next(
            (i for i, plan in enumerate(PLANS) if plan[0] == game.session.prep_choice), 1
        )
        self.pace_index = PACES.index(game.session.difficulty)
        self.card_rects = [pygame.Rect(8 + i * 102, 54, 98, 62) for i in range(3)]
        self.pace_rect = pygame.Rect(18, 127, 284, 23)
        self.start_rect = pygame.Rect(112, 160, 96, 18)

    def start_mission(self):
        self.game.session.prep_choice = PLANS[self.plan_index][0]
        self.game.session.difficulty = PACES[self.pace_index]
        self.game.session.save()
        from src.states.chapter_intro import ChapterIntro
        next_state = (lambda: ChapterIntro(self.game, self.stage_id)
                      if self.has_chapter_opener(self.stage_id)
                      else BigMap(self.game, self.stage_id))
        self.game.state_manager.change(LoadingScreen(
            self.game, next_state,
            f"LOADING {self.stage['name'].upper()}",
        ))

    @staticmethod
    def has_chapter_opener(stage_id):
        return stage_id in load_json("data/chapter_openers.json")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.state_manager.pop()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.plan_index = (self.plan_index - 1) % len(PLANS)
                audio.play("tick")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.plan_index = (self.plan_index + 1) % len(PLANS)
                audio.play("tick")
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.pace_index = (self.pace_index - 1) % len(PACES)
                audio.play("tick")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.pace_index = (self.pace_index + 1) % len(PACES)
                audio.play("tick")
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.plan_index = event.key - pygame.K_1
                audio.play("tick")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                audio.play("confirm")
                self.start_mission()
        elif event.type == pygame.MOUSEMOTION:
            pos = self.game.to_canvas_pos(event.pos)
            for index, rect in enumerate(self.card_rects):
                if rect.collidepoint(pos):
                    self.plan_index = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.game.to_canvas_pos(event.pos)
            for index, rect in enumerate(self.card_rects):
                if rect.collidepoint(pos):
                    self.plan_index = index
                    return
            if self.pace_rect.collidepoint(pos):
                self.pace_index = (self.pace_index + 1) % len(PACES)
            elif self.start_rect.collidepoint(pos):
                self.start_mission()

    def draw(self, surface):
        surface.fill((28, 36, 49))
        # This is a short, story-led briefing before the prep choices. It uses
        # the authored chapter scene line and player sprite, never a narrator.
        theme.draw_panel(surface, pygame.Rect(8, 4, 304, 44), accent=theme.SKY, alpha=245)
        if self.player_art:
            art = pygame.transform.scale(self.player_art, (16, 24))
            surface.blit(art, (14, 12))
        place = self.opening.get("place", self.stage.get("chapter", "BAYANSAFE"))
        theme.draw_text(surface, self.stage["name"], (38, 8), "tiny", theme.HONEY)
        theme.draw_text(surface, place, (38, 21), "tiny", theme.CREAM_DIM)
        scene_line = self.opening.get("scene", "Choose a community plan before setting out.")
        theme.draw_text(surface, scene_line, (160, 39), "tiny", theme.CREAM,
                        anchor="midbottom")

        for index, ((key, title, description, color), rect) in enumerate(zip(PLANS, self.card_rects)):
            selected = index == self.plan_index
            theme.draw_panel(surface, rect, accent=color if selected else theme.CREAM_DIM,
                             alpha=245 if selected else 210)
            icon_name = {"first_aid": "first_aid", "route_plan": "map",
                         "community_radio": "radio"}[key]
            icon = sprite("items", icon_name)
            if icon:
                icon = pygame.transform.scale(icon, (16, 16))
                surface.blit(icon, (rect.x + 6, rect.y + 7))
            else:
                pygame.draw.rect(surface, color, (rect.x + 8, rect.y + 9, 10, 10))
            theme.draw_text(surface, f"{index + 1}. {title}", (rect.x + 25, rect.y + 9),
                            "tiny", theme.CREAM if selected else theme.CREAM_DIM)
            for line_index, line in enumerate(wrap_text(description, theme.get_font("tiny"), 82)[:3]):
                theme.draw_text(surface, line, (rect.x + 7, rect.y + 32 + line_index * 9),
                                "tiny", theme.CREAM_DIM)

        theme.draw_text(surface, "1-3 PLAN    UP / DOWN PACE    ENTER START",
                        (160, 121), "tiny", theme.CREAM_DIM, anchor="center")
        pace = PACES[self.pace_index]
        pace_color = {"relaxed": theme.SAGE, "standard": theme.SKY,
                      "challenge": theme.CORAL}[pace]
        theme.draw_panel(surface, self.pace_rect, title=f"PLAY PACE: {pace.upper()}  (UP / DOWN)",
                         accent=pace_color, alpha=230)
        theme.draw_text(surface, PACE_COPY[pace], (160, 154), "tiny", theme.CREAM,
                        anchor="center")

        theme.draw_button(surface, self.start_rect, "BEGIN JOURNEY", selected=True, font="tiny")
