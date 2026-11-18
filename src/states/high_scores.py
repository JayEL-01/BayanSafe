import pygame

from src.states.base_state import BaseState
from src.story.chapter_registry import CHAPTER_INFO, MISSION_INFO
from src.ui import theme
from src.core.save_data import load_save
from src.core.database import db_manager
from src.utils.helpers import wrap_text


class HighScores(BaseState):
    """Leaderboard comparing whole-chapter totals and individual missions."""

    VIEWS = {"chapters": CHAPTER_INFO, "missions": MISSION_INFO}

    def __init__(self, game):
        super().__init__(game)
        self.source = "local"
        self.view = "chapters"
        self.index = 0

        saved = load_save()
        if isinstance(saved, dict):
            self._merge_saved_boards(saved)
            self.game.session.backfill_chapter_records(saved.get("completed", []))

        # Open on the latest board that actually has a recorded result, so a
        # player who just finished a chapter immediately sees their total.
        self.index = self._last_recorded_index()

    def _merge_saved_boards(self, saved):
        """Show saved scores even when the player opens this before Continue."""
        session = self.game.session
        scores = session.high_scores if isinstance(session.high_scores, dict) else {}
        saved_scores = saved.get("high_scores")
        if isinstance(saved_scores, dict):
            for key, board in saved_scores.items():
                if isinstance(board, dict):
                    scores.setdefault(key, board)
        session.high_scores = scores

        for field in ("records", "campaign_results"):
            stored = getattr(session, field, {})
            if not isinstance(stored, dict):
                stored = {}
            incoming = saved.get(field)
            if isinstance(incoming, dict):
                for key, value in incoming.items():
                    if isinstance(value, dict):
                        stored.setdefault(key, value)
            setattr(session, field, stored)

        if not getattr(session, "challenger_id", ""):
            session.challenger_id = str(saved.get("challenger_id", ""))[:14]
            session.challenger_name = str(saved.get("challenger_name", ""))[:14]

    @property
    def boards(self):
        return self.VIEWS[self.view]

    def _has_entry(self, board_key):
        scores = getattr(self.game.session, "high_scores", {})
        if isinstance(scores, dict):
            board = scores.get(board_key)
            if isinstance(board, dict) and board:
                return True
        records = getattr(self.game.session, "records", {})
        return isinstance(records, dict) and board_key in records

    def _last_recorded_index(self):
        for index in range(len(self.boards) - 1, -1, -1):
            if self._has_entry(self.boards[index]["key"]):
                return index
        return 0

    def _show_view(self, view):
        if view == self.view:
            return
        self.view = view
        self.index = self._last_recorded_index()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_SPACE):
                self.game.state_manager.pop()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.index = (self.index - 1) % len(self.boards)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % len(self.boards)
            elif event.key == pygame.K_c:
                self._show_view("chapters")
            elif event.key == pygame.K_m:
                self._show_view("missions")
            elif event.key == pygame.K_v:
                self._show_view("missions" if self.view == "chapters" else "chapters")
            elif event.key == pygame.K_TAB:
                self.source = "database" if self.source == "local" else "local"

    def draw(self, surface):
        theme.draw_background(surface)
        theme.draw_text(surface, "CHALLENGE SCORES", (160, 13), "heading",
                        theme.HONEY, anchor="midtop")
        source_label = "LOCAL DEVICE" if self.source == "local" else "DATABASE (ONLINE)"
        theme.draw_text(surface, f"BEST RESULT PER PLAYER ID · STORED ON {source_label} · TAB TO SWITCH",
                        (160, 39), "tiny", theme.CREAM_DIM, anchor="center")

        board = self.boards[self.index]
        panel = pygame.Rect(14, 51, 292, 105)
        panel_title = "CHAPTER TOTALS" if self.view == "chapters" else "MISSION RESULTS"
        theme.draw_panel(surface, panel, title=panel_title, alpha=248)
        switch_hint = "V: MISSIONS" if self.view == "chapters" else "V: CHAPTERS"
        theme.draw_text(surface, switch_hint, (panel.right - 6, panel.y + 3),
                        "tiny", theme.CREAM_DIM, shadow=False, anchor="topright")

        board_title = board["title"].upper()
        name_lines = wrap_text(board_title, theme.get_font("tiny"), 252)[:2]
        for index, line in enumerate(name_lines):
            theme.draw_text(surface, line, (160, 66 + index * 9), "tiny", theme.SKY, anchor="center")

        info_y = 66 + len(name_lines) * 9
        theme.draw_text(surface, board["chapter_label"], (160, info_y),
                        "tiny", theme.CREAM_DIM, anchor="center")
        count_label = "CHAPTER" if self.view == "chapters" else "MISSION"
        theme.draw_text(surface, f"{count_label} {self.index + 1}/{len(self.boards)}",
                        (160, info_y + 9), "tiny", theme.CREAM_DIM, anchor="center")

        stage_id = board["key"]
        if self.source == "database" and db_manager.is_connected:
            entries = db_manager.get_high_scores(stage_id, limit=10)
            shown = [{"score": e["score"], "attempts": 1, "best_time": e.get("time", 0),
                      "player_id": e["username"]}
                     for e in entries]
        else:
            shown = list(self.game.session.stage_high_scores(stage_id))

        if not shown:
            if self.view == "chapters":
                message = f"No completed chapters yet ({source_label.lower()})."
            else:
                message = f"No completed runs for this mission yet ({source_label.lower()})."
            theme.draw_text(surface, message, (160, max(116, info_y + 24)),
                            "small", theme.CREAM, anchor="center")
        else:
            for rank, entry in enumerate(shown[:3]):
                y = max(101, info_y + 20) + rank * 18
                rank_color = theme.HONEY if rank == 0 else theme.CREAM_DIM
                theme.draw_text(surface, f"{rank + 1}.", (42, y), "tiny", rank_color)
                player_id = entry.get("player_id", entry.get("character_id", "PLAYER"))
                theme.draw_text(surface, str(player_id).upper()[:14], (68, y), "tiny", theme.CREAM)
                theme.draw_text(surface, f"{entry.get('score', 0):,} PTS", (280, y), "tiny",
                                theme.SAGE, anchor="topright")

                detail = (f"ATTEMPTS {entry.get('attempts', 1)}   "
                          f"BEST {int(entry.get('best_time') or 0)}s")
                if self.view == "chapters":
                    if entry.get("missions_done") is not None:
                        detail += (f"   MISSIONS {entry.get('missions_done', 0)}"
                                   f"/{entry.get('missions_total', 0)}")
                elif "quests_total" in entry:
                    detail += f"   OBJ {entry.get('quests_done', 0)}/{entry.get('quests_total', 0)}"
                theme.draw_text(surface, detail, (68, y + 9), "tiny", theme.CREAM_DIM)

        theme.draw_text(surface, "LEFT/RIGHT BOARD · V VIEW · TAB SOURCE · ENTER BACK",
                        (160, 160), "tiny", theme.CREAM_DIM, anchor="center")
