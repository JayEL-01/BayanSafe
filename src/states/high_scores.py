import pygame

from src.core.session import GameSession
from src.states.base_state import BaseState
from src.ui import theme
from src.core.save_data import load_save
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text


class HighScores(BaseState):
    """Local single-player leaderboard comparing the best run per hero."""

    def __init__(self, game):
        super().__init__(game)
        self.stages = GameSession.STAGE_ORDER
        self.stage_index = 0
        self.stage_data = None
        self.filters = [("ALL DISASTERS", None)]
        hazard_labels = {
            "earthquake": "QUAKE", "flash_fire": "FIRE", "wildfire": "FIRE",
            "landslide": "SLIDE", "typhoon": "TYPHOON", "volcano": "VOLCANO",
            "tsunami": "TSUNAMI", "flood": "FLOOD",
        }
        self.filter_index = 0
        self.stage_indexes = []
        for stage_id in self.stages:
            data = load_json(f"data/stages/{stage_id}.json")
            hazards = tuple(sorted(set(data.get("hazards", {}).get("disasters", []))))
            if hazards and hazards not in [entry[1] for entry in self.filters]:
                label = (f"ALL {len(hazards)} HAZARDS" if len(hazards) > 5 else
                         " + ".join(hazard_labels.get(hazard, hazard.upper()) for hazard in hazards))
                self.filters.append((label, hazards))
        saved = load_save()
        if saved and isinstance(saved.get("high_scores"), dict):
            self.game.session.high_scores = saved["high_scores"]
        self.refresh_stage()

    def refresh_stage(self):
        hazards = self.filters[self.filter_index][1]
        matches = []
        for index, stage_id in enumerate(self.stages):
            data = load_json(f"data/stages/{stage_id}.json")
            stage_hazards = tuple(sorted(set(data.get("hazards", {}).get("disasters", []))))
            if hazards is None or stage_hazards == hazards:
                matches.append(index)
        self.stage_indexes = matches or [0]
        self.stage_index %= len(self.stage_indexes)
        self.selected_stage_index = self.stage_indexes[self.stage_index]
        self.stage_data = load_json(f"data/stages/{self.stages[self.selected_stage_index]}.json")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_SPACE):
                self.game.state_manager.pop()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.stage_index = (self.stage_index - 1) % len(self.stage_indexes)
                self.refresh_stage()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.stage_index = (self.stage_index + 1) % len(self.stage_indexes)
                self.refresh_stage()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.filter_index = (self.filter_index - 1) % len(self.filters)
                self.stage_index = 0
                self.refresh_stage()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.filter_index = (self.filter_index + 1) % len(self.filters)
                self.stage_index = 0
                self.refresh_stage()

    def draw(self, surface):
        surface.fill((18, 31, 43))
        theme.draw_text(surface, "CHALLENGE SCORES", (160, 13), "heading",
                        theme.HONEY, anchor="midtop")
        theme.draw_text(surface, "BEST RESULT PER PLAYER ID · STORED ON THIS DEVICE",
                        (160, 39), "tiny", theme.CREAM_DIM, anchor="center")

        panel = pygame.Rect(14, 51, 292, 105)
        theme.draw_panel(surface, panel, title="LOCAL LEADERBOARD", alpha=248)
        filter_label = self.filters[self.filter_index][0]
        theme.draw_text(surface, f"FILTER {self.filter_index + 1}/{len(self.filters)} · {filter_label}",
                        (160, 66), "tiny", theme.HONEY, anchor="center")
        name_lines = wrap_text(self.stage_data["name"].upper(), theme.get_font("tiny"), 252)[:2]
        for index, line in enumerate(name_lines):
            theme.draw_text(surface, line, (160, 77 + index * 9), "tiny", theme.SKY,
                            anchor="center")
        mission_y = 77 + len(name_lines) * 9
        theme.draw_text(surface, f"STORY {self.selected_stage_index + 1}/22 · LEVEL {self.stage_index + 1}/{len(self.stage_indexes)}",
                        (160, mission_y), "tiny", theme.CREAM_DIM, anchor="center")
        entries = self.game.session.stage_high_scores(self.stages[self.selected_stage_index])
        shown = entries
        if not shown:
            theme.draw_text(surface, "No completed runs for this mission yet.",
                            (160, max(116, mission_y + 15)), "small", theme.CREAM, anchor="center")
        else:
            for rank, entry in enumerate(shown[:3]):
                y = max(99, mission_y + 11) + rank * 18
                rank_color = theme.HONEY if rank == 0 else theme.CREAM_DIM
                theme.draw_text(surface, f"{rank + 1}.", (42, y), "tiny", rank_color)
                player_id = entry.get("player_id", entry.get("character_id", "PLAYER"))
                theme.draw_text(surface, str(player_id).upper()[:14],
                                (68, y), "tiny", theme.CREAM)
                theme.draw_text(surface, f"{entry.get('score', 0):,} PTS",
                                (280, y), "tiny", theme.SAGE, anchor="topright")
                detail = (f"OBJECTIVES {entry.get('quests_done', 0)}/{entry.get('quests_total', 0)}"
                          f"   ATTEMPTS {entry.get('attempts', 1)}"
                          f"   BEST {int(entry.get('best_time', 0))}s")
                theme.draw_text(surface, detail, (68, y + 9), "tiny", theme.CREAM_DIM)

        theme.draw_text(surface, "UP/DOWN FILTER · LEFT/RIGHT MISSION · ENTER BACK",
                        (160, 160), "tiny", theme.CREAM_DIM, anchor="center")
