"""Board dominance checks for the in-game HUD.

Theme text is flushed on top of the scaled canvas, so any world text
(NPC names, item names, house names, zone labels, prompts) queued before
a UI board would otherwise render *over* that board. These tests drive a
real story level and assert that:

  * the quest board (objective) stays compact, and
  * no queued text that belongs to the world ever covers a board.
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import unittest

from src.core import settings
from src.core.decision_system import Decision
from src.core.session import GameSession
from src.story.prologue.level_3_severe_flooding import (
    PrologueLevel3SevereFlooding,
)
from src.ui import theme

W, H = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT


class BoardDominanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((W * 4, H * 4))
        theme._font_cache.clear()
        cls.surface = pygame.Surface((W, H))

        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        session.character = json.loads(
            (root / "data" / "characters.json").read_text(encoding="utf-8")
        )[0]
        session.save = lambda: None
        cls.game = SimpleNamespace(
            session=session,
            state_manager=SimpleNamespace(
                pop=lambda: None, change=lambda _state: None,
                push=lambda _state: None, stack=[],
            ),
            ask_quit=lambda: None,
            to_canvas_pos=lambda pos: pos,
        )

    @classmethod
    def tearDownClass(cls):
        # Leave pygame initialised: other test modules imported during
        # discovery rely on the shared font cache, and quitting here would
        # invalidate fonts they still hold.
        theme._font_cache.clear()

    def make_level(self):
        level = PrologueLevel3SevereFlooding(self.game)
        level.camera.offset.update(0, 0)     # deterministic screen coords
        return level

    @staticmethod
    def quiet_hud(level):
        """Turn off hint/countdown so board-vs-board overlap can't confuse checks."""
        level.hint_timer = 0.0
        level.hint_text = ""
        level.stop_countdown()
        return level

    def queued(self):
        out = []
        for font, text, _color, (x, y), _shadow in theme.TEXT_QUEUE:
            tw, th = font.size(text)
            out.append((pygame.Rect(x, y, tw, th), text))
        return out

    def draw_level(self, level):
        theme.TEXT_QUEUE.clear()
        level.draw(self.surface)

    def board_rects(self, level):
        """The small boards only (a full-screen board is checked separately)."""
        rects = [pygame.Rect(0, 0, W, level.HUD_BAR_H),
                 level._objective_box(W)[0]]
        hint = level._hint_box(W, H)
        if hint is not None:
            rects.append(hint[0])
        cd_rect = level._countdown_rect(W)
        if cd_rect is not None:
            rects.append(cd_rect)
        if (level.active_dialogue is not None
                and level.dialogue_idx < len(level.active_dialogue)):
            rects.append(level._dialogue_box_layout(W, H)[0])
        if level.decision_system.is_active():
            rects.append(level._decision_box_layout(W, H)[0])
        return rects

    def full_screen_board_active(self, level):
        return (level.show_lesson_modal or level.legend_screen.visible
                or level.pause_menu.visible)

    def assert_no_world_text_over_boards(self, level):
        # A full-screen board covers the small boards, so only canvas
        # containment matters there.
        if self.full_screen_board_active(level):
            for rect, text in self.queued():
                if text.strip():
                    self.assertTrue(
                        pygame.Rect(0, 0, W, H).contains(rect),
                        f"text {text!r} {rect} left the canvas",
                    )
            return

        boards = self.board_rects(level)
        for rect, text in self.queued():
            if not text.strip():
                continue
            for board in boards:
                if rect.colliderect(board):
                    self.assertTrue(
                        board.contains(rect),
                        f"world text {text!r} {rect} is drawn over board {board}",
                    )

    def test_quest_board_is_compact(self):
        level = self.make_level()
        rect, _lines, _lh = level._objective_box(W)
        self.assertLessEqual(rect.w, level.OBJ_MAX_W)
        self.assertLessEqual(rect.right, W)

    def test_world_label_under_quest_board_is_dropped(self):
        level = self.make_level()
        theme.TEXT_QUEUE.clear()
        obj_rect, _lines, _lh = level._objective_box(W)
        label_pos = (obj_rect.x + 4, obj_rect.y + 4)
        theme.draw_text(self.surface, "FLOODED HOUSE", label_pos,
                        size="tiny", shadow=False, anchor="topleft")
        level.draw(self.surface)
        self.assertNotIn("FLOODED HOUSE", [t for _r, t in self.queued()])
        self.assert_no_world_text_over_boards(level)

    def test_world_label_under_dialogue_box_is_dropped(self):
        level = self.make_level()
        level.start_dialogue("KAP. BEN", ["Move to higher ground immediately."])
        rect, _lines, _lh, _pad = level._dialogue_box_layout(W, H)
        theme.TEXT_QUEUE.clear()
        theme.draw_text(self.surface, "DR. REYES", (rect.x + 6, rect.y + 4),
                        size="tiny", shadow=False, anchor="topleft")
        level.draw(self.surface)
        self.assertNotIn("DR. REYES", [t for _r, t in self.queued()])
        self.assert_no_world_text_over_boards(level)

    def test_world_label_under_lesson_modal_is_dropped(self):
        level = self.make_level()
        level.show_lesson_modal = True
        theme.TEXT_QUEUE.clear()
        theme.draw_text(self.surface, "FARM HOUSE", (8, 90),
                        size="tiny", shadow=False, anchor="topleft")
        level.draw(self.surface)
        self.assertNotIn("FARM HOUSE", [t for _r, t in self.queued()])
        self.assert_no_world_text_over_boards(level)

    def test_world_label_under_decision_box_is_dropped(self):
        level = self.quiet_hud(self.make_level())
        level.decision_system.trigger_decision(Decision(
            decision_id="test",
            prompt="The water is rising quickly. What is the safest thing to do?",
            options=[{"text": "Move to higher ground now", "safe": True},
                     {"text": "Wade through the flood", "safe": False}],
        ))
        rect, _p, _o, _lh, _pad, _fh = level._decision_box_layout(W, H)
        theme.TEXT_QUEUE.clear()
        theme.draw_text(self.surface, "SARI", (rect.x + 6, rect.y + 4),
                        size="tiny", shadow=False, anchor="topleft")
        level.draw(self.surface)
        self.assertNotIn("SARI", [t for _r, t in self.queued()])
        self.assert_no_world_text_over_boards(level)

    def test_npc_name_is_kept_when_no_board_covers_it(self):
        level = self.quiet_hud(self.make_level())
        # Captain Reyes sits off-camera at the spawn point; pan to him.
        level.camera.offset.update(300, 16)
        self.draw_level(level)
        self.assertIn("Captain Reyes", [t for _r, t in self.queued()])

    def test_every_board_state_keeps_world_text_off_boards(self):
        # Small-board states: no queued text may cover a board.
        for level in (self.quiet_hud(self.make_level()),
                      self.quiet_hud(self.make_level())):
            with self.subTest(small_board=level):
                self.draw_level(level)
                self.assert_no_world_text_over_boards(level)

        dialogue = self.quiet_hud(self.make_level())
        dialogue.start_dialogue("KAP. BEN", ["Move to higher ground immediately."])
        self.draw_level(dialogue)
        self.assert_no_world_text_over_boards(dialogue)

        quiet_decision = self.quiet_hud(self.make_level())
        quiet_decision.decision_system.trigger_decision(Decision(
            decision_id="test",
            prompt="Pick the safest action.",
            options=[{"text": "Move up", "safe": True},
                     {"text": "Stay", "safe": False}],
        ))
        self.draw_level(quiet_decision)
        self.assert_no_world_text_over_boards(quiet_decision)

        # Full-screen board states: a marker world label must be gone.
        full_screen_states = []
        lesson = self.make_level()
        lesson.show_lesson_modal = True
        full_screen_states.append(lesson)
        paused = self.make_level()
        paused.pause_menu.show()
        full_screen_states.append(paused)
        legend = self.make_level()
        legend.legend_screen.show()
        full_screen_states.append(legend)

        for level in full_screen_states:
            with self.subTest(full_screen_board=level):
                theme.TEXT_QUEUE.clear()
                theme.draw_text(self.surface, "MARKER LABEL", (8, 90),
                                size="tiny", shadow=False, anchor="topleft")
                level.draw(self.surface)
                self.assertNotIn("MARKER LABEL", [t for _r, t in self.queued()])
                for rect, text in self.queued():
                    self.assertTrue(
                        pygame.Rect(0, 0, W, H).contains(rect),
                        f"text {text!r} {rect} left the canvas",
                    )


if __name__ == "__main__":
    unittest.main()
