from pathlib import Path
import pygame

from src.core.session import GameSession
from src.states.base_state import BaseState
from src.ui import theme
from src.core.save_data import load_save
from src.core.database import db_manager
from src.utils.data_loader import BASE_DIR, load_json
from src.utils.helpers import wrap_text


class HighScores(BaseState):
    """Local single-player leaderboard comparing the best run per hero."""

    def __init__(self, game):
        super().__init__(game)
        self.stages = GameSession.STAGE_ORDER
        self.stage_index = 0
        self.stage_data = None
        self.source = "local"

        saved = load_save()
        if saved and isinstance(saved.get("high_scores"), dict):
            self.game.session.high_scores = saved["high_scores"]
        self.refresh_stage()

    def refresh_stage(self):
        self.stage_index %= max(1, len(self.stages))
        stage_id = self.stages[self.stage_index]
        path = BASE_DIR / "data" / "story" / f"{stage_id}.json"
        if path.exists():
            self.stage_data = load_json(f"data/story/{stage_id}.json")
        else:
            self.stage_data = {"id": stage_id, "title": stage_id.replace("_", " ").title()}

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_SPACE):
                self.game.state_manager.pop()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.stage_index = (self.stage_index - 1) % len(self.stages)
                self.refresh_stage()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.stage_index = (self.stage_index + 1) % len(self.stages)
                self.refresh_stage()
            elif event.key == pygame.K_TAB:
                self.source = "database" if self.source == "local" else "local"

    def draw(self, surface):
        theme.draw_background(surface)
        theme.draw_text(surface, "CHALLENGE SCORES", (160, 13), "heading",
                        theme.HONEY, anchor="midtop")
        source_label = "LOCAL DEVICE" if self.source == "local" else "DATABASE (ONLINE)"
        theme.draw_text(surface, f"BEST RESULT PER PLAYER ID · STORED ON {source_label} · TAB TO SWITCH",
                        (160, 39), "tiny", theme.CREAM_DIM, anchor="center")

        panel = pygame.Rect(14, 51, 292, 105)
        theme.draw_panel(surface, panel, title="LEADERBOARD", alpha=248)

        stage_title = self.stage_data.get("title", self.stage_data.get("name", self.stages[self.stage_index])).upper()
        name_lines = wrap_text(stage_title, theme.get_font("tiny"), 252)[:2]
        for index, line in enumerate(name_lines):
            theme.draw_text(surface, line, (160, 68 + index * 9), "tiny", theme.SKY, anchor="center")

        mission_y = 68 + len(name_lines) * 9
        theme.draw_text(surface, f"CHAPTER {self.stage_index + 1}/{len(self.stages)}",
                        (160, mission_y), "tiny", theme.CREAM_DIM, anchor="center")

        stage_id = self.stages[self.stage_index]
        if self.source == "database" and db_manager.is_connected:
            entries = db_manager.get_high_scores(stage_id, limit=10)
            shown = [{"score": e["score"], "attempts": 1, "best_time": e.get("time", 0), "player_id": e["username"]} for e in entries]
        else:
            entries = self.game.session.stage_high_scores(stage_id)
            shown = list(entries)

        if not shown:
            theme.draw_text(surface, f"No completed runs for this chapter yet ({source_label.lower()}).",
                            (160, max(116, mission_y + 15)), "small", theme.CREAM, anchor="center")
        else:
            for rank, entry in enumerate(shown[:3]):
                y = max(99, mission_y + 11) + rank * 18
                rank_color = theme.HONEY if rank == 0 else theme.CREAM_DIM
                theme.draw_text(surface, f"{rank + 1}.", (42, y), "tiny", rank_color)
                player_id = entry.get("player_id", entry.get("character_id", "PLAYER"))
                theme.draw_text(surface, str(player_id).upper()[:14], (68, y), "tiny", theme.CREAM)
                theme.draw_text(surface, f"{entry.get('score', 0):,} PTS", (280, y), "tiny", theme.SAGE, anchor="topright")
                detail = f"ATTEMPTS {entry.get('attempts', 1)}   BEST {int(entry.get('best_time') or 0)}s"
                theme.draw_text(surface, detail, (68, y + 9), "tiny", theme.CREAM_DIM)

        theme.draw_text(surface, "LEFT/RIGHT CHAPTER · TAB SOURCE · ENTER BACK",
                        (160, 160), "tiny", theme.CREAM_DIM, anchor="center")
